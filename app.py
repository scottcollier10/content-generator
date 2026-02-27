# app.py — Flask application entry point
# Receives Slack slash commands, spawns background threads for processing,
# and orchestrates brand context → AI generation → HubSpot draft creation.

import os
import time
import threading
from datetime import datetime

import yaml
import requests
from flask import Flask, request, jsonify
from dotenv import load_dotenv

from models import SlackCommand, BrandContext, GenerationResult
from services import GoogleDriveBrandContext, ContentGenerator, HubSpotClient
from utils import GenerationLogger, get_app_logger

# Load environment variables from .env
load_dotenv()

# Load client-specific config
with open("config.yaml") as f:
    config = yaml.safe_load(f)

app = Flask(__name__)
logger = get_app_logger("app")
generation_logger = GenerationLogger(config["logging"]["output_dir"])


def process_campaign(command: SlackCommand) -> None:
    """Process campaign generation in a background thread.

    This runs after the immediate 200 OK is returned to Slack.
    Posts progress updates and final results back to command.response_url.
    """
    start_time = time.time()
    errors = []

    try:
        # Notify Slack that processing has started
        requests.post(
            command.response_url,
            json={
                "response_type": "in_channel",
                "text": (
                    f"⏳ Generating 3 email variations for \"{command.topic}\"...\n"
                    f"Target audience: {command.audience}\n"
                    f"Goal: {command.goal}\n\n"
                    "This usually takes 10-15 seconds."
                ),
            },
        )

        # 1. Fetch brand context from Google Drive
        logger.info("Fetching brand context...")
        try:
            brand_provider = GoogleDriveBrandContext(
                folder_id=config["google_drive"]["brand_folder_id"]
            )
            brand_context = brand_provider.get_brand_context()
            logger.info(f"Loaded brand context from {len(brand_context.files_processed)} files")
        except Exception as e:
            # Graceful degradation — continue without brand context
            logger.warning(f"Failed to load brand context: {e}")
            brand_context = BrandContext()
            errors.append(f"Brand context: {str(e)}")

        # 2. Generate email variations via Claude
        logger.info("Generating content variations...")
        generator = ContentGenerator()
        variations = generator.generate_variations(
            topic=command.topic,
            audience=command.audience,
            goal=command.goal,
            brand_context=brand_context,
        )
        logger.info(f"Generated {len(variations)} variations")

        # 3. Clone template and create HubSpot drafts
        logger.info("Creating HubSpot drafts...")
        hubspot = HubSpotClient(portal_id=config["hubspot"]["portal_id"])

        # Use provided template_id or fall back to config default
        effective_template_id = command.template_id or config["hubspot"]["default_template_id"]
        if command.template_id:
            logger.info(f"Using provided template_id: {effective_template_id}")
        else:
            logger.info(f"Using default template_id from config: {effective_template_id}")

        drafts = hubspot.create_email_drafts(
            template_id=effective_template_id,
            topic=command.topic,
            variations=variations,
        )

        duration = time.time() - start_time

        # 4. Log generation to JSON file
        generation_logger.log_generation(
            topic=command.topic,
            data={
                "timestamp": datetime.utcnow().isoformat(),
                "slack_user": command.user_name,
                "request": {
                    "topic": command.topic,
                    "audience": command.audience,
                    "goal": command.goal,
                    "template_id": command.template_id,
                },
                "brand_context_files": brand_context.files_processed,
                "variations": [
                    {
                        "approach": v.approach,
                        "subject": v.subject,
                        "preview": v.preview,
                        "cta_text": v.cta_text,
                    }
                    for v in variations
                ],
                "hubspot_drafts": [
                    {
                        "approach": d.approach,
                        "id": d.email_id,
                        "url": d.draft_url,
                    }
                    for d in drafts
                ],
                "duration_seconds": round(duration, 2),
                "errors": errors,
            },
        )

        # 5. Post rich Slack response with HubSpot links
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "✅ 3 Email Variations Ready!",
                    "emoji": True,
                },
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": (
                        f"*Campaign:* {command.topic}\n"
                        f"*Audience:* {command.audience}\n"
                        f"*Goal:* {command.goal}"
                    ),
                },
            },
            {"type": "divider"},
        ]

        for i, draft in enumerate(drafts, 1):
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*{i}. {draft.approach.upper()}*\n_{draft.subject}_",
                },
                "accessory": {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "Edit in HubSpot",
                        "emoji": True,
                    },
                    "url": draft.draft_url,
                    "action_id": f"link_{i}",
                },
            })

        requests.post(
            command.response_url,
            json={
                "response_type": "in_channel",
                "blocks": blocks,
            },
        )

    except Exception as e:
        logger.error(f"Campaign generation failed: {e}", exc_info=True)
        requests.post(
            command.response_url,
            json={
                "response_type": "in_channel",
                "text": f"❌ Generation failed: {str(e)}",
            },
        )


@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint — used by Docker and monitoring."""
    return jsonify({"status": "ok"})


@app.route("/slack-interactive", methods=["POST"])
def slack_interactive():
    """Handle Slack interactive components (button acknowledgements).

    Required to suppress Slack's 'endpoint not configured' warning.
    """
    return "", 200


@app.route("/slack-campaign", methods=["POST"])
def slack_campaign():
    """Handle Slack slash command for campaign generation.

    Expected format: /campaign <topic> <audience> <goal> [template_id]

    Examples:
        /campaign webinar CFOs engagement
        /campaign product-launch enterprise awareness 315102898877
    """
    command = SlackCommand.from_slack_body(request.form.to_dict())
    template_info = f"template={command.template_id}" if command.template_id else "template=default"
    logger.info(
        f"Received command from {command.user_name}: "
        f"topic={command.topic}, audience={command.audience}, goal={command.goal}, {template_info}"
    )

    # Spawn background thread — Slack requires a response within 3 seconds
    thread = threading.Thread(target=process_campaign, args=(command,))
    thread.start()

    return "", 200


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)

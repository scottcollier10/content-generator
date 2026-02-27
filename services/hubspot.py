# services/hubspot.py
# Handles HubSpot Marketing Email API operations:
# clone template → read structure → patch with AI content → return draft URL.

import os
from typing import Optional
from datetime import date

import requests

from models import HubSpotDraft
from utils import get_app_logger

logger = get_app_logger(__name__)


def build_patch_payload(
    subject: str,
    body_html: str,
    cta_text: str,
    approach: str,
    topic: str,
    widgets: dict,
) -> dict:
    """Build the PATCH payload for updating a cloned email's content.

    Wraps the AI-generated body HTML with a CTA button, then injects
    it into the correct widget. Works with both classic and DnD templates.
    """
    # Append a styled CTA button below the body content
    branded_html = f"""
{body_html}

<p style="margin: 32px 0 0 0;">
  <a href="#" style="display: inline-block; padding: 14px 32px; background-color: #2F6FED; color: #ffffff; text-decoration: none; font-size: 16px; font-weight: 500; border-radius: 6px;">{cta_text}</a>
</p>
"""

    # Discover the correct widget ID — varies by template type
    target_widget_id = None

    if "hs_email_body" in widgets:
        # Classic template structure
        target_widget_id = "hs_email_body"
    else:
        # Drag-and-drop template — find the first non-footer rich_text widget
        for widget_id, widget in widgets.items():
            body = widget.get("body", {})
            if body.get("path") in ["@hubspot/rich_text", "@hubspot/raw_html_email"]:
                html = body.get("html", "").lower()
                if "unsubscribe" not in html and "footer" not in html:
                    target_widget_id = widget_id
                    break

    if not target_widget_id:
        raise ValueError(
            f"Could not find an editable widget in this template. "
            f"Available widget IDs: {list(widgets.keys())}"
        )

    # Merge updated widget into existing widget map
    updated_widgets = dict(widgets)
    updated_widgets[target_widget_id] = {
        **widgets[target_widget_id],
        "body": {
            **widgets[target_widget_id].get("body", {}),
            "html": branded_html,
        },
    }

    return {
        "name": f"{approach} - {topic}",
        "subject": subject,
        "content": {
            "widgets": updated_widgets,
        },
    }


class HubSpotClient:
    """Client for the HubSpot Marketing Email API."""

    BASE_URL = "https://api.hubapi.com/marketing/v3/emails"

    def __init__(self, api_key: Optional[str] = None, portal_id: Optional[str] = None):
        self.api_key = api_key or os.getenv("HUBSPOT_API_KEY")
        self.portal_id = portal_id
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def get_email_content(self, email_id: str) -> dict:
        """Fetch full email data including widget/content structure."""
        response = requests.get(
            f"{self.BASE_URL}/{email_id}",
            headers=self.headers,
        )
        response.raise_for_status()
        return response.json()

    def clone_template(self, template_id: str, name: str) -> str:
        """Clone an email template and return the new email's ID.

        HubSpot doesn't have a /clone endpoint, so we:
        1. GET the source template to retrieve its structure
        2. POST a new email using that structure

        This preserves the layout, styling, footer, and unsubscribe links.
        """
        logger.info(f"Fetching template {template_id}...")
        template = self.get_email_content(template_id)

        create_payload = {
            "name": name,
            "subject": template.get("subject", ""),
            "language": template.get("language", "en"),
            "subcategory": template.get("subcategory", "marketing_email"),
            "state": "DRAFT",
        }

        # Preserve content structure (widgets, modules)
        if "content" in template:
            create_payload["content"] = template["content"]

        # Preserve business unit if present
        if template.get("businessUnitId"):
            create_payload["businessUnitId"] = template["businessUnitId"]

        # Preserve template path reference
        if template.get("primaryEmailTemplateId"):
            create_payload["primaryEmailTemplateId"] = template["primaryEmailTemplateId"]
        elif template.get("templatePath"):
            create_payload["templatePath"] = template["templatePath"]

        logger.info("Creating new email from template...")
        response = requests.post(
            self.BASE_URL,
            headers=self.headers,
            json=create_payload,
        )
        if not response.ok:
            logger.error(f"HubSpot API error: {response.status_code} - {response.text}")
        response.raise_for_status()

        new_email = response.json()
        logger.info(f"Created email with ID: {new_email['id']}")
        return new_email["id"]

    def patch_email(
        self,
        email_id: str,
        subject: str,
        body_html: str,
        cta_text: str,
        approach: str,
        topic: str,
    ) -> HubSpotDraft:
        """Patch a cloned email with generated content. Returns the draft."""
        # Re-fetch current content to get widget structure before patching
        current = self.get_email_content(email_id)
        widgets = current.get("content", {}).get("widgets", {})

        payload = build_patch_payload(
            subject=subject,
            body_html=body_html,
            cta_text=cta_text,
            approach=approach,
            topic=topic,
            widgets=widgets,
        )

        response = requests.patch(
            f"{self.BASE_URL}/{email_id}",
            headers=self.headers,
            json=payload,
        )
        response.raise_for_status()

        result = response.json()
        draft_url = f"https://app.hubspot.com/email/{self.portal_id}/edit/{result['id']}"

        return HubSpotDraft(
            email_id=result["id"],
            draft_url=draft_url,
            approach=approach,
            subject=subject,
        )

    def create_email_drafts(
        self,
        template_id: str,
        topic: str,
        variations: list,
    ) -> list[HubSpotDraft]:
        """Create a draft for each variation. Returns list of HubSpotDraft objects."""
        drafts = []

        for variation in variations:
            try:
                clone_name = f"{variation.approach} - {topic} - {date.today().isoformat()}"
                clone_id = self.clone_template(template_id, clone_name)
                logger.info(f"Cloned template to {clone_id}")

                draft = self.patch_email(
                    email_id=clone_id,
                    subject=variation.subject,
                    body_html=variation.body_html,
                    cta_text=variation.cta_text,
                    approach=variation.approach,
                    topic=topic,
                )
                drafts.append(draft)
                logger.info(f"Created draft: {draft.draft_url}")

            except Exception as e:
                logger.error(f"Failed to create draft for {variation.approach}: {e}")

        return drafts

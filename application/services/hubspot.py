# application/services/hubspot.py
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
    """Build the PATCH payload for updating email content."""
    # Wrap content with CTA button
    branded_html = f"""
{body_html}

<p style="margin: 32px 0 0 0;">
  <a href="#" style="display: inline-block; padding: 14px 32px; background-color: #2F6FED; color: #ffffff; text-decoration: none; font-size: 16px; font-weight: 500; border-radius: 6px;">{cta_text}</a>
</p>
"""

    # Find the target widget (hs_email_body for classic, or first rich_text for DnD)
    target_widget_id = None

    if "hs_email_body" in widgets:
        target_widget_id = "hs_email_body"
    else:
        # Look for rich_text widget in DnD templates
        for widget_id, widget in widgets.items():
            body = widget.get("body", {})
            if body.get("path") in ["@hubspot/rich_text", "@hubspot/raw_html_email"]:
                html = body.get("html", "").lower()
                # Skip footer widgets
                if "unsubscribe" not in html and "footer" not in html:
                    target_widget_id = widget_id
                    break

    if not target_widget_id:
        raise ValueError(f"Could not find editable widget. Available: {list(widgets.keys())}")

    # Update the widget
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
    """Client for HubSpot Marketing Email API."""

    BASE_URL = "https://api.hubapi.com/marketing/v3/emails"

    def __init__(self, api_key: Optional[str] = None, portal_id: Optional[str] = None):
        self.api_key = api_key or os.getenv("HUBSPOT_API_KEY")
        self.portal_id = portal_id
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def clone_template(self, template_id: str, name: str) -> str:
        """Clone an email template. Returns the new email ID."""
        response = requests.post(
            f"{self.BASE_URL}/clone",
            headers=self.headers,
            json={
                "id": template_id,
                "cloneName": name,
                "language": "en",
            },
        )
        response.raise_for_status()
        return response.json()["id"]

    def get_email_content(self, email_id: str) -> dict:
        """Get email content including widget structure."""
        response = requests.get(
            f"{self.BASE_URL}/{email_id}",
            headers=self.headers,
        )
        response.raise_for_status()
        return response.json()

    def patch_email(
        self,
        email_id: str,
        subject: str,
        body_html: str,
        cta_text: str,
        approach: str,
        topic: str,
    ) -> HubSpotDraft:
        """Update email with new content. Returns draft info."""
        # Get current content to preserve widget structure
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
        """Create email drafts for each variation."""
        drafts = []

        for variation in variations:
            try:
                # Clone template
                clone_name = f"{variation.approach} - {topic} - {date.today().isoformat()}"
                clone_id = self.clone_template(template_id, clone_name)
                logger.info(f"Cloned template to {clone_id}")

                # Patch with content
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

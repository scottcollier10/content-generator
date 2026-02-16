# application/tests/test_hubspot.py
from services.hubspot import HubSpotClient, build_patch_payload


def test_build_patch_payload_includes_subject():
    """Patch payload should include email subject."""
    payload = build_patch_payload(
        subject="Test Subject",
        body_html="<p>Hello</p>",
        cta_text="Click Here",
        approach="benefit-focused",
        topic="summer sale",
        widgets={"hs_email_body": {"body": {"html": ""}}},
    )
    assert payload["subject"] == "Test Subject"


def test_build_patch_payload_wraps_html_with_cta():
    """Patch payload should include CTA button in HTML."""
    payload = build_patch_payload(
        subject="Test",
        body_html="<p>Content</p>",
        cta_text="Learn More",
        approach="story-driven",
        topic="test",
        widgets={"hs_email_body": {"body": {"html": ""}}},
    )
    # CTA should be in the widget HTML
    widget_html = payload["content"]["widgets"]["hs_email_body"]["body"]["html"]
    assert "Learn More" in widget_html
    assert "<p>Content</p>" in widget_html

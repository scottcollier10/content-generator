# tests/test_hubspot.py
# Unit tests for HubSpot payload construction.

from services.hubspot import build_patch_payload


CLASSIC_WIDGETS = {"hs_email_body": {"body": {"html": ""}}}


def test_build_patch_payload_includes_subject():
    """Patch payload should carry the email subject."""
    payload = build_patch_payload(
        subject="Test Subject",
        body_html="<p>Hello</p>",
        cta_text="Click Here",
        approach="benefit-focused",
        topic="summer sale",
        widgets=CLASSIC_WIDGETS,
    )
    assert payload["subject"] == "Test Subject"


def test_build_patch_payload_wraps_html_with_cta():
    """Patch payload should embed CTA button text inside the widget HTML."""
    payload = build_patch_payload(
        subject="Test",
        body_html="<p>Content</p>",
        cta_text="Learn More",
        approach="story-driven",
        topic="test",
        widgets=CLASSIC_WIDGETS,
    )
    widget_html = payload["content"]["widgets"]["hs_email_body"]["body"]["html"]
    assert "Learn More" in widget_html
    assert "<p>Content</p>" in widget_html


def test_build_patch_payload_email_name_includes_approach_and_topic():
    """Email name should follow the approach - topic convention."""
    payload = build_patch_payload(
        subject="Test",
        body_html="<p>Body</p>",
        cta_text="Go",
        approach="urgency-based",
        topic="product-launch",
        widgets=CLASSIC_WIDGETS,
    )
    assert "urgency-based" in payload["name"]
    assert "product-launch" in payload["name"]


def test_build_patch_payload_raises_on_no_widget():
    """Should raise ValueError if no editable widget is found."""
    import pytest
    with pytest.raises(ValueError, match="Could not find"):
        build_patch_payload(
            subject="Test",
            body_html="<p>Body</p>",
            cta_text="Go",
            approach="benefit-focused",
            topic="test",
            widgets={},  # Empty — no valid widget
        )

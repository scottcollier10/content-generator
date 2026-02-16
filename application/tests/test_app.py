# application/tests/test_app.py
import json
from app import app


def test_health_endpoint():
    """Health endpoint should return 200."""
    client = app.test_client()
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json["status"] == "ok"


def test_slack_webhook_returns_200():
    """Slack webhook should return 200 immediately."""
    client = app.test_client()
    response = client.post(
        "/slack-campaign",
        data={
            "text": "summer-sale customers conversions",
            "response_url": "https://hooks.slack.com/test",
            "user_id": "U123",
            "user_name": "test.user",
            "channel_id": "C123",
        },
        content_type="application/x-www-form-urlencoded",
    )
    # Should return 200 immediately (async processing)
    assert response.status_code == 200

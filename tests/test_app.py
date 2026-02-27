# tests/test_app.py
# Integration tests for Flask routes.

from app import app


def test_health_endpoint():
    """Health endpoint should return 200 with status ok."""
    client = app.test_client()
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json["status"] == "ok"


def test_slack_webhook_returns_200_immediately():
    """Slack webhook must return 200 immediately (Slack requires < 3s)."""
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
    assert response.status_code == 200


def test_slack_interactive_returns_200():
    """Interactive endpoint should acknowledge button clicks silently."""
    client = app.test_client()
    response = client.post("/slack-interactive")
    assert response.status_code == 200

"""
Integration tests for the HubSpot Content Generator.

These tests require external services and should be run manually
with proper credentials configured.

Manual Testing Flow:
1. Start the app: docker-compose up --build
2. Expose via ngrok: ngrok http 5000
3. Configure Slack slash command to ngrok URL
4. Test from Slack: /campaign topic="Test" audience="Developers" goal="Awareness"
5. Verify HubSpot drafts are created
"""

import pytest


class TestIntegrationPlaceholder:
    """Placeholder for future integration tests."""

    def test_placeholder(self):
        """Placeholder test - integration tests require external services."""
        # Future: Test full flow with mocked external services
        # - Mock Google Drive API responses
        # - Mock Claude API responses
        # - Mock HubSpot API responses
        # - Verify end-to-end flow
        assert True

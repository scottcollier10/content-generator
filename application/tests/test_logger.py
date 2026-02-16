import os
import json
import tempfile
from datetime import datetime
from utils.logger import GenerationLogger


def test_log_generation_creates_file():
    """Logger should create a JSON file with generation data."""
    with tempfile.TemporaryDirectory() as tmpdir:
        logger = GenerationLogger(output_dir=tmpdir)

        data = {
            "timestamp": datetime.utcnow().isoformat(),
            "slack_user": "test.user",
            "request": {"topic": "summer sale"},
            "variations": [],
            "hubspot_drafts": [],
            "duration_seconds": 1.5,
        }

        filepath = logger.log_generation(
            topic="summer sale",
            data=data,
        )

        assert os.path.exists(filepath)
        with open(filepath) as f:
            saved = json.load(f)
        assert saved["slack_user"] == "test.user"

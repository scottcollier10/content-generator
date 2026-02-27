# utils/logger.py
# Application logging utilities.
# get_app_logger — returns a configured Python logger.
# GenerationLogger — persists each generation run as a JSON file for auditing.

import os
import json
import logging
from datetime import datetime
from typing import Any


def get_app_logger(name: str = "app") -> logging.Logger:
    """Return a configured logger with a consistent format.

    Idempotent — calling this multiple times with the same name
    returns the same logger without adding duplicate handlers.
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(
            logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        )
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger


class GenerationLogger:
    """Persists each generation run as a timestamped JSON file.

    Useful for auditing, debugging, and reviewing past generations.
    Files are written to output_dir and gitignored by default.
    """

    def __init__(self, output_dir: str = "logs/"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def log_generation(self, topic: str, data: dict[str, Any]) -> str:
        """Write generation data to a JSON file. Returns the file path."""
        timestamp = datetime.utcnow().strftime("%Y-%m-%d_%H-%M-%S")
        # Sanitize topic for use in filename
        safe_topic = "".join(c if c.isalnum() or c in "-_" else "-" for c in topic)
        filename = f"{timestamp}_{safe_topic}.json"
        filepath = os.path.join(self.output_dir, filename)

        with open(filepath, "w") as f:
            json.dump(data, f, indent=2, default=str)

        return filepath

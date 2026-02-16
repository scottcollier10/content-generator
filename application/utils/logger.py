import os
import json
import logging
from datetime import datetime
from typing import Any


def get_app_logger(name: str = "app") -> logging.Logger:
    """Get configured application logger."""
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
    """Logs generation requests and results to JSON files."""

    def __init__(self, output_dir: str = "logs/generations"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def log_generation(self, topic: str, data: dict[str, Any]) -> str:
        """
        Log a generation to a JSON file.

        Returns the filepath of the created log.
        """
        timestamp = datetime.utcnow().strftime("%Y-%m-%d_%H-%M-%S")
        safe_topic = "".join(c if c.isalnum() or c in "-_" else "-" for c in topic)
        filename = f"{timestamp}_{safe_topic}.json"
        filepath = os.path.join(self.output_dir, filename)

        with open(filepath, "w") as f:
            json.dump(data, f, indent=2, default=str)

        return filepath

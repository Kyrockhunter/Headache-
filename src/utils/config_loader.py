"""
config_loader.py
------------------------------------
Centralizes YAML configuration and logging setup for Fantasy V4.
"""

import yaml
import logging
import logging.config
from pathlib import Path

CONFIG_DIR = Path(__file__).resolve().parents[2] / "config"

def load_settings():
    """Load general settings.yaml"""
    with open(CONFIG_DIR / "settings.yaml", "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def setup_logging():
    """Configure logging from logging.yaml"""
    with open(CONFIG_DIR / "logging.yaml", "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    logging.config.dictConfig(config)
    logging.info("Logging configured successfully.")

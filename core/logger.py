"""
Centralized logging system for workspace-tools.
Writes to both console and rotating log file.
"""

import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from datetime import datetime

# Log directory in user's home
LOG_DIR = Path.home() / ".workspace-tools" / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

LOG_FILE = LOG_DIR / "pdf-tool.log"


def get_logger(name: str = "pdf-tool") -> logging.Logger:
    """
    Returns a configured logger instance.

    Args:
        name: Logger name (typically the module name).

    Returns:
        Configured Logger instance.
    """
    logger = logging.getLogger(name)

    # Avoid adding duplicate handlers on repeated calls
    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG)

    # --- Console handler (INFO and above) ---
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_fmt = logging.Formatter(
        "%(levelname)s: %(message)s"
    )
    console_handler.setFormatter(console_fmt)

    # --- File handler (DEBUG and above, rotating) ---
    file_handler = RotatingFileHandler(
        LOG_FILE,
        maxBytes=5 * 1024 * 1024,  # 5 MB
        backupCount=3,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG)
    file_fmt = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    file_handler.setFormatter(file_fmt)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger


# Module-level default logger
log = get_logger("pdf-tool")

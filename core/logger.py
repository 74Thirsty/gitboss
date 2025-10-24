"""Logging configuration utilities for GitBoss."""
from __future__ import annotations

import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional

LOG_DIR = Path(os.path.expanduser("~/.gitboss/logs"))
LOG_FILE = LOG_DIR / "gitboss.log"
DEFAULT_LOG_LEVEL = logging.INFO


def _ensure_log_directory() -> None:
    """Create the log directory if it does not already exist."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)


def configure_logging(level: int = DEFAULT_LOG_LEVEL, handler: Optional[logging.Handler] = None) -> None:
    """Configure application-wide logging.

    Parameters
    ----------
    level:
        The logging level to configure for the root logger.
    handler:
        Optional custom handler. If omitted, a RotatingFileHandler pointing
        to :data:`LOG_FILE` is created.
    """
    _ensure_log_directory()

    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Remove existing handlers to avoid duplicate logs in environments where
    # configure_logging may be called multiple times (e.g., tests or reloads).
    for existing_handler in list(root_logger.handlers):
        root_logger.removeHandler(existing_handler)

    if handler is None:
        handler = RotatingFileHandler(LOG_FILE, maxBytes=2 * 1024 * 1024, backupCount=3)

    formatter = logging.Formatter(
        fmt="[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)

    root_logger.addHandler(handler)


__all__ = ["configure_logging", "LOG_FILE"]

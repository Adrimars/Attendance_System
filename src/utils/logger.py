"""
logger.py — Application-wide file logger with timestamps.

Writes all events to logs/attendance_YYYY-MM-DD.log
Events covered: app startup/shutdown, card taps, session start/end, errors, imports, exports.
"""

import logging
import os
from datetime import datetime
from pathlib import Path

# ── Resolve log directory relative to project root ──────────────────────────
_PROJECT_ROOT = Path(__file__).resolve().parents[2]  # src/utils/logger.py → root
_LOG_DIR = _PROJECT_ROOT / "logs"
_LOG_DIR.mkdir(exist_ok=True)

_log_filename = _LOG_DIR / f"attendance_{datetime.now().strftime('%Y-%m-%d')}.log"

# ── Configure module-level logger ────────────────────────────────────────────
_logger = logging.getLogger("attendance_system")
_logger.setLevel(logging.DEBUG)

if not _logger.handlers:
    _file_handler = logging.FileHandler(_log_filename, encoding="utf-8")
    _file_handler.setLevel(logging.DEBUG)
    _formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )
    _file_handler.setFormatter(_formatter)
    _logger.addHandler(_file_handler)


def log_info(message: str) -> None:
    """Log an informational message."""
    _logger.info(message)


def log_warning(message: str) -> None:
    """Log a warning message."""
    _logger.warning(message)


def log_error(message: str) -> None:
    """Log an error message (full trace should be appended by caller if available)."""
    _logger.error(message)


def log_debug(message: str) -> None:
    """Log a debug message."""
    _logger.debug(message)

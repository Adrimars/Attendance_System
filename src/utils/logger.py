"""
logger.py — Application-wide file logger with timestamps.

Writes all events to logs/attendance_YYYY-MM-DD.log
Events covered: app startup/shutdown, card taps, session start/end, errors, imports, exports.
"""

import logging
import logging.handlers
from datetime import datetime
from pathlib import Path

# ── Resolve log directory relative to project root ──────────────────────────
_PROJECT_ROOT = Path(__file__).resolve().parents[2]  # src/utils/logger.py → root
_LOG_DIR = _PROJECT_ROOT / "logs"
_LOG_DIR.mkdir(exist_ok=True)

_log_filename = _LOG_DIR / "attendance.log"

# ── Configure module-level logger ────────────────────────────────────────────
_logger = logging.getLogger("attendance_system")
_logger.setLevel(logging.DEBUG)

if not _logger.handlers:
    # TimedRotatingFileHandler rotates at midnight and names files by date.
    _file_handler = logging.handlers.TimedRotatingFileHandler(
        _log_filename,
        when="midnight",
        interval=1,
        backupCount=90,       # keep ~3 months of logs
        encoding="utf-8",
    )
    _file_handler.suffix = "%Y-%m-%d"
    _file_handler.setLevel(logging.DEBUG)
    _formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )
    _file_handler.setFormatter(_formatter)
    _logger.addHandler(_file_handler)


# ── Core log functions ────────────────────────────────────────────────────────

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


# ── Structured event helpers ──────────────────────────────────────────────────

def log_startup() -> None:
    """Log application startup."""
    _logger.info("=" * 60)
    _logger.info("APPLICATION STARTUP")
    _logger.info("=" * 60)


def log_shutdown() -> None:
    """Log application shutdown."""
    _logger.info("=" * 60)
    _logger.info("APPLICATION SHUTDOWN")
    _logger.info("=" * 60)


def log_card_tap(card_id: str, student_name: str, result: str, session_id: int) -> None:
    """
    Log an RFID card tap event.

    Args:
        card_id:      The raw card identifier.
        student_name: Full name of the matched student (or 'UNKNOWN').
        result:       'PRESENT', 'DUPLICATE', 'UNKNOWN', or 'ERROR'.
        session_id:   The active session id.
    """
    _logger.info(
        f"CARD_TAP | card='{card_id}' student='{student_name}' "
        f"result={result} session={session_id}"
    )


def log_session_start(session_id: int, section_name: str) -> None:
    """Log a session-start event."""
    _logger.info(
        f"SESSION_START | id={session_id} section='{section_name}'"
    )


def log_session_end(
    session_id: int,
    section_name: str,
    present: int,
    absent: int,
) -> None:
    """Log a session-end event with summary counts."""
    _logger.info(
        f"SESSION_END | id={session_id} section='{section_name}' "
        f"present={present} absent={absent}"
    )


def log_import_event(
    sheet_title: str,
    imported: int,
    skipped: int,
) -> None:
    """Log a completed Google Sheets import."""
    _logger.info(
        f"IMPORT | sheet='{sheet_title}' imported={imported} skipped={skipped}"
    )


def get_log_file_path() -> str:
    """Return the absolute path of the current log file."""
    return str(_log_filename)


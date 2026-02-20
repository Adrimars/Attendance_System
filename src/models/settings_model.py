"""
settings_model.py — Data-access layer for the settings (key-value) table.

Expected keys:
    absence_threshold         — integer as string, e.g. '3'
    admin_pin                 — hashed PIN string (empty = not yet set)
    language                  — 'en' or 'tr'
    google_credentials_path   — absolute file path to service-account JSON
"""

import sqlite3
from typing import Optional

from models.database import get_connection
from utils.logger import log_debug


def get_setting(key: str) -> Optional[str]:
    """
    Return the value for the given settings key, or None if not found.

    Args:
        key: The settings key to look up.
    """
    with get_connection() as conn:
        row = conn.execute(
            "SELECT value FROM settings WHERE key = ?;", (key,)
        ).fetchone()
    return row["value"] if row else None


def set_setting(key: str, value: str) -> None:
    """
    Insert or replace a key-value pair in the settings table.

    Args:
        key:   The settings key.
        value: The new value (always stored as TEXT).
    """
    with get_connection() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?);",
            (key, value),
        )
    log_debug(f"Setting updated: {key!r}")


def get_all_settings() -> dict[str, str]:
    """Return all settings as a plain Python dict."""
    with get_connection() as conn:
        rows = conn.execute("SELECT key, value FROM settings;").fetchall()
    return {row["key"]: row["value"] for row in rows}

"""
session_model.py — Data-access layer for the sessions table.
"""

import sqlite3
from datetime import datetime, timezone
from typing import Optional

from models.database import get_connection
from utils.logger import log_debug

SessionRow = sqlite3.Row


def create_session(section_id: int) -> int:
    """
    Open a new active session for the given section at the current UTC time.

    Args:
        section_id: FK reference to sections.id.

    Returns:
        The auto-incremented id of the new session.
    """
    now = datetime.now(timezone.utc)
    date_str = now.date().isoformat()          # YYYY-MM-DD
    start_time_str = now.isoformat()           # full ISO-8601 timestamp

    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO sessions (section_id, date, start_time, status)
            VALUES (?, ?, ?, 'active');
            """,
            (section_id, date_str, start_time_str),
        )
        new_id = cursor.lastrowid
    log_debug(f"Created session id={new_id} section_id={section_id} date={date_str}")
    return new_id  # type: ignore[return-value]


def get_session_by_id(session_id: int) -> Optional[SessionRow]:
    """Return a session row by primary key, or None if not found."""
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM sessions WHERE id = ?;", (session_id,)
        ).fetchone()
    return row


def get_active_session(section_id: int) -> Optional[SessionRow]:
    """
    Return the active (status='active') session for a section, or None.
    Only one active session per section is expected at any time.
    """
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT * FROM sessions
            WHERE section_id = ? AND status = 'active'
            ORDER BY start_time DESC
            LIMIT 1;
            """,
            (section_id,),
        ).fetchone()
    return row


def get_existing_session_for_date(section_id: int, date: str) -> Optional[SessionRow]:
    """
    Return the most recent session for section_id on the given ISO date string,
    regardless of status.  Used to detect duplicate session creation.
    """
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT * FROM sessions
            WHERE section_id = ? AND date = ?
            ORDER BY start_time DESC
            LIMIT 1;
            """,
            (section_id, date),
        ).fetchone()
    return row


def close_session(session_id: int) -> None:
    """
    Mark a session as closed and record its end_time.

    Args:
        session_id: The session to close.
    """
    end_time_str = datetime.now(timezone.utc).isoformat()
    with get_connection() as conn:
        conn.execute(
            """
            UPDATE sessions
            SET status = 'closed', end_time = ?
            WHERE id = ?;
            """,
            (end_time_str, session_id),
        )
    log_debug(f"Closed session id={session_id} end_time={end_time_str}")

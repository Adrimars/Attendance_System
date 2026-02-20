"""
attendance_model.py — Data-access layer for the attendance table.
"""

import sqlite3
from datetime import datetime, timezone
from typing import Optional

from models.database import get_connection
from utils.logger import log_debug

AttendanceRow = sqlite3.Row


def mark_present(
    session_id: int,
    student_id: int,
    method: str = "RFID",
) -> int:
    """
    Insert an attendance record with status 'Present'.

    Args:
        session_id: FK reference to sessions.id.
        student_id: FK reference to students.id.
        method:     'RFID' or 'Manual'.

    Returns:
        The id of the new attendance record.

    Raises:
        sqlite3.IntegrityError: If a record for (session_id, student_id) already exists.
    """
    timestamp = datetime.now(timezone.utc).isoformat()
    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO attendance (session_id, student_id, status, method, timestamp)
            VALUES (?, ?, 'Present', ?, ?);
            """,
            (session_id, student_id, method, timestamp),
        )
        new_id = cursor.lastrowid
    log_debug(
        f"Marked present: session={session_id} student={student_id} method={method}"
    )
    return new_id  # type: ignore[return-value]


def mark_absent(
    session_id: int,
    student_id: int,
    method: str = "Manual",
) -> int:
    """
    Insert an attendance record with status 'Absent'.

    Returns:
        The id of the new attendance record.
    """
    timestamp = datetime.now(timezone.utc).isoformat()
    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO attendance (session_id, student_id, status, method, timestamp)
            VALUES (?, ?, 'Absent', ?, ?);
            """,
            (session_id, student_id, method, timestamp),
        )
        new_id = cursor.lastrowid
    log_debug(
        f"Marked absent: session={session_id} student={student_id} method={method}"
    )
    return new_id  # type: ignore[return-value]


def toggle_status(session_id: int, student_id: int) -> str:
    """
    Toggle a student's attendance status between Present and Absent.
    Sets method to 'Manual' on every toggle (as required by the spec).

    Returns:
        The new status string ('Present' or 'Absent').

    Raises:
        ValueError: If no attendance record exists for (session_id, student_id).
    """
    timestamp = datetime.now(timezone.utc).isoformat()
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT status FROM attendance
            WHERE session_id = ? AND student_id = ?;
            """,
            (session_id, student_id),
        ).fetchone()

        if row is None:
            raise ValueError(
                f"No attendance record for session={session_id} student={student_id}"
            )

        new_status = "Absent" if row["status"] == "Present" else "Present"
        conn.execute(
            """
            UPDATE attendance
            SET status = ?, method = 'Manual', timestamp = ?
            WHERE session_id = ? AND student_id = ?;
            """,
            (new_status, timestamp, session_id, student_id),
        )
    log_debug(
        f"Toggled attendance: session={session_id} student={student_id} → {new_status}"
    )
    return new_status


def get_attendance_by_session(session_id: int) -> list[AttendanceRow]:
    """
    Return all attendance records for a session, joined with student names.

    Each returned row has:
        id, session_id, student_id, status, method, timestamp,
        first_name, last_name, card_id
    """
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT
                a.id, a.session_id, a.student_id,
                a.status, a.method, a.timestamp,
                s.first_name, s.last_name, s.card_id
            FROM attendance a
            JOIN students s ON s.id = a.student_id
            WHERE a.session_id = ?
            ORDER BY s.last_name, s.first_name;
            """,
            (session_id,),
        ).fetchall()
    return rows


def get_attendance_record(
    session_id: int, student_id: int
) -> Optional[AttendanceRow]:
    """Return a single attendance record or None if it doesn't exist."""
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT * FROM attendance
            WHERE session_id = ? AND student_id = ?;
            """,
            (session_id, student_id),
        ).fetchone()
    return row


def is_duplicate_tap(session_id: int, student_id: int) -> bool:
    """Return True if the student already has an attendance record in this session."""
    return get_attendance_record(session_id, student_id) is not None

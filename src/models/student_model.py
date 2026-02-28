"""
student_model.py — Data-access layer for the students and student_sections tables.

All methods open their own connection via get_connection() so callers at the
controller layer do not need to manage connections directly.
"""

import sqlite3
from datetime import datetime, timezone
from typing import Optional

from models.database import get_connection
from utils.logger import log_debug, log_error


# ── Type aliases (plain dicts for simplicity — no ORM) ───────────────────────
StudentRow = sqlite3.Row


def create_student(
    first_name: str,
    last_name: str,
    card_id: Optional[str] = None,
) -> int:
    """
    Insert a new student and return the new row id.

    Args:
        first_name: Student's first name.
        last_name:  Student's last name.
        card_id:    RFID card identifier; may be None if not yet assigned.

    Returns:
        The auto-incremented id of the newly created student.

    Raises:
        sqlite3.IntegrityError: If card_id is not unique.
        sqlite3.Error:          On any other DB error.
    """
    created_at = datetime.now(timezone.utc).isoformat()
    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO students (first_name, last_name, card_id, created_at)
            VALUES (?, ?, ?, ?);
            """,
            (first_name.strip(), last_name.strip(), card_id, created_at),
        )
        new_id = cursor.lastrowid
    log_debug(f"Created student id={new_id} name='{first_name} {last_name}'")
    return new_id  # type: ignore[return-value]


def get_student_by_id(student_id: int) -> Optional[StudentRow]:
    """Return a student row by primary key, or None if not found."""
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM students WHERE id = ?;", (student_id,)
        ).fetchone()
    return row


def get_student_by_card_id(card_id: str) -> Optional[StudentRow]:
    """Return a student row matching the given RFID card_id, or None."""
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM students WHERE card_id = ?;", (card_id,)
        ).fetchone()
    return row


def get_all_students() -> list[StudentRow]:
    """Return all students ordered by RFID card_id ascending (numerically), then name."""
    with get_connection() as conn:
        rows = conn.execute(
            """SELECT * FROM students
               ORDER BY CAST(card_id AS INTEGER) ASC, last_name, first_name;"""
        ).fetchall()
    return rows


def update_student(
    student_id: int,
    first_name: str,
    last_name: str,
) -> None:
    """Update a student's name fields. Use assign_card / remove_card for card changes."""
    with get_connection() as conn:
        conn.execute(
            """
            UPDATE students SET first_name = ?, last_name = ?
            WHERE id = ?;
            """,
            (first_name.strip(), last_name.strip(), student_id),
        )
    log_debug(f"Updated student id={student_id}")


def delete_student(student_id: int) -> None:
    """Delete a student and all their related records.

    Deletes in FK-safe order: attendance → student_sections → students.
    All three deletes share one transaction so a crash can’t leave orphans.
    """
    with get_connection() as conn:
        # Attendance records must go first (FK: attendance.student_id → students.id)
        conn.execute(
            "DELETE FROM attendance WHERE student_id = ?;", (student_id,)
        )
        conn.execute(
            "DELETE FROM student_sections WHERE student_id = ?;", (student_id,)
        )
        conn.execute("DELETE FROM students WHERE id = ?;", (student_id,))
    log_debug(f"Deleted student id={student_id} (including attendance records)")


def assign_card(student_id: int, card_id: str) -> None:
    """
    Set the card_id for a student.

    Raises:
        sqlite3.IntegrityError: If card_id is already assigned to another student.
    """
    with get_connection() as conn:
        conn.execute(
            "UPDATE students SET card_id = ? WHERE id = ?;",
            (card_id, student_id),
        )
    log_debug(f"Assigned card '{card_id}' to student id={student_id}")


def assign_card_to_student(student_id: int, card_id: str) -> tuple[bool, str]:
    """Atomically assign *card_id* to *student_id*.

    Clears the card from any other student in the same transaction before
    assigning it, eliminating the TOCTOU race that exists when doing
    ``get_student_by_card_id`` + ``assign_card`` across two connections.

    Returns:
        ``(True, "")`` on success.
        ``(False, reason)`` if a database constraint prevents the assignment.
    """
    try:
        with get_connection() as conn:
            # Drop the card from any existing holder first
            conn.execute(
                "UPDATE students SET card_id = NULL WHERE card_id = ? AND id != ?;",
                (card_id, student_id),
            )
            conn.execute(
                "UPDATE students SET card_id = ? WHERE id = ?;",
                (card_id, student_id),
            )
        log_debug(f"Atomic card assign: card='{card_id}' → student id={student_id}")
        return True, ""
    except sqlite3.IntegrityError:
        return False, "Card is already assigned to another student."


def remove_card(student_id: int) -> None:
    """Set card_id to NULL for the given student (before reassignment)."""
    with get_connection() as conn:
        conn.execute(
            "UPDATE students SET card_id = NULL WHERE id = ?;", (student_id,)
        )
    log_debug(f"Removed card from student id={student_id}")


def assign_section(student_id: int, section_id: int) -> None:
    """Enrol a student in a section (INSERT OR IGNORE to be idempotent)."""
    with get_connection() as conn:
        conn.execute(
            """
            INSERT OR IGNORE INTO student_sections (student_id, section_id)
            VALUES (?, ?);
            """,
            (student_id, section_id),
        )


def remove_section(student_id: int, section_id: int) -> None:
    """Remove a student from a section."""
    with get_connection() as conn:
        conn.execute(
            """
            DELETE FROM student_sections
            WHERE student_id = ? AND section_id = ?;
            """,
            (student_id, section_id),
        )


def get_sections_for_student(student_id: int) -> list[StudentRow]:
    """Return all section rows the student is enrolled in."""
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT s.*
            FROM sections s
            JOIN student_sections ss ON ss.section_id = s.id
            WHERE ss.student_id = ?
            ORDER BY s.name;
            """,
            (student_id,),
        ).fetchall()
    return rows


def set_inactive_status(student_id: int, inactive: bool) -> None:
    """Set or clear the is_inactive flag for a student (1 = inactive, 0 = active)."""
    with get_connection() as conn:
        conn.execute(
            "UPDATE students SET is_inactive = ? WHERE id = ?;",
            (1 if inactive else 0, student_id),
        )
    log_debug(
        f"Student id={student_id} marked {'inactive' if inactive else 'active'}"
    )

"""
section_model.py — Data-access layer for the sections and student_sections tables.
"""

import sqlite3
from typing import Optional

from models.database import get_connection
from utils.logger import log_debug

SectionRow = sqlite3.Row


def create_section(
    name: str,
    type_: str,
    level: str,
    day: str,
    time: str,
) -> int:
    """
    Insert a new section and return the new row id.

    Args:
        name:   Section display name.
        type_:  'Technique' or 'Normal'.
        level:  'Beginner', 'Intermediate', or 'Advanced'.
        day:    Day of week, e.g. 'Monday'.
        time:   Time string, e.g. '18:00'.

    Returns:
        The auto-incremented id of the new section.
    """
    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO sections (name, type, level, day, time)
            VALUES (?, ?, ?, ?, ?);
            """,
            (name.strip(), type_.strip(), level.strip(), day.strip(), time.strip()),
        )
        new_id = cursor.lastrowid
    log_debug(f"Created section id={new_id} name='{name}'")
    return new_id  # type: ignore[return-value]


def get_section_by_id(section_id: int) -> Optional[SectionRow]:
    """Return a section row by primary key, or None if not found."""
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM sections WHERE id = ?;", (section_id,)
        ).fetchone()
    return row


def get_all_sections() -> list[SectionRow]:
    """Return all sections ordered by name."""
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM sections ORDER BY name;"
        ).fetchall()
    return rows


def update_section(
    section_id: int,
    name: str,
    type_: str,
    level: str,
    day: str,
    time: str,
) -> None:
    """Update all editable fields of a section."""
    with get_connection() as conn:
        conn.execute(
            """
            UPDATE sections
            SET name = ?, type = ?, level = ?, day = ?, time = ?
            WHERE id = ?;
            """,
            (name.strip(), type_.strip(), level.strip(), day.strip(), time.strip(), section_id),
        )
    log_debug(f"Updated section id={section_id}")


def delete_section(section_id: int) -> None:
    """
    Delete a section and all related data in the correct FK order:
      1. attendance records whose session belongs to this section
      2. sessions belonging to this section
      3. student_sections enrolments
      4. the section itself
    """
    with get_connection() as conn:
        # 1. Remove attendance records linked to this section's sessions
        conn.execute(
            """
            DELETE FROM attendance
            WHERE session_id IN (
                SELECT id FROM sessions WHERE section_id = ?
            );
            """,
            (section_id,),
        )
        # 2. Remove sessions for this section
        conn.execute(
            "DELETE FROM sessions WHERE section_id = ?;", (section_id,)
        )
        # 3. Remove student enrolments
        conn.execute(
            "DELETE FROM student_sections WHERE section_id = ?;", (section_id,)
        )
        # 4. Remove the section row itself
        conn.execute("DELETE FROM sections WHERE id = ?;", (section_id,))
    log_debug(f"Deleted section id={section_id} (cascade)")


def get_enrolled_students(section_id: int) -> list[sqlite3.Row]:
    """Return all student rows enrolled in the given section."""
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT st.*
            FROM students st
            JOIN student_sections ss ON ss.student_id = st.id
            WHERE ss.section_id = ?
            ORDER BY st.last_name, st.first_name;
            """,
            (section_id,),
        ).fetchall()
    return rows


def get_sections_for_student_on_day(student_id: int, day: str) -> list[sqlite3.Row]:
    """
    Return all sections the given student is enrolled in that are scheduled
    on the specified weekday (case-insensitive match, e.g. 'Monday').
    """
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT s.*
            FROM sections s
            JOIN student_sections ss ON ss.section_id = s.id
            WHERE ss.student_id = ?
              AND LOWER(s.day) = LOWER(?);
            """,
            (student_id, day),
        ).fetchall()
    return rows

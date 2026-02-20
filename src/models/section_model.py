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
    Delete a section and all student enrolments for that section.
    Sessions and attendance records are retained for audit purposes.
    """
    with get_connection() as conn:
        conn.execute(
            "DELETE FROM student_sections WHERE section_id = ?;", (section_id,)
        )
        conn.execute("DELETE FROM sections WHERE id = ?;", (section_id,))
    log_debug(f"Deleted section id={section_id}")


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

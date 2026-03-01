"""
student_controller.py — Business logic for student registration and card management.

Responsibilities:
- Register a new student from an unknown card tap.
- Reassign an RFID card (with uniqueness validation and unlinking of old card).
- Search and sort the student list.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from typing import Optional

import models.student_model as student_model
import models.section_model as section_model
import models.attendance_model as attendance_model
from models.database import transaction
from utils.logger import log_info, log_error, log_warning
from utils.localization import turkish_lower


@dataclass
class RegistrationResult:
    """Result of register_new_student()."""
    success: bool
    student_id: Optional[int] = None
    message: str = ""


@dataclass
class CardReassignResult:
    """Result of reassign_card()."""
    success: bool
    message: str = ""


def register_new_student(
    first_name: str,
    last_name: str,
    card_id: str,
    section_id: Optional[int] = None,
) -> RegistrationResult:
    """
    Create a new student record and optionally enrol them in a section.

    Args:
        first_name: Student's first name (will be stripped).
        last_name:  Student's last name (will be stripped).
        card_id:    RFID card id to assign immediately.
        section_id: Optional section to enrol the student in.

    Returns:
        RegistrationResult with success flag and new student_id.
    """
    first_name = first_name.strip()
    last_name  = last_name.strip()
    card_id    = card_id.strip()

    if not first_name or not last_name:
        return RegistrationResult(
            success=False,
            message="First name and last name are required.",
        )

    if not card_id:
        return RegistrationResult(
            success=False,
            message="Card ID cannot be empty.",
        )

    # Check card uniqueness before attempting insert
    existing = student_model.get_student_by_card_id(card_id)
    if existing is not None:
        return RegistrationResult(
            success=False,
            message=(
                f"Card '{card_id}' is already assigned to "
                f"{existing['first_name']} {existing['last_name']}."
            ),
        )

    try:
        student_id = student_model.create_student(first_name, last_name, card_id)

        if section_id is not None:
            student_model.assign_section(student_id, section_id)
            log_info(
                f"Registered student id={student_id} "
                f"name='{first_name} {last_name}' card='{card_id}' "
                f"section={section_id}"
            )
        else:
            log_info(
                f"Registered student id={student_id} "
                f"name='{first_name} {last_name}' card='{card_id}' (no section)"
            )

        return RegistrationResult(
            success=True,
            student_id=student_id,
            message=f"Student '{first_name} {last_name}' registered successfully.",
        )

    except sqlite3.IntegrityError as exc:
        log_error(f"IntegrityError during registration: {exc}")
        return RegistrationResult(
            success=False,
            message=f"Registration failed — duplicate card or data constraint:\n{exc}",
        )
    except sqlite3.Error as exc:
        log_error(f"DB error during registration: {exc}")
        return RegistrationResult(
            success=False,
            message="A database error occurred during registration.",
        )


def register_student_with_sections(
    first_name: str,
    last_name: str,
    card_id: str,
    section_ids: list[int],
) -> RegistrationResult:
    """
    Register a new student with a pre-scanned RFID card and multiple section
    enrolments in a single call.

    Used by the passive-flow registration dialog (unknown card tapped → dialog
    → this function).

    Args:
        first_name:   Student's first name.
        last_name:    Student's last name.
        card_id:      RFID card id to assign (must be unique).
        section_ids:  List of section ids to enrol the student in (may be empty).

    Returns:
        RegistrationResult with success flag and new student_id on success.
    """
    first_name = first_name.strip()
    last_name  = last_name.strip()
    card_id    = card_id.strip()

    if not first_name or not last_name:
        return RegistrationResult(
            success=False,
            message="First name and last name are required.",
        )

    if not card_id:
        return RegistrationResult(
            success=False,
            message="Card ID cannot be empty.",
        )

    existing = student_model.get_student_by_card_id(card_id)
    if existing is not None:
        return RegistrationResult(
            success=False,
            message=(
                f"Card '{card_id}' is already assigned to "
                f"{existing['first_name']} {existing['last_name']}."
            ),
        )

    try:
        student_id = student_model.create_student(first_name, last_name, card_id)
        for sec_id in section_ids:
            student_model.assign_section(student_id, sec_id)
        log_info(
            f"Registered student id={student_id} name='{first_name} {last_name}' "
            f"card='{card_id}' sections={section_ids}"
        )
        return RegistrationResult(
            success=True,
            student_id=student_id,
            message=f"Student '{first_name} {last_name}' registered successfully.",
        )
    except sqlite3.IntegrityError as exc:
        log_error(f"IntegrityError during register_student_with_sections: {exc}")
        return RegistrationResult(
            success=False,
            message=f"Registration failed — duplicate card or data conflict:\n{exc}",
        )
    except sqlite3.Error as exc:
        log_error(f"DB error during register_student_with_sections: {exc}")
        return RegistrationResult(
            success=False,
            message="A database error occurred during registration.",
        )


def reassign_card(student_id: int, new_card_id: str) -> CardReassignResult:
    """Atomically reassign an RFID card to a student.

    Delegates to ``student_model.assign_card_to_student()`` which handles
    clearing the card from any previous holder in a single DB round-trip,
    eliminating the TOCTOU race that existed with the old check-then-act
    pattern.

    Args:
        student_id:  Target student.
        new_card_id: The new card to assign.
    """
    new_card_id = new_card_id.strip()

    if not new_card_id:
        return CardReassignResult(success=False, message="Card ID cannot be empty.")

    try:
        ok, err = student_model.assign_card_to_student(student_id, new_card_id)
        if not ok:
            return CardReassignResult(success=False, message=err)

        log_info(f"Card reassigned: student_id={student_id} new_card='{new_card_id}'")
        return CardReassignResult(
            success=True,
            message=f"Card '{new_card_id}' has been assigned successfully.",
        )

    except sqlite3.IntegrityError as exc:
        log_error(f"IntegrityError during card reassignment: {exc}")
        return CardReassignResult(
            success=False,
            message=f"Card reassignment failed — constraint violated:\n{exc}",
        )
    except sqlite3.Error as exc:
        log_error(f"DB error during card reassignment: {exc}")
        return CardReassignResult(
            success=False,
            message="A database error occurred during card reassignment.",
        )


def search_students(query: str) -> list:
    """
    Return students whose first name, last name, or card_id contain the query
    string (case-insensitive).

    Args:
        query: Search string; empty string returns all students.
    """
    if not query.strip():
        return list(student_model.get_all_students())

    q = f"%{query.strip()}%"
    from models.database import get_connection
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT * FROM students
            WHERE first_name LIKE ? COLLATE NOCASE
               OR last_name  LIKE ? COLLATE NOCASE
               OR card_id    LIKE ? COLLATE NOCASE
            ORDER BY last_name, first_name;
            """,
            (q, q, q),
        ).fetchall()
    return list(rows)


def sort_students(
    students: list,
    sort_by: str = "last_name",
    ascending: bool = True,
) -> list:
    """
    Sort a list of student rows by a given column.

    Args:
        students:  List of student rows (sqlite3.Row or dict).
        sort_by:   Column name: 'last_name', 'first_name', or 'card_id'.
        ascending: Sort direction.
    """
    def _key(s: object) -> str:
        val = s[sort_by] if s[sort_by] is not None else ""  # type: ignore[index]
        return turkish_lower(str(val))

    return sorted(students, key=_key, reverse=not ascending)


def get_all_students() -> list:
    """Return the full student list (pass-through to model)."""
    return list(student_model.get_all_students())


def get_student_with_sections_by_id(student_id: int) -> Optional[dict]:
    """Return a single student enriched with section names and attendance info.

    Uses a targeted SQL query instead of loading all students.  Returns ``None``
    if the student does not exist.
    """
    from models.database import get_connection

    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT s.id, s.first_name, s.last_name, s.card_id, s.is_inactive,
                   GROUP_CONCAT(DISTINCT sec.name) AS section_names,
                   COUNT(CASE WHEN a.status = 'Present' THEN 1 END) AS attended,
                   COUNT(DISTINCT sess.id) AS total_sessions
            FROM   students s
            LEFT JOIN student_sections ss  ON ss.student_id = s.id
            LEFT JOIN sections sec         ON sec.id = ss.section_id
            LEFT JOIN sessions sess        ON sess.section_id = ss.section_id
            LEFT JOIN attendance a         ON a.student_id = s.id
                                          AND a.session_id = sess.id
            WHERE  s.id = ?
            GROUP BY s.id;
            """,
            (student_id,),
        ).fetchone()

    if row is None:
        return None

    attended = row["attended"] or 0
    total = row["total_sessions"] or 0
    pct = f"{attended / total * 100:.0f}%" if total > 0 else "—"
    return {
        "id":             row["id"],
        "first_name":     row["first_name"],
        "last_name":      row["last_name"],
        "card_id":        row["card_id"] or "",
        "sections":       row["section_names"] or "—",
        "is_inactive":    bool(row["is_inactive"]),
        "attended":       attended,
        "total_sessions": total,
        "attendance_pct": pct,
    }


def get_student_by_card_id(card_id: str):
    """Return a student row by card_id, or None."""
    return student_model.get_student_by_card_id(card_id)


def delete_student(student_id: int) -> tuple[bool, str]:
    """
    Delete a student by id.

    Returns:
        (True, "") on success, (False, error_message) on failure.
    """
    try:
        student_model.delete_student(student_id)
        log_info(f"Student deleted: id={student_id}")
        return True, ""
    except sqlite3.Error as exc:
        log_error(f"DB error deleting student id={student_id}: {exc}")
        return False, f"Database error: {exc}"


def update_student(
    student_id: int,
    first_name: str,
    last_name: str,
) -> tuple[bool, str]:
    """
    Update a student's name.

    Returns:
        (True, "") on success, (False, error_message) on failure.
    """
    if not first_name.strip() or not last_name.strip():
        return False, "First name and last name are required."
    try:
        student_model.update_student(student_id, first_name, last_name)
        return True, ""
    except sqlite3.Error as exc:
        log_error(f"DB error updating student id={student_id}: {exc}")
        return False, f"Database error: {exc}"


def get_all_students_with_sections() -> list[dict]:
    """
    Return all students enriched with their comma-separated section names,
    attendance percentage, and inactive status.

    Optimised: uses 2 bulk queries instead of N+1 per-student calls.

    Returns:
        List of dicts: {id, first_name, last_name, card_id, sections,
                        is_inactive, attended, total_sessions, attendance_pct}.
        card_id is '' if not assigned.  sections is '—' if none.
        attendance_pct is e.g. '80%' or '—' if no sessions.
    """
    from models.database import get_connection

    # Single query: students + section names + attendance summary
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT s.id, s.first_name, s.last_name, s.card_id, s.is_inactive,
                   GROUP_CONCAT(DISTINCT sec.name) AS section_names,
                   COUNT(CASE WHEN a.status = 'Present' THEN 1 END) AS attended,
                   COUNT(DISTINCT sess.id) AS total_sessions
            FROM   students s
            LEFT JOIN student_sections ss  ON ss.student_id = s.id
            LEFT JOIN sections sec         ON sec.id = ss.section_id
            LEFT JOIN sessions sess        ON sess.section_id = ss.section_id
            LEFT JOIN attendance a         ON a.student_id = s.id
                                          AND a.session_id = sess.id
            GROUP BY s.id
            ORDER BY CAST(s.card_id AS INTEGER) ASC, s.last_name, s.first_name;
            """,
        ).fetchall()

    result: list[dict] = []
    for row in rows:
        section_names = row["section_names"] or "—"
        attended = row["attended"] or 0
        total = row["total_sessions"] or 0
        pct = f"{attended / total * 100:.0f}%" if total > 0 else "—"
        result.append({
            "id":             row["id"],
            "first_name":     row["first_name"],
            "last_name":      row["last_name"],
            "card_id":        row["card_id"] or "",
            "sections":       section_names,
            "is_inactive":    bool(row["is_inactive"]),
            "attended":       attended,
            "total_sessions": total,
            "attendance_pct": pct,
        })
    return result


def create_student_manually(
    first_name: str,
    last_name: str,
    section_ids: Optional[list[int]] = None,
) -> RegistrationResult:
    """
    Create a new student without an RFID card (admin-initiated, not via tap).

    The student's card_id remains NULL until they tap a card for the first time.

    Args:
        first_name:  Student's first name.
        last_name:   Student's last name.
        section_ids: Optional list of section ids to enrol the student in.

    Returns:
        RegistrationResult with success flag and new student_id.
    """
    first_name = first_name.strip()
    last_name  = last_name.strip()

    if not first_name or not last_name:
        return RegistrationResult(
            success=False,
            message="First name and last name are required.",
        )

    try:
        student_id = student_model.create_student(first_name, last_name, card_id=None)

        if section_ids:
            for sid in section_ids:
                student_model.assign_section(student_id, sid)

        log_info(
            f"Manually created student id={student_id} "
            f"name='{first_name} {last_name}' sections={section_ids}"
        )
        return RegistrationResult(
            success=True,
            student_id=student_id,
            message=f"Student '{first_name} {last_name}' added successfully.",
        )

    except sqlite3.Error as exc:
        log_error(f"DB error creating student manually: {exc}")
        return RegistrationResult(
            success=False,
            message=f"A database error occurred: {exc}",
        )


def update_student_sections(
    student_id: int,
    section_ids: list[int],
) -> tuple[bool, str]:
    """Atomically replace a student's section enrolments.

    Deletes all existing enrolments and inserts the new list within a single
    transaction (W2 fix).  If the app crashes between the DELETE and the final
    INSERT the entire operation is rolled back, so the student is never left
    with zero sections due to a partial write.

    Args:
        student_id:  Target student id.
        section_ids: New list of section ids (may be empty).

    Returns:
        (True, "") on success, (False, error_message) on failure.
    """
    try:
        with transaction() as conn:
            conn.execute(
                "DELETE FROM student_sections WHERE student_id = ?;",
                (student_id,),
            )
            for sec_id in section_ids:
                conn.execute(
                    """
                    INSERT OR IGNORE INTO student_sections (student_id, section_id)
                    VALUES (?, ?);
                    """,
                    (student_id, sec_id),
                )
        log_info(
            f"Section memberships updated for student_id={student_id}: {section_ids}"
        )
        return True, ""
    except sqlite3.Error as exc:
        log_error(
            f"DB error updating sections for student_id={student_id}: {exc}"
        )
        return False, f"Database error: {exc}"


def get_enrolled_section_ids(student_id: int) -> set[int]:
    """
    Return the set of section IDs the student is currently enrolled in.

    Args:
        student_id: Target student id.

    Returns:
        Set of integer section ids (empty set on error or no enrolments).
    """
    try:
        rows = student_model.get_sections_for_student(student_id)
        return {row["id"] for row in rows}
    except sqlite3.Error as exc:
        log_error(f"DB error fetching enrolled sections for student_id={student_id}: {exc}")
        return set()


def remove_student_card(student_id: int) -> tuple[bool, str]:
    """
    Remove (unlink) the RFID card from a student, setting card_id to NULL.

    Returns:
        (True, "") on success, (False, error_message) on failure.
    """
    try:
        student_model.remove_card(student_id)
        log_info(f"Card removed from student_id={student_id}")
        return True, ""
    except sqlite3.Error as exc:
        log_error(f"DB error removing card for student_id={student_id}: {exc}")
        return False, f"Database error: {exc}"

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
from utils.logger import log_info, log_error, log_warning


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


def reassign_card(student_id: int, new_card_id: str) -> CardReassignResult:
    """
    Reassign a new RFID card to a student.

    Steps:
    1. Validate new_card_id is not already assigned to anyone.
    2. NULL-out old card_id for this student.
    3. Assign new_card_id.

    Args:
        student_id:  Target student.
        new_card_id: The new card to assign.
    """
    new_card_id = new_card_id.strip()

    if not new_card_id:
        return CardReassignResult(success=False, message="Card ID cannot be empty.")

    try:
        # Check if the new card is already in use
        holder = student_model.get_student_by_card_id(new_card_id)
        if holder is not None and holder["id"] != student_id:
            return CardReassignResult(
                success=False,
                message=(
                    f"Card '{new_card_id}' is already assigned to "
                    f"{holder['first_name']} {holder['last_name']}."
                ),
            )

        # Unlink old card first (maintains UNIQUE constraint safety)
        student_model.remove_card(student_id)
        student_model.assign_card(student_id, new_card_id)

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
    all_students = student_model.get_all_students()
    if not query.strip():
        return list(all_students)

    q = query.strip().lower()
    return [
        s for s in all_students
        if q in s["first_name"].lower()
        or q in s["last_name"].lower()
        or (s["card_id"] and q in s["card_id"].lower())
    ]


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
        return str(val).lower()

    return sorted(students, key=_key, reverse=not ascending)


def get_all_students() -> list:
    """Return the full student list (pass-through to model)."""
    return list(student_model.get_all_students())


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

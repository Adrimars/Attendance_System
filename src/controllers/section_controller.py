"""
section_controller.py — Business logic for section CRUD orchestration.
"""

from __future__ import annotations

import sqlite3
from typing import Optional

import models.section_model as section_model
from utils.logger import log_info, log_error

_VALID_TYPES  = {"Technique", "Normal"}
_VALID_LEVELS = {"Beginner", "Intermediate", "Advanced"}
_VALID_DAYS   = {
    "Monday", "Tuesday", "Wednesday", "Thursday",
    "Friday", "Saturday", "Sunday",
}


def _validate(
    name: str,
    type_: str,
    level: str,
    day: str,
    time: str,
) -> Optional[str]:
    """Return an error message string if inputs are invalid, else None."""
    if not name.strip():
        return "Section name cannot be empty."
    if type_ not in _VALID_TYPES:
        return f"Type must be one of: {', '.join(sorted(_VALID_TYPES))}."
    if level not in _VALID_LEVELS:
        return f"Level must be one of: {', '.join(sorted(_VALID_LEVELS))}."
    if day not in _VALID_DAYS:
        return f"Day must be a full weekday name (e.g. 'Monday')."
    if not time.strip():
        return "Time cannot be empty."
    return None


def create_section(
    name: str,
    type_: str,
    level: str,
    day: str,
    time: str,
) -> tuple[bool, str, Optional[int]]:
    """
    Create a new section after validation.

    Returns:
        (True, "", new_section_id) on success.
        (False, error_message, None) on validation or DB error.
    """
    err = _validate(name, type_, level, day, time)
    if err:
        return False, err, None

    try:
        new_id = section_model.create_section(name, type_, level, day, time)
        log_info(f"Section created: id={new_id} name='{name}'")
        return True, "", new_id
    except sqlite3.Error as exc:
        log_error(f"DB error creating section: {exc}")
        return False, f"Database error: {exc}", None


def update_section(
    section_id: int,
    name: str,
    type_: str,
    level: str,
    day: str,
    time: str,
) -> tuple[bool, str]:
    """
    Update an existing section after validation.

    Returns:
        (True, "") on success.
        (False, error_message) on failure.
    """
    err = _validate(name, type_, level, day, time)
    if err:
        return False, err

    try:
        section_model.update_section(section_id, name, type_, level, day, time)
        log_info(f"Section updated: id={section_id}")
        return True, ""
    except sqlite3.Error as exc:
        log_error(f"DB error updating section id={section_id}: {exc}")
        return False, f"Database error: {exc}"


def delete_section(section_id: int) -> tuple[bool, str]:
    """
    Delete a section and its student enrolments.

    Returns:
        (True, "") on success, (False, error_message) on failure.
    """
    try:
        section_model.delete_section(section_id)
        log_info(f"Section deleted: id={section_id}")
        return True, ""
    except sqlite3.Error as exc:
        log_error(f"DB error deleting section id={section_id}: {exc}")
        return False, f"Database error: {exc}"


def get_all_sections() -> list:
    """Return all sections (pass-through to model)."""
    return list(section_model.get_all_sections())


def get_section_by_id(section_id: int):
    """Return a single section row or None."""
    return section_model.get_section_by_id(section_id)


def get_enrolled_students(section_id: int) -> list:
    """Return all students enrolled in the given section."""
    return list(section_model.get_enrolled_students(section_id))

"""
attendance_controller.py — Business logic for processing RFID card taps.

The controller is the only consumer of attendance_model and student_model
for tap-processing.  Views call process_card_tap() and act on the returned
TapResult.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from enum import Enum, auto
from typing import Optional

import models.attendance_model as attendance_model
import models.student_model as student_model
from utils.logger import log_info, log_error, log_warning


class TapResultType(Enum):
    """Describes the outcome of a card tap so the view can display the right feedback."""
    KNOWN_PRESENT   = auto()   # Known student → marked Present (Green flash)
    UNKNOWN_CARD    = auto()   # Card not in DB → registration required (Red flash)
    DUPLICATE_TAP   = auto()   # Student already marked in this session (Yellow flash)
    NO_SESSION      = auto()   # No active session — tap ignored
    ERROR           = auto()   # Unexpected error (show dialog)


@dataclass
class TapResult:
    """Return value from process_card_tap(); carries all info the view needs."""
    result_type: TapResultType
    card_id: str
    student_id: Optional[int] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    message: str = ""
    error: Optional[Exception] = None


def process_card_tap(card_id: str, session_id: Optional[int]) -> TapResult:
    """
    Core tap-processing pipeline:

    1. Reject if no active session.
    2. Look up card in students table.
    3. If unknown  → return UNKNOWN_CARD (view opens registration dialog).
    4. If duplicate → return DUPLICATE_TAP (view shows yellow flash).
    5. If known    → mark Present via RFID, return KNOWN_PRESENT.

    Args:
        card_id:    The raw card identifier string from the RFID reader.
        session_id: The currently active session id, or None.

    Returns:
        A TapResult describing what happened.
    """
    card_id = card_id.strip()

    if not card_id:
        return TapResult(
            result_type=TapResultType.ERROR,
            card_id=card_id,
            message="Empty card ID received.",
        )

    if session_id is None:
        return TapResult(
            result_type=TapResultType.NO_SESSION,
            card_id=card_id,
            message="No active session. Start a session first.",
        )

    try:
        student = student_model.get_student_by_card_id(card_id)

        if student is None:
            log_info(f"Unknown card tap: '{card_id}'")
            return TapResult(
                result_type=TapResultType.UNKNOWN_CARD,
                card_id=card_id,
                message="Unregistered card — please complete registration.",
            )

        student_id: int = student["id"]
        first_name: str = student["first_name"]
        last_name: str  = student["last_name"]

        if attendance_model.is_duplicate_tap(session_id, student_id):
            log_warning(
                f"Duplicate tap: student_id={student_id} session_id={session_id}"
            )
            return TapResult(
                result_type=TapResultType.DUPLICATE_TAP,
                card_id=card_id,
                student_id=student_id,
                first_name=first_name,
                last_name=last_name,
                message=f"{first_name} {last_name} is already marked present.",
            )

        attendance_model.mark_present(session_id, student_id, method="RFID")
        log_info(
            f"Card tap OK: card='{card_id}' student_id={student_id} "
            f"name='{first_name} {last_name}' session={session_id}"
        )
        return TapResult(
            result_type=TapResultType.KNOWN_PRESENT,
            card_id=card_id,
            student_id=student_id,
            first_name=first_name,
            last_name=last_name,
            message=f"{first_name} {last_name} marked present.",
        )

    except sqlite3.Error as exc:
        log_error(f"DB error in process_card_tap: {exc}")
        return TapResult(
            result_type=TapResultType.ERROR,
            card_id=card_id,
            message="A database error occurred. Please check the logs.",
            error=exc,
        )


def record_attendance_after_registration(
    session_id: int, student_id: int
) -> bool:
    """
    Called after successful registration from the registration dialog to mark
    the newly created student as present in the current session.

    Returns:
        True on success, False on failure.
    """
    try:
        attendance_model.mark_present(session_id, student_id, method="RFID")
        log_info(
            f"Post-registration attendance: session={session_id} student={student_id}"
        )
        return True
    except sqlite3.Error as exc:
        log_error(f"DB error in record_attendance_after_registration: {exc}")
        return False


def toggle_attendance(session_id: int, student_id: int) -> Optional[str]:
    """
    Toggle a student's attendance status (Manual override).

    Returns:
        The new status string ('Present' or 'Absent'), or None on error.
    """
    try:
        new_status = attendance_model.toggle_status(session_id, student_id)
        log_info(
            f"Manual toggle: session={session_id} student={student_id} → {new_status}"
        )
        return new_status
    except (sqlite3.Error, ValueError) as exc:
        log_error(f"Error toggling attendance: {exc}")
        return None

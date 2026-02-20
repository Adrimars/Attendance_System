"""
attendance_controller.py — Business logic for processing RFID card taps.

The controller is the only consumer of attendance_model and student_model
for tap-processing.  Views call process_card_tap() and act on the returned
TapResult.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum, auto
from typing import Optional

import models.attendance_model as attendance_model
import models.student_model as student_model
import models.section_model as section_model
import models.session_model as session_model
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


def mark_present_manual(session_id: int, student_id: int) -> tuple[bool, str]:
    """
    Mark a student as Present with method='Manual' (RFID fallback path).

    If the student already has a Present record, this is a no-op and returns
    True.  If they are Absent, their record is toggled to Present.  If no
    record exists at all, a new Present record is inserted.

    Args:
        session_id: The active session id.
        student_id: The student to mark present.

    Returns:
        (True, "")            on success or already-present.
        (False, error_msg)    on failure.
    """
    try:
        existing = attendance_model.get_attendance_record(session_id, student_id)
        if existing is None:
            # No record yet — insert as Present/Manual
            attendance_model.mark_present(session_id, student_id, method="Manual")
            log_info(
                f"Manual mark-present: session={session_id} student={student_id} (new record)"
            )
        elif existing["status"] == "Absent":
            attendance_model.toggle_status(session_id, student_id)
            log_info(
                f"Manual mark-present (toggle): session={session_id} student={student_id}"
            )
        # else already Present — nothing to do
        return True, ""
    except sqlite3.Error as exc:
        log_error(f"DB error in mark_present_manual: {exc}")
        return False, f"Database error: {exc}"


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


@dataclass
class PassiveTapResult:
    """Result from process_rfid_passive(); carries all info the Attendance view needs."""
    result_type: TapResultType
    card_id: str
    student_id: Optional[int] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    sections_marked: list = field(default_factory=list)   # names of newly-marked sections
    sections_duplicate: list = field(default_factory=list) # names of already-marked sections
    message: str = ""


def process_rfid_passive(card_id: str) -> PassiveTapResult:
    """
    Passive (always-on) RFID tap processing used in the new attendance flow.

    Steps:
      1. Look up card_id in the students table.
      2. If unknown → return UNKNOWN_CARD (view opens registration dialog).
      3. If known → find all sections the student is enrolled in whose *day*
         matches today’s weekday name.
      4. For each matching section auto-create (or reuse) a daily session.
      5. Mark the student Present in every section not yet marked today.
      6. Return a PassiveTapResult with a human-readable summary.

    Note: If a student has no section scheduled today a KNOWN_PRESENT result
    is still returned (sections_marked will be empty) so the view can show an
    informational message rather than an error.
    """
    card_id = card_id.strip()
    if not card_id:
        return PassiveTapResult(
            result_type=TapResultType.ERROR,
            card_id=card_id,
            message="Empty card ID received.",
        )

    try:
        student = student_model.get_student_by_card_id(card_id)
        if student is None:
            log_info(f"Passive tap — unknown card: '{card_id}'")
            return PassiveTapResult(
                result_type=TapResultType.UNKNOWN_CARD,
                card_id=card_id,
                message="Unregistered card — please register the student.",
            )

        student_id: int  = student["id"]
        first_name: str  = student["first_name"]
        last_name: str   = student["last_name"]

        today_date: str = date.today().isoformat()           # 'YYYY-MM-DD'
        today_day: str  = datetime.now().strftime("%A")      # 'Monday' … 'Sunday'

        sections_today = section_model.get_sections_for_student_on_day(student_id, today_day)

        if not sections_today:
            log_info(
                f"Passive tap: student_id={student_id} ({first_name} {last_name}) — "
                f"no sections scheduled on {today_day}."
            )
            return PassiveTapResult(
                result_type=TapResultType.KNOWN_PRESENT,
                card_id=card_id,
                student_id=student_id,
                first_name=first_name,
                last_name=last_name,
                sections_marked=[],
                message=f"{first_name} {last_name} — no sections today ({today_day}).",
            )

        newly_marked: list[str] = []
        already_marked: list[str] = []

        for sec in sections_today:
            session_id = session_model.get_or_create_session(sec["id"], today_date)
            if attendance_model.is_duplicate_tap(session_id, student_id):
                already_marked.append(sec["name"])
            else:
                attendance_model.mark_present(session_id, student_id, method="RFID")
                newly_marked.append(sec["name"])

        if newly_marked:
            log_info(
                f"Passive tap OK: student_id={student_id} "
                f"sections_marked={newly_marked}"
            )
            result_type = TapResultType.KNOWN_PRESENT
            message = (
                f"{first_name} {last_name} — present: {', '.join(newly_marked)}"
            )
        else:
            log_info(
                f"Passive tap duplicate: student_id={student_id} "
                f"all sections already marked={already_marked}"
            )
            result_type = TapResultType.DUPLICATE_TAP
            message = (
                f"{first_name} {last_name} already marked today: "
                f"{', '.join(already_marked)}"
            )

        return PassiveTapResult(
            result_type=result_type,
            card_id=card_id,
            student_id=student_id,
            first_name=first_name,
            last_name=last_name,
            sections_marked=newly_marked,
            sections_duplicate=already_marked,
            message=message,
        )

    except sqlite3.Error as exc:
        log_error(f"DB error in process_rfid_passive: {exc}")
        return PassiveTapResult(
            result_type=TapResultType.ERROR,
            card_id=card_id,
            message="A database error occurred. Please check the logs.",
        )


def get_student_attendance_overview(student_id: int, date_str: str) -> list[dict]:
    """
    Return attendance status for a student across all enrolled sections on a date.

    Each item in the returned list is a dict with:
        section_id, section_name, day, time,
        session_id (None if no session exists on date_str),
        status ('Present', 'Absent', or None if no record).
    """
    sections = student_model.get_sections_for_student(student_id)
    result: list[dict] = []
    for sec in sections:
        session = session_model.get_existing_session_for_date(sec["id"], date_str)
        session_id: Optional[int] = session["id"] if session else None
        status: Optional[str] = None
        if session_id is not None:
            record = attendance_model.get_attendance_record(session_id, student_id)
            if record:
                status = record["status"]
        result.append({
            "section_id":   sec["id"],
            "section_name": sec["name"],
            "day":          sec["day"],
            "time":         sec["time"] if sec["time"] else "",
            "session_id":   session_id,
            "status":       status,
        })
    return result


def set_student_attendance(
    student_id: int, section_id: int, date_str: str, target_status: str
) -> tuple[bool, str]:
    """
    Explicitly set a student's attendance to 'Present' or 'Absent' for a given
    section and date. Creates a session automatically if one does not yet exist.

    Returns:
        (True, "") on success.
        (False, error_message) on failure.
    """
    try:
        session_id = session_model.get_or_create_session(section_id, date_str)
        record = attendance_model.get_attendance_record(session_id, student_id)
        if record is None:
            if target_status == "Present":
                attendance_model.mark_present(session_id, student_id, method="Manual")
            else:
                attendance_model.mark_absent(session_id, student_id, method="Manual")
        elif record["status"] != target_status:
            attendance_model.toggle_status(session_id, student_id)
        # else: already correct status — no-op
        log_info(
            f"Manual attendance set: student={student_id} section={section_id} "
            f"date={date_str} status={target_status}"
        )
        return True, ""
    except sqlite3.Error as exc:
        log_error(f"DB error in set_student_attendance: {exc}")
        return False, f"Database error: {exc}"

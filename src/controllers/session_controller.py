"""
session_controller.py — Business logic for session lifecycle management.

Responsibilities:
- Start a session (validate section, check for duplicate, create).
- End a session (collect absent summary, close record).
- Provide live attendance state for the view.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import date
from typing import Optional

import models.session_model as session_model
import models.section_model as section_model
import models.student_model as student_model
import models.attendance_model as attendance_model
from utils.logger import log_info, log_error, log_warning


@dataclass
class SessionStartResult:
    """Outcome of start_session()."""
    success: bool
    session_id: Optional[int] = None
    message: str = ""
    existing_session_id: Optional[int] = None   # Set when duplicate detected


@dataclass
class AbsentStudentInfo:
    """Information about a single absent student, used in the End Session summary."""
    student_id: int
    first_name: str
    last_name: str


@dataclass
class SessionSummary:
    """Full summary generated when ending a session."""
    session_id: int
    section_name: str
    total_enrolled: int
    present_count: int
    absent_count: int
    absent_students: list[AbsentStudentInfo]


def start_session(section_id: int) -> SessionStartResult:
    """
    Start an attendance session for the given section.

    Checks for:
      - Invalid section_id.
      - An already-active session for this section (any date).
      - An existing session for *today* (prompts to resume rather than duplicate).

    Args:
        section_id: The section to start a session for.

    Returns:
        SessionStartResult with success flag and session_id on success.
    """
    try:
        section = section_model.get_section_by_id(section_id)
        if section is None:
            return SessionStartResult(
                success=False,
                message=f"Section id={section_id} does not exist.",
            )

        # Check for an already-active session (any date)
        active = session_model.get_active_session(section_id)
        if active is not None:
            log_warning(
                f"Attempted to start session but active session "
                f"id={active['id']} already exists for section_id={section_id}."
            )
            return SessionStartResult(
                success=False,
                message=(
                    f"A session is already active for '{section['name']}' "
                    f"(started {active['start_time'][:16]}).\n"
                    "End the current session before starting a new one."
                ),
                existing_session_id=active["id"],
            )

        # Check for existing session today (closed, but same date)
        today_str = date.today().isoformat()
        existing_today = session_model.get_existing_session_for_date(
            section_id, today_str
        )
        if existing_today is not None and existing_today["status"] == "closed":
            log_warning(
                f"Session already exists for section={section_id} date={today_str}."
            )
            return SessionStartResult(
                success=False,
                message=(
                    f"A session already exists for '{section['name']}' today "
                    f"({today_str}) and it is closed.\n"
                    "Create a second session only if you are sure."
                ),
                existing_session_id=existing_today["id"],
            )

        new_id = session_model.create_session(section_id)
        log_info(f"Session started: id={new_id} section='{section['name']}'")
        return SessionStartResult(
            success=True,
            session_id=new_id,
            message=f"Session started for '{section['name']}'.",
        )

    except sqlite3.Error as exc:
        log_error(f"DB error in start_session: {exc}")
        return SessionStartResult(
            success=False,
            message="A database error occurred while starting the session.",
        )


def end_session(session_id: int) -> Optional[SessionSummary]:
    """
    Close a session and return the absent summary.

    Enrolled students without a 'Present' attendance record are considered absent.
    Those students get an 'Absent' / 'Manual' record written automatically.

    Args:
        session_id: The session to close.

    Returns:
        A SessionSummary, or None on error.
    """
    try:
        sess = session_model.get_session_by_id(session_id)
        if sess is None:
            log_error(f"end_session called for non-existent session_id={session_id}")
            return None

        section = section_model.get_section_by_id(sess["section_id"])
        section_name: str = section["name"] if section else f"Section {sess['section_id']}"

        enrolled = section_model.get_enrolled_students(sess["section_id"])
        attendance_rows = attendance_model.get_attendance_by_session(session_id)
        present_ids: set[int] = {
            row["student_id"]
            for row in attendance_rows
            if row["status"] == "Present"
        }

        absent_students: list[AbsentStudentInfo] = []
        for student in enrolled:
            if student["id"] not in present_ids and not student["is_inactive"]:
                # Auto-create absence record so the session is complete
                try:
                    attendance_model.mark_absent(session_id, student["id"], method="Manual")
                except sqlite3.IntegrityError:
                    pass  # Record may already exist (e.g. manually marked absent earlier)
                absent_students.append(
                    AbsentStudentInfo(
                        student_id=student["id"],
                        first_name=student["first_name"],
                        last_name=student["last_name"],
                    )
                )

        session_model.close_session(session_id)

        summary = SessionSummary(
            session_id=session_id,
            section_name=section_name,
            total_enrolled=len(enrolled),
            present_count=len(present_ids),
            absent_count=len(absent_students),
            absent_students=absent_students,
        )
        log_info(
            f"Session ended: id={session_id} present={summary.present_count} "
            f"absent={summary.absent_count}"
        )
        return summary

    except sqlite3.Error as exc:
        log_error(f"DB error in end_session: {exc}")
        return None


def get_live_attendance(session_id: int) -> list[dict]:
    """
    Return a list of dicts describing the current attendance state of all
    enrolled students for the session's section.

    Each dict contains:
        student_id, first_name, last_name, card_id,
        status ('Present' | 'Absent' | 'Not Recorded'),
        method ('RFID' | 'Manual' | '')

    Used by the view to refresh the live student list.
    """
    try:
        sess = session_model.get_session_by_id(session_id)
        if sess is None:
            return []

        enrolled = section_model.get_enrolled_students(sess["section_id"])
        attendance_map: dict[int, dict] = {
            row["student_id"]: dict(row)
            for row in attendance_model.get_attendance_by_session(session_id)
        }

        result: list[dict] = []
        for student in enrolled:
            att = attendance_map.get(student["id"])
            result.append(
                {
                    "student_id": student["id"],
                    "first_name": student["first_name"],
                    "last_name":  student["last_name"],
                    "card_id":    student["card_id"],
                    "status":     att["status"] if att else "Not Recorded",
                    "method":     att["method"] if att else "",
                }
            )
        return result

    except sqlite3.Error as exc:
        log_error(f"DB error in get_live_attendance: {exc}")
        return []

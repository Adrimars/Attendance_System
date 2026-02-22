"""
attendance_controller.py — Business logic for processing RFID card taps.

The controller is the only consumer of attendance_model and student_model
for tap-processing.  Views call process_card_tap() and act on the returned
TapResult.
"""

from __future__ import annotations

import csv
import sqlite3
from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum, auto
from pathlib import Path
from typing import Optional

import models.attendance_model as attendance_model
import models.student_model as student_model
import models.section_model as section_model
import models.session_model as session_model
from utils.logger import log_info, log_error, log_warning

# ── Locale-independent weekday helper ─────────────────────────────────────────
_ENGLISH_DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday',
                 'Friday', 'Saturday', 'Sunday']
_ENGLISH_MONTHS = ['January', 'February', 'March', 'April', 'May', 'June',
                   'July', 'August', 'September', 'October', 'November', 'December']


def _english_weekday(dt: datetime) -> str:
    """Return English weekday name regardless of OS locale."""
    return _ENGLISH_DAYS[dt.weekday()]


def _english_month(dt: datetime) -> str:
    """Return English month name regardless of OS locale."""
    return _ENGLISH_MONTHS[dt.month - 1]


class TapResultType(Enum):
    """Describes the outcome of a card tap so the view can display the right feedback."""
    KNOWN_PRESENT   = auto()   # Known student → marked Present (Green flash)
    UNKNOWN_CARD    = auto()   # Card not in DB → registration required (Red flash)
    DUPLICATE_TAP   = auto()   # Student already marked in this session (Yellow flash)
    NO_SESSION      = auto()   # No active session — tap ignored
    NO_SECTIONS     = auto()   # Known student but zero sections enrolled → assign dialog
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
    sections_marked: list = field(default_factory=list)    # names of newly-marked sections
    sections_duplicate: list = field(default_factory=list) # names of already-marked sections
    message: str = ""
    is_inactive: bool = False    # True if student is currently flagged inactive
    attended: int = 0            # Total 'Present' records across all enrolled sessions
    total_sessions: int = 0      # Total sessions across all enrolled sections


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
        is_inactive: bool = bool(student["is_inactive"])

        # Attendance summary for the banner (fetched before the current tap is applied)
        attended, total_sessions = attendance_model.get_student_attendance_summary(student_id)

        # ── Check if student has ANY sections enrolled at all ─────────────────────
        all_enrolled = student_model.get_sections_for_student(student_id)
        if not all_enrolled:
            log_info(
                f"Passive tap — no sections: student_id={student_id} "
                f"({first_name} {last_name})"
            )
            return PassiveTapResult(
                result_type=TapResultType.NO_SECTIONS,
                card_id=card_id,
                student_id=student_id,
                first_name=first_name,
                last_name=last_name,
                is_inactive=is_inactive,
                attended=attended,
                total_sessions=total_sessions,
                message=(
                    f"{first_name} {last_name} has no sections assigned. "
                    "Please select their sections."
                ),
            )

        today_date: str = date.today().isoformat()           # 'YYYY-MM-DD'
        today_day: str  = _english_weekday(datetime.now())   # 'Monday' … 'Sunday'

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
                is_inactive=is_inactive,
                attended=attended,
                total_sessions=total_sessions,
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
            # Re-fetch summary AFTER marking so the count reflects this tap
            attended_now, total_now = attendance_model.get_student_attendance_summary(student_id)
            message = (
                f"{first_name} {last_name} — present: {', '.join(newly_marked)} "
                f"| {attended_now}/{total_now} sessions"
            )
            # Student just attended — re-evaluate inactive status (may become active again)
            _refresh_inactive_status_for(student_id)
            _refreshed = student_model.get_student_by_id(student_id)
            is_inactive = bool(_refreshed["is_inactive"]) if _refreshed is not None else False
        else:
            log_info(
                f"Passive tap duplicate: student_id={student_id} "
                f"all sections already marked={already_marked}"
            )
            result_type = TapResultType.DUPLICATE_TAP
            attended_now, total_now = attended, total_sessions
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
            is_inactive=is_inactive,
            attended=attended_now,
            total_sessions=total_now,
            message=message,
        )

    except sqlite3.Error as exc:
        log_error(f"DB error in process_rfid_passive: {exc}")
        return PassiveTapResult(
            result_type=TapResultType.ERROR,
            card_id=card_id,
            message="A database error occurred. Please check the logs.",
        )


def mark_present_for_enrolled_sections(
    student_id: int,
    section_ids: list[int],
) -> list[str]:
    """
    Called right after new-student registration to mark the student Present
    in every section they just enrolled in (for today's date).

    A session is auto-created for each section if one does not yet exist.
    Sections where the student is already marked are silently skipped.

    Args:
        student_id:  The newly created student id.
        section_ids: The section ids the student was enrolled in.

    Returns:
        List of section ids (as strings) that were successfully marked Present.
    """
    today = date.today().isoformat()
    marked: list[str] = []
    for sec_id in section_ids:
        try:
            session_id = session_model.get_or_create_session(sec_id, today)
            if not attendance_model.is_duplicate_tap(session_id, student_id):
                attendance_model.mark_present(session_id, student_id, method="RFID")
                marked.append(str(sec_id))
                log_info(
                    f"Post-registration mark-present: student={student_id} "
                    f"section={sec_id} session={session_id}"
                )
        except sqlite3.Error as exc:
            log_error(
                f"DB error marking post-registration attendance: "
                f"student={student_id} section={sec_id} — {exc}"
            )
    return marked


# ── Inactive-student helpers ──────────────────────────────────────────────────

def _refresh_inactive_status_for(student_id: int) -> None:
    """
    Re-evaluate a single student's inactive flag based on their consecutive
    absences versus the ``inactive_threshold`` setting.
    Call this after any attendance change that could affect the student.
    """
    import models.settings_model as _sm
    threshold = int(_sm.get_setting("inactive_threshold") or 3)
    consec = attendance_model.get_consecutive_recent_absences(student_id)
    should_be_inactive = consec >= threshold
    current = student_model.get_student_by_id(student_id)
    if current is not None and bool(current["is_inactive"]) != should_be_inactive:
        student_model.set_inactive_status(student_id, should_be_inactive)
        log_info(
            f"Student id={student_id} marked "
            f"{'inactive' if should_be_inactive else 'active'} "
            f"(consecutive absences: {consec}, threshold: {threshold})"
        )


def refresh_inactive_status_all() -> tuple[int, int]:
    """
    Recompute the inactive flag for every student and persist any changes.

    Returns:
        (newly_inactive_count, newly_active_count) — number of status changes made.
    """
    import models.settings_model as _sm
    threshold = int(_sm.get_setting("inactive_threshold") or 3)
    students = student_model.get_all_students()
    became_inactive = 0
    became_active = 0
    for stu in students:
        sid = stu["id"]
        consec = attendance_model.get_consecutive_recent_absences(sid)
        should = consec >= threshold
        currently = bool(stu["is_inactive"])
        if currently != should:
            student_model.set_inactive_status(sid, should)
            if should:
                became_inactive += 1
            else:
                became_active += 1
    log_info(
        f"refresh_inactive_status_all: +{became_inactive} inactive, "
        f"+{became_active} re-activated (threshold={threshold})"
    )
    return became_inactive, became_active


def get_daily_report(date_str: str) -> dict:
    """
    Build a summary dict for the given date.

    Inactive students are excluded from all totals.

    Returns a dict with:
        date          — the date string
        total_active  — distinct active students enrolled in any section today
        present_count — of those, how many were marked Present in at least one section
        absent_count  — total_active - present_count
        sections      — list of dicts {name, present, absent, total}
    """
    from models.database import get_connection as _gc
    try:
        today_day = _english_weekday(datetime.strptime(date_str, "%Y-%m-%d"))
    except ValueError:
        today_day = ""

    with _gc() as conn:
        # Active students enrolled in sections whose day matches today
        enrolled_rows = conn.execute(
            """
            SELECT DISTINCT s.id,
                            sec.id   AS sec_id,
                            sec.name AS sec_name
            FROM   students s
            JOIN   student_sections ss ON ss.student_id  = s.id
            JOIN   sections         sec ON sec.id         = ss.section_id
            WHERE  sec.day      = ?
              AND  s.is_inactive = 0;
            """,
            (today_day,),
        ).fetchall()

        # Present records today (any section)
        present_rows = conn.execute(
            """
            SELECT DISTINCT a.student_id,
                            sec.id AS sec_id
            FROM   attendance a
            JOIN   sessions sess ON sess.id   = a.session_id
            JOIN   sections sec  ON sec.id    = sess.section_id
            WHERE  sess.date  = ?
              AND  a.status   = 'Present';
            """,
            (date_str,),
        ).fetchall()

    present_set: set[tuple[int, int]] = {
        (r["student_id"], r["sec_id"]) for r in present_rows
    }

    sec_data: dict[int, dict] = {}
    total_active_students: set[int] = set()
    present_students: set[int] = set()

    for row in enrolled_rows:
        sid    = row["id"]
        sec_id = row["sec_id"]
        total_active_students.add(sid)
        if sec_id not in sec_data:
            sec_data[sec_id] = {
                "name": row["sec_name"],
                "present": 0,
                "absent": 0,
                "total": 0,
            }
        sec_data[sec_id]["total"] += 1
        if (sid, sec_id) in present_set:
            present_students.add(sid)
            sec_data[sec_id]["present"] += 1
        else:
            sec_data[sec_id]["absent"] += 1

    total   = len(total_active_students)
    present = len(present_students)
    return {
        "date":          date_str,
        "total_active":  total,
        "present_count": present,
        "absent_count":  total - present,
        "sections":      list(sec_data.values()),
    }


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


# ── C1 MVC pass-through ────────────────────────────────────────────────────────

def get_today_log() -> list[dict]:
    """Return today's attendance records with student and section details.

    This is the single authorised entry point for the view layer to fetch
    today's log.  Routing the call through the controller means any future
    caching, filtering, or logging added here is automatically applied to
    all consumers.

    Returns:
        A list of dicts as produced by
        ``attendance_model.get_today_attendance_with_details()``.
    """
    return attendance_model.get_today_attendance_with_details(
        date.today().isoformat()
    )


# ── CSV Export ─────────────────────────────────────────────────────────────────

_CSV_FIELDS = ["date", "first_name", "last_name", "section_name",
               "status", "method", "timestamp"]


def _write_attendance_csv(records: list[dict], filepath: str) -> None:
    """Write a list of attendance record dicts to a UTF-8 BOM CSV file.

    The BOM ensures Excel on Windows opens the file with the correct encoding.
    """
    with open(filepath, "w", newline="", encoding="utf-8-sig") as fh:
        writer = csv.DictWriter(fh, fieldnames=_CSV_FIELDS, extrasaction="ignore")
        writer.writeheader()
        for rec in records:
            ts = rec.get("timestamp", "")
            # Extract the date portion from the ISO-8601 timestamp
            try:
                date_part = datetime.fromisoformat(ts).date().isoformat()
            except Exception:
                date_part = rec.get("date", "")
            writer.writerow({
                "date":         date_part,
                "first_name":   rec.get("first_name", ""),
                "last_name":    rec.get("last_name", ""),
                "section_name": rec.get("section_name", ""),
                "status":       rec.get("status", ""),
                "method":       rec.get("method", ""),
                "timestamp":    ts,
            })


def export_today_to_csv(filepath: str) -> tuple[bool, str]:
    """Export today's attendance records to a CSV file.

    Args:
        filepath: Absolute path (including filename) for the output file.

    Returns:
        (True, filepath)     on success.
        (False, error_msg)   on failure.
    """
    try:
        records = get_today_log()
        _write_attendance_csv(records, filepath)
        log_info(f"Exported today's attendance to CSV: {filepath} ({len(records)} rows)")
        return True, filepath
    except Exception as exc:
        log_error(f"CSV export (today) failed: {exc}")
        return False, str(exc)


def export_all_to_csv(filepath: str) -> tuple[bool, str]:
    """Export every attendance record in the database to a CSV file.

    Args:
        filepath: Absolute path (including filename) for the output file.

    Returns:
        (True, filepath)     on success.
        (False, error_msg)   on failure.
    """
    try:
        records = attendance_model.get_all_attendance_with_details()
        _write_attendance_csv(records, filepath)
        log_info(f"Exported all attendance to CSV: {filepath} ({len(records)} rows)")
        return True, filepath
    except Exception as exc:
        log_error(f"CSV export (all) failed: {exc}")
        return False, str(exc)


# ── PDF export helpers ────────────────────────────────────────────────────────

def _write_attendance_pdf(
    records: list[dict],
    filepath: str,
    title: str = "Attendance Report",
) -> None:
    """Render *records* as a styled PDF table using ReportLab.

    Columns: Date | First Name | Last Name | Section | Status | Method
    Each row is colour-coded by status (green = Present, red = Absent).

    Args:
        records:  List of dicts as returned by the attendance model helpers.
        filepath: Destination file path (must end with .pdf).
        title:    Heading text shown at the top of the document.
    """
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.enums import TA_CENTER

    doc = SimpleDocTemplate(
        filepath,
        pagesize=landscape(A4),
        leftMargin=1.5 * cm,
        rightMargin=1.5 * cm,
        topMargin=1.5 * cm,
        bottomMargin=1.5 * cm,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "ReportTitle",
        parent=styles["Title"],
        fontSize=18,
        spaceAfter=4,
        textColor=colors.HexColor("#1e3a5f"),
        alignment=TA_CENTER,
    )
    sub_style = ParagraphStyle(
        "ReportSub",
        parent=styles["Normal"],
        fontSize=9,
        textColor=colors.HexColor("#6b7280"),
        alignment=TA_CENTER,
        spaceAfter=12,
    )

    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    present_count = sum(1 for r in records if r.get("status") == "Present")
    absent_count  = len(records) - present_count

    story = [
        Paragraph(title, title_style),
        Paragraph(
            f"Generated: {generated_at} &nbsp;&nbsp;|&nbsp;&nbsp; "
            f"Total: {len(records)} &nbsp;&nbsp;|&nbsp;&nbsp; "
            f"Present: {present_count} &nbsp;&nbsp;|&nbsp;&nbsp; "
            f"Absent: {absent_count}",
            sub_style,
        ),
        Spacer(1, 0.2 * cm),
    ]

    # ── Build table data ───────────────────────────────────────────────────────
    headers = ["#", "Date", "First Name", "Last Name", "Section", "Status", "Method"]
    col_widths = [1.0 * cm, 2.6 * cm, 3.8 * cm, 3.8 * cm, 4.5 * cm, 2.4 * cm, 2.6 * cm]

    table_data = [headers]
    row_colors: list[tuple[int, colors.Color]] = []  # (row_index, fill_color)

    STATUS_PRESENT_BG = colors.HexColor("#dcfce7")
    STATUS_ABSENT_BG  = colors.HexColor("#fee2e2")

    for i, rec in enumerate(records, start=1):
        ts = rec.get("timestamp", "")
        try:
            date_part = datetime.fromisoformat(ts).date().isoformat()
        except Exception:
            date_part = rec.get("date", "")

        status = rec.get("status", "")
        table_data.append([
            str(i),
            date_part,
            rec.get("first_name", ""),
            rec.get("last_name", ""),
            rec.get("section_name", ""),
            status,
            rec.get("method", ""),
        ])
        # +1 because row 0 is the header
        bg = STATUS_PRESENT_BG if status == "Present" else STATUS_ABSENT_BG
        row_colors.append((i, bg))

    tbl = Table(table_data, colWidths=col_widths, repeatRows=1)

    # ── Base style ─────────────────────────────────────────────────────────────
    style_cmds = [
        # Header
        ("BACKGROUND",  (0, 0), (-1, 0), colors.HexColor("#1e3a5f")),
        ("TEXTCOLOR",   (0, 0), (-1, 0), colors.white),
        ("FONTNAME",    (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",    (0, 0), (-1, 0), 10),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
        ("TOPPADDING",  (0, 0), (-1, 0), 8),
        # Body
        ("FONTNAME",    (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE",    (0, 1), (-1, -1), 9),
        ("TOPPADDING",  (0, 1), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 1), (-1, -1), 5),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f9fafb")]),
        # Grid
        ("GRID",        (0, 0), (-1, -1), 0.4, colors.HexColor("#d1d5db")),
        ("VALIGN",      (0, 0), (-1, -1), "MIDDLE"),
        # Align # column centre
        ("ALIGN",       (0, 0), (0, -1), "CENTER"),
    ]
    # Per-row status colours (override ROWBACKGROUNDS)
    for row_idx, bg in row_colors:
        style_cmds.append(("BACKGROUND", (0, row_idx), (-1, row_idx), bg))

    tbl.setStyle(TableStyle(style_cmds))
    story.append(tbl)

    doc.build(story)


def export_today_to_pdf(filepath: str) -> tuple[bool, str]:
    """Export today's attendance records to a PDF file.

    Args:
        filepath: Absolute path (including filename) for the output .pdf file.

    Returns:
        (True, filepath)   on success.
        (False, error_msg) on failure.
    """
    try:
        records = get_today_log()
        _write_attendance_pdf(
            records,
            filepath,
            title=f"Today's Attendance Report — {date.today().isoformat()}",
        )
        log_info(f"Exported today's attendance to PDF: {filepath} ({len(records)} rows)")
        return True, filepath
    except Exception as exc:
        log_error(f"PDF export (today) failed: {exc}")
        return False, str(exc)


def export_all_to_pdf(filepath: str) -> tuple[bool, str]:
    """Export every attendance record in the database to a PDF file.

    Args:
        filepath: Absolute path (including filename) for the output .pdf file.

    Returns:
        (True, filepath)   on success.
        (False, error_msg) on failure.
    """
    try:
        records = attendance_model.get_all_attendance_with_details()
        _write_attendance_pdf(
            records,
            filepath,
            title="Full Attendance Report",
        )
        log_info(f"Exported all attendance to PDF: {filepath} ({len(records)} rows)")
        return True, filepath
    except Exception as exc:
        log_error(f"PDF export (all) failed: {exc}")
        return False, str(exc)


# ─────────────────────────────────────────────────────────────────────────────

def export_to_google_sheets(
    spreadsheet_url: str,
    worksheet_title: str = "Attendance Export",
) -> tuple[bool, str]:
    """Export all attendance records to a Google Sheet.

    The function appends all rows to a worksheet named *worksheet_title*
    inside the spreadsheet identified by *spreadsheet_url*.  If the
    worksheet does not yet exist it is created.  Existing content is
    **replaced** (worksheet is cleared before writing).

    Credentials are read from the ``google_credentials_path`` setting.

    Args:
        spreadsheet_url:  Full URL or spreadsheet-key string.
        worksheet_title:  Name of the target worksheet tab.

    Returns:
        (True, info_msg)    on success.
        (False, error_msg)  on failure.
    """
    try:
        import gspread  # type: ignore[import]
        from google.oauth2.service_account import Credentials  # type: ignore[import]
    except ImportError as exc:
        return False, f"gspread / google-auth not installed: {exc}"

    import models.settings_model as settings_model
    creds_path = settings_model.get_setting("google_credentials_path") or ""
    if not creds_path or not Path(creds_path).is_file():
        return (
            False,
            "Google credentials file not configured.\n"
            "Set the path in Settings → Google Credentials.",
        )

    try:
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
        ]
        creds = Credentials.from_service_account_file(creds_path, scopes=scopes)
        gc = gspread.authorize(creds)
        sh = gc.open_by_url(spreadsheet_url)
    except gspread.exceptions.APIError as exc:
        log_error(f"Google Sheets API error during export: {exc}")
        return False, f"Google Sheets API error:\n{exc}"
    except Exception as exc:
        log_error(f"Failed to open spreadsheet: {exc}")
        return False, f"Could not open spreadsheet:\n{exc}"

    try:
        try:
            ws = sh.worksheet(worksheet_title)
            ws.clear()
        except gspread.exceptions.WorksheetNotFound:
            ws = sh.add_worksheet(title=worksheet_title, rows=1000, cols=20)

        records = attendance_model.get_all_attendance_with_details()
        header = ["Date", "First Name", "Last Name", "Section", "Status", "Method", "Timestamp"]
        rows_out = [header]
        for rec in records:
            ts = rec.get("timestamp", "")
            try:
                date_part = datetime.fromisoformat(ts).date().isoformat()
            except Exception:
                date_part = rec.get("date", "")
            rows_out.append([
                date_part,
                rec.get("first_name", ""),
                rec.get("last_name", ""),
                rec.get("section_name", ""),
                rec.get("status", ""),
                rec.get("method", ""),
                ts,
            ])

        ws.update(rows_out)
        info = (
            f"Exported {len(records)} records to "
            f"'{worksheet_title}' in the sheet."
        )
        log_info(f"Google Sheets export: {info}")
        return True, info
    except gspread.exceptions.APIError as exc:
        log_error(f"Google Sheets write error: {exc}")
        return False, f"Google Sheets write error:\n{exc}"
    except Exception as exc:
        log_error(f"Unexpected error during Sheets export: {exc}")
        return False, str(exc)


def push_summary_to_sheets(spreadsheet_url: str) -> tuple[bool, str]:
    """
    Push a per-student attendance summary (attended/total format) to a dedicated
    'Attendance Summary' worksheet in the given Google Spreadsheet.

    The worksheet is created if it does not already exist, and its contents are
    **replaced** on every call.

    Credentials are read from the ``google_credentials_path`` setting.

    Args:
        spreadsheet_url: Full URL of the Google Spreadsheet.

    Returns:
        (True, info_msg)    on success.
        (False, error_msg)  on failure.
    """
    try:
        import gspread  # type: ignore[import]
        from google.oauth2.service_account import Credentials  # type: ignore[import]
    except ImportError as exc:
        return False, f"gspread / google-auth not installed: {exc}"

    import models.settings_model as settings_model

    creds_path = settings_model.get_setting("google_credentials_path") or ""
    if not creds_path or not Path(creds_path).is_file():
        return False, "Credentials not configured"

    try:
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
        ]
        creds = Credentials.from_service_account_file(creds_path, scopes=scopes)
        gc = gspread.authorize(creds)
        sh = gc.open_by_url(spreadsheet_url)
    except Exception as exc:
        log_error(f"push_summary_to_sheets: failed to open spreadsheet: {exc}")
        return False, str(exc)

    try:
        try:
            ws = sh.worksheet("Attendance Summary")
        except gspread.exceptions.WorksheetNotFound:
            ws = sh.add_worksheet(title="Attendance Summary", rows=1000, cols=10)

        ws.clear()

        data = attendance_model.get_total_attendance_per_student()
        header = ["First Name", "Last Name", "Card ID", "Total Attendance"]
        rows_out = [header]
        for student in data:
            rows_out.append(
                [
                    student.get("first_name", ""),
                    student.get("last_name", ""),
                    student.get("card_id") or "",
                    student.get("summary", "0/0"),
                ]
            )

        ws.update(rows_out, "A1")
        info = f"Pushed {len(data)} students to Attendance Summary"
        log_info(f"push_summary_to_sheets: {info}")
        return True, info
    except Exception as exc:
        log_error(f"push_summary_to_sheets: {exc}")
        return False, str(exc)

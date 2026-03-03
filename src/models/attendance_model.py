"""
attendance_model.py — Data-access layer for the attendance table.
"""

import sqlite3
from datetime import datetime, timezone
from typing import Optional

from models.database import get_connection
from utils.logger import log_debug

AttendanceRow = sqlite3.Row


def mark_present(
    session_id: int,
    student_id: int,
    method: str = "RFID",
) -> int:
    """
    Insert an attendance record with status 'Present'.

    Args:
        session_id: FK reference to sessions.id.
        student_id: FK reference to students.id.
        method:     'RFID' or 'Manual'.

    Returns:
        The id of the new attendance record.

    Raises:
        sqlite3.IntegrityError: If a record for (session_id, student_id) already exists.
    """
    timestamp = datetime.now(timezone.utc).isoformat()
    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO attendance (session_id, student_id, status, method, timestamp)
            VALUES (?, ?, 'Present', ?, ?);
            """,
            (session_id, student_id, method, timestamp),
        )
        new_id = cursor.lastrowid
    log_debug(
        f"Marked present: session={session_id} student={student_id} method={method}"
    )
    return new_id  # type: ignore[return-value]


def mark_absent(
    session_id: int,
    student_id: int,
    method: str = "Manual",
) -> int:
    """
    Insert an attendance record with status 'Absent'.

    Returns:
        The id of the new attendance record.
    """
    timestamp = datetime.now(timezone.utc).isoformat()
    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO attendance (session_id, student_id, status, method, timestamp)
            VALUES (?, ?, 'Absent', ?, ?);
            """,
            (session_id, student_id, method, timestamp),
        )
        new_id = cursor.lastrowid
    log_debug(
        f"Marked absent: session={session_id} student={student_id} method={method}"
    )
    return new_id  # type: ignore[return-value]


def toggle_status(session_id: int, student_id: int) -> str:
    """
    Toggle a student's attendance status between Present and Absent.
    Sets method to 'Manual' on every toggle (as required by the spec).

    Returns:
        The new status string ('Present' or 'Absent').

    Raises:
        ValueError: If no attendance record exists for (session_id, student_id).
    """
    timestamp = datetime.now(timezone.utc).isoformat()
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT status FROM attendance
            WHERE session_id = ? AND student_id = ?;
            """,
            (session_id, student_id),
        ).fetchone()

        if row is None:
            raise ValueError(
                f"No attendance record for session={session_id} student={student_id}"
            )

        new_status = "Absent" if row["status"] == "Present" else "Present"
        conn.execute(
            """
            UPDATE attendance
            SET status = ?, method = 'Manual', timestamp = ?
            WHERE session_id = ? AND student_id = ?;
            """,
            (new_status, timestamp, session_id, student_id),
        )
    log_debug(
        f"Toggled attendance: session={session_id} student={student_id} → {new_status}"
    )
    return new_status


def get_attendance_by_session(session_id: int) -> list[AttendanceRow]:
    """
    Return all attendance records for a session, joined with student names.

    Each returned row has:
        id, session_id, student_id, status, method, timestamp,
        first_name, last_name, card_id
    """
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT
                a.id, a.session_id, a.student_id,
                a.status, a.method, a.timestamp,
                s.first_name, s.last_name, s.card_id
            FROM attendance a
            JOIN students s ON s.id = a.student_id
            WHERE a.session_id = ?
            ORDER BY s.last_name, s.first_name;
            """,
            (session_id,),
        ).fetchall()
    return rows


def get_attendance_record(
    session_id: int, student_id: int
) -> Optional[AttendanceRow]:
    """Return a single attendance record or None if it doesn't exist."""
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT * FROM attendance
            WHERE session_id = ? AND student_id = ?;
            """,
            (session_id, student_id),
        ).fetchone()
    return row


def is_duplicate_tap(session_id: int, student_id: int) -> bool:
    """Return True if the student already has an attendance record in this session."""
    return get_attendance_record(session_id, student_id) is not None


def get_today_attendance_with_details(today_date: str) -> list[dict]:
    """
    Return all attendance records for the given date, enriched with student
    and section information.

    If duplicate sessions exist for the same section+date, only the latest
    attendance record (by timestamp) per student+section is returned so
    each student appears at most once per section.

    Args:
        today_date: ISO-8601 date string, e.g. '2026-02-20'.

    Returns:
        List of dicts with keys:
            id, status, method, timestamp,
            first_name, last_name, card_id,
            section_name
        Ordered newest-first.
    """
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT a.id,
                   a.status,
                   a.method,
                   a.timestamp,
                   st.first_name,
                   st.last_name,
                   st.card_id,
                   sec.name AS section_name,
                   a.student_id,
                   sec.id   AS section_id
            FROM   attendance a
            JOIN   sessions   ses ON ses.id        = a.session_id
            JOIN   sections   sec ON sec.id        = ses.section_id
            JOIN   students   st  ON st.id         = a.student_id
            WHERE  ses.date = ?
            ORDER  BY a.timestamp DESC;
            """,
            (today_date,),
        ).fetchall()

    # Deduplicate: keep only the first (latest by timestamp) per student+section
    seen: set[tuple[int, int]] = set()
    result: list[dict] = []
    for r in rows:
        key = (r["student_id"], r["section_id"])
        if key in seen:
            continue
        seen.add(key)
        result.append(dict(r))
    return result


def get_all_attendance_with_details() -> list[dict]:
    """
    Return every attendance record in the database, enriched with student,
    session date, and section information.

    If duplicate sessions exist for the same section+date, only the latest
    attendance record (by timestamp) per student+section+date is returned.

    Returns:
        List of dicts with keys:
            id, status, method, timestamp,
            first_name, last_name, card_id,
            section_name, date
        Ordered newest-first.
    """
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT a.id,
                   a.status,
                   a.method,
                   a.timestamp,
                   st.first_name,
                   st.last_name,
                   st.card_id,
                   sec.name AS section_name,
                   ses.date,
                   a.student_id,
                   sec.id   AS section_id
            FROM   attendance a
            JOIN   sessions   ses ON ses.id  = a.session_id
            JOIN   sections   sec ON sec.id  = ses.section_id
            JOIN   students   st  ON st.id   = a.student_id
            ORDER  BY a.timestamp DESC;
            """,
        ).fetchall()

    # Deduplicate: keep only the latest record per student+section+date
    seen: set[tuple[int, int, str]] = set()
    result: list[dict] = []
    for r in rows:
        key = (r["student_id"], r["section_id"], r["date"])
        if key in seen:
            continue
        seen.add(key)
        result.append(dict(r))
    return result


def get_total_attendance_per_student() -> list[dict]:
    """
    Return one record per student showing how many sessions they attended
    versus the total number of sessions for sections they are enrolled in.

    Returns:
        List of dicts with keys:
            first_name, last_name, card_id,
            attended       — count of 'Present' records for that student,
            total_sessions — count of distinct sessions in enrolled sections,
            summary        — formatted string "<attended>/<total_sessions>"
        Ordered by last_name, first_name.
        Students with no card_id (NULL) are included.
        If a student is enrolled in multiple sections, counts are summed
        across all sections.
    """
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT s.id,
                   s.first_name,
                   s.last_name,
                   s.card_id,
                   COUNT(DISTINCT CASE WHEN a.status = 'Present'
                         THEN sess.section_id || '|' || sess.date END) AS attended,
                   COUNT(DISTINCT CASE WHEN sess.date IS NOT NULL
                         THEN sess.section_id || '|' || sess.date END) AS total_sessions
            FROM   students         s
            LEFT JOIN student_sections ss   ON ss.student_id   = s.id
            LEFT JOIN sessions         sess ON sess.section_id = ss.section_id
            LEFT JOIN attendance       a    ON a.student_id    = s.id
                                           AND a.session_id    = sess.id
            GROUP  BY s.id
            ORDER  BY s.last_name, s.first_name;
            """,
        ).fetchall()

    result: list[dict] = []
    for row in rows:
        attended = row["attended"] or 0
        total = row["total_sessions"] or 0
        result.append(
            {
                "id":           row["id"],
                "first_name":   row["first_name"],
                "last_name":    row["last_name"],
                "card_id":      row["card_id"],
                "attended":     attended,
                "total_sessions": total,
                "summary":      f"{attended}/{total}",
            }
        )
    return result


def get_per_section_attendance_per_student() -> list[dict]:
    """
    Return per-student, per-section attendance breakdown.

    Each row represents one student–section combination with:
        student_id, first_name, last_name, card_id,
        section_id, section_name, section_day, section_time,
        attended       — count of 'Present' records for the student in that section,
        total_sessions — count of distinct sessions for that section,
        summary        — formatted "<attended>/<total_sessions>"

    Ordered by student last_name, first_name, then section name.
    """
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT s.id             AS student_id,
                   s.first_name,
                   s.last_name,
                   s.card_id,
                   sec.id           AS section_id,
                   sec.name         AS section_name,
                   sec.day          AS section_day,
                   sec.time         AS section_time,
                   COUNT(DISTINCT CASE WHEN a.status = 'Present'
                         THEN sess.date END)                         AS attended,
                   COUNT(DISTINCT sess.date)                         AS total_sessions
            FROM   students          s
            JOIN   student_sections   ss   ON ss.student_id   = s.id
            JOIN   sections           sec  ON sec.id          = ss.section_id
            LEFT JOIN sessions        sess ON sess.section_id = sec.id
            LEFT JOIN attendance      a    ON a.student_id    = s.id
                                          AND a.session_id    = sess.id
            GROUP  BY s.id, sec.id
            ORDER  BY s.last_name, s.first_name, sec.name;
            """,
        ).fetchall()

    result: list[dict] = []
    for row in rows:
        attended = row["attended"] or 0
        total = row["total_sessions"] or 0
        result.append({
            "student_id":    row["student_id"],
            "first_name":    row["first_name"],
            "last_name":     row["last_name"],
            "card_id":       row["card_id"],
            "section_id":    row["section_id"],
            "section_name":  row["section_name"],
            "section_day":   row["section_day"],
            "section_time":  row["section_time"],
            "attended":      attended,
            "total_sessions": total,
            "summary":       f"{attended}/{total}",
        })
    return result


def get_student_attendance_summary(student_id: int) -> tuple[int, int]:
    """
    Return (attended, total_sessions) for a single student.

    attended       — COUNT of 'Present' records for that student.
    total_sessions — COUNT of distinct sessions across all enrolled sections.
    """
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT
                COUNT(DISTINCT CASE WHEN a.status = 'Present'
                      THEN ss.section_id || '|' || sess.date END) AS attended,
                COUNT(DISTINCT CASE WHEN sess.date IS NOT NULL
                      THEN ss.section_id || '|' || sess.date END) AS total_sessions
            FROM   student_sections ss
            LEFT JOIN sessions     sess ON sess.section_id = ss.section_id
            LEFT JOIN attendance   a    ON a.student_id    = ?
                                       AND a.session_id    = sess.id
            WHERE  ss.student_id = ?;
            """,
            (student_id, student_id),
        ).fetchone()
    if row is None:
        return 0, 0
    return (row["attended"] or 0), (row["total_sessions"] or 0)


def get_section_attendance_on_date(section_id: int, date_str: str) -> list[dict]:
    """
    Return attendance data for every enrolled student in a given section on a
    specific date.

    For each enrolled student, includes their *final* attendance status on that
    date (Present, Absent, or None if no session/record exists).  If multiple
    sessions exist for the same section+date (legacy data), the most-recent
    attendance record (by timestamp) is used so each student appears only once.

    Returns:
        List of dicts with keys:
            student_id, first_name, last_name, card_id, status, method, timestamp
    """
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT st.id          AS student_id,
                   st.first_name,
                   st.last_name,
                   st.card_id,
                   a.status,
                   a.method,
                   a.timestamp
            FROM   students st
            JOIN   student_sections ss ON ss.student_id = st.id
            LEFT JOIN sessions sess   ON sess.section_id = ss.section_id
                                      AND sess.date = ?
            LEFT JOIN attendance a    ON a.session_id = sess.id
                                      AND a.student_id = st.id
            WHERE  ss.section_id = ?
            ORDER  BY st.last_name, st.first_name, a.timestamp DESC;
            """,
            (date_str, section_id),
        ).fetchall()

    # Deduplicate: keep only the first (latest by timestamp) row per student
    seen: set[int] = set()
    result: list[dict] = []
    for r in rows:
        sid = r["student_id"]
        if sid in seen:
            continue
        seen.add(sid)
        result.append(dict(r))
    return result


def get_full_section_attendance(section_id: int) -> list[dict]:
    """
    Return comprehensive attendance data for all students enrolled in a section
    across ALL dates/sessions ever recorded for that section.

    If duplicate sessions exist for the same section+date, only the latest
    attendance record (by timestamp) per student per date is kept.

    Returns:
        List of dicts with keys:
            student_id, first_name, last_name, card_id,
            session_date, status, method, timestamp
        Ordered by student name, then session date descending.
    """
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT st.id          AS student_id,
                   st.first_name,
                   st.last_name,
                   st.card_id,
                   sess.date      AS session_date,
                   a.status,
                   a.method,
                   a.timestamp
            FROM   students st
            JOIN   student_sections ss ON ss.student_id = st.id
            LEFT JOIN sessions sess   ON sess.section_id = ss.section_id
            LEFT JOIN attendance a    ON a.session_id = sess.id
                                      AND a.student_id = st.id
            WHERE  ss.section_id = ?
            ORDER  BY st.last_name, st.first_name, sess.date DESC, a.timestamp DESC;
            """,
            (section_id,),
        ).fetchall()

    # Deduplicate: keep only the first (latest by timestamp) row per (student, date)
    seen: set[tuple[int, str | None]] = set()
    result: list[dict] = []
    for r in rows:
        key = (r["student_id"], r["session_date"])
        if key in seen:
            continue
        seen.add(key)
        result.append(dict(r))
    return result


def get_section_session_dates(section_id: int) -> list[str]:
    """Return all distinct session dates for a given section, newest first."""
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT DISTINCT date
            FROM   sessions
            WHERE  section_id = ?
            ORDER  BY date DESC;
            """,
            (section_id,),
        ).fetchall()
    return [r["date"] for r in rows]


def get_consecutive_recent_absences(student_id: int) -> int:
    """
    Count how many of the most-recent sessions (across all enrolled sections)
    a student was absent from (status != 'Present' or no record at all).

    Counts backwards from the newest session and stops the moment a 'Present'
    record is found, returning the number of consecutive non-present sessions.

    Duplicate sessions for the same section+date are collapsed so they count
    as one calendar event.

    Returns 0 if the student has no sessions or their last session was 'Present'.
    """
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT sess.section_id,
                   sess.date,
                   COALESCE(a.status, 'Absent') AS status,
                   a.timestamp
            FROM   student_sections ss
            JOIN   sessions         sess ON sess.section_id = ss.section_id
            LEFT JOIN attendance    a    ON a.session_id    = sess.id
                                        AND a.student_id    = ss.student_id
            WHERE  ss.student_id = ?
            ORDER  BY sess.date DESC, a.timestamp DESC;
            """,
            (student_id,),
        ).fetchall()

    # Deduplicate: keep only the latest record per (section, date)
    seen: set[tuple[int, str]] = set()
    deduped: list[dict] = []
    for row in rows:
        key = (row["section_id"], row["date"])
        if key in seen:
            continue
        seen.add(key)
        deduped.append({"status": row["status"], "date": row["date"]})

    # Sort newest-first by date (may have mixed sections)
    deduped.sort(key=lambda r: r["date"], reverse=True)

    count = 0
    for rec in deduped:
        if rec["status"] == "Present":
            break
        count += 1
    return count
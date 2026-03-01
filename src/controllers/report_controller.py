"""
report_controller.py — Business logic for the unified Report module.

Supports two modes:
  Mode A: Daily Section Report  — specific date + section
  Mode B: Full Section Report   — all dates for a section
"""

from __future__ import annotations

import io
import os
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional

import models.attendance_model as attendance_model
import models.section_model as section_model
from utils.logger import log_info, log_error


# ── Locale-independent weekday helper (shared with attendance_controller) ─────
_ENGLISH_DAYS = [
    "Monday", "Tuesday", "Wednesday", "Thursday",
    "Friday", "Saturday", "Sunday",
]


def _english_weekday_from_date(date_str: str) -> str:
    """Return English weekday name for an ISO date string 'YYYY-MM-DD'."""
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    return _ENGLISH_DAYS[dt.weekday()]


# ═══════════════════════════════════════════════════════════════════════════════
# Mode A — Daily Section Report
# ═══════════════════════════════════════════════════════════════════════════════


def get_daily_section_report(section_id: int, date_str: str) -> dict:
    """
    Build a detailed attendance report for one section on one date.

    Returns dict with:
        section_name, section_day, section_time,
        date, weekday,
        total_enrolled, present_count, absent_count, no_record_count,
        students: list of {student_id, first_name, last_name, card_id, status}
    """
    sec = section_model.get_section_by_id(section_id)
    if sec is None:
        raise ValueError(f"Section {section_id} not found.")

    weekday = _english_weekday_from_date(date_str)
    rows = attendance_model.get_section_attendance_on_date(section_id, date_str)

    present = sum(1 for r in rows if r["status"] == "Present")
    absent = sum(1 for r in rows if r["status"] == "Absent")
    no_record = sum(1 for r in rows if r["status"] is None)

    students = []
    for r in rows:
        students.append({
            "student_id": r["student_id"],
            "first_name": r["first_name"],
            "last_name": r["last_name"],
            "card_id": r["card_id"],
            "status": r["status"] or "No Record",
        })

    return {
        "section_name": sec["name"],
        "section_day": sec["day"],
        "section_time": sec["time"],
        "date": date_str,
        "weekday": weekday,
        "total_enrolled": len(rows),
        "present_count": present,
        "absent_count": absent,
        "no_record_count": no_record,
        "students": students,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Mode B — Full Section Report
# ═══════════════════════════════════════════════════════════════════════════════


def get_full_section_report(section_id: int) -> dict:
    """
    Build a comprehensive report for a section showing all students and all
    their attendance records across every session date.

    Returns dict with:
        section_name, section_day, section_time,
        session_dates: list of date strings (sorted newest-first),
        students: list of {
            student_id, first_name, last_name, card_id,
            total_present, total_absent, total_sessions,
            attendance_pct,
            records: {date_str: status_str}
        }
    """
    sec = section_model.get_section_by_id(section_id)
    if sec is None:
        raise ValueError(f"Section {section_id} not found.")

    session_dates = attendance_model.get_section_session_dates(section_id)
    raw_rows = attendance_model.get_full_section_attendance(section_id)

    # Group by student
    students_map: dict[int, dict] = {}
    for r in raw_rows:
        sid = r["student_id"]
        if sid not in students_map:
            students_map[sid] = {
                "student_id": sid,
                "first_name": r["first_name"],
                "last_name": r["last_name"],
                "card_id": r["card_id"],
                "records": {},
            }
        if r["session_date"] is not None:
            students_map[sid]["records"][r["session_date"]] = r["status"] or "No Record"

    # Compute summaries per student
    students = []
    for stu in students_map.values():
        total_present = sum(1 for s in stu["records"].values() if s == "Present")
        total_absent = sum(1 for s in stu["records"].values() if s == "Absent")
        total_sessions = len(session_dates)
        pct = f"{total_present / total_sessions * 100:.0f}%" if total_sessions > 0 else "N/A"
        stu["total_present"] = total_present
        stu["total_absent"] = total_absent
        stu["total_sessions"] = total_sessions
        stu["attendance_pct"] = pct
        students.append(stu)

    # Sort by last name, first name
    students.sort(key=lambda s: (s["last_name"].lower(), s["first_name"].lower()))

    return {
        "section_name": sec["name"],
        "section_day": sec["day"],
        "section_time": sec["time"],
        "session_dates": session_dates,
        "students": students,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# PDF Generation (Mode A — Daily Section Report)
# ═══════════════════════════════════════════════════════════════════════════════


def generate_daily_section_pdf(report: dict, output_path: str) -> str:
    """
    Generate a PDF from a Mode-A daily section report.

    Args:
        report: dict returned by get_daily_section_report().
        output_path: full file path for the PDF.

    Returns:
        The output_path on success.
    """
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.units import mm
    from reportlab.platypus import (
        SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer,
    )
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

    doc = SimpleDocTemplate(output_path, pagesize=A4,
                            leftMargin=20*mm, rightMargin=20*mm,
                            topMargin=20*mm, bottomMargin=20*mm)

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "ReportTitle", parent=styles["Title"],
        fontSize=18, spaceAfter=6,
    )
    subtitle_style = ParagraphStyle(
        "ReportSubtitle", parent=styles["Normal"],
        fontSize=11, textColor=colors.grey, spaceAfter=12,
    )
    heading_style = ParagraphStyle(
        "ReportHeading", parent=styles["Heading2"],
        fontSize=13, spaceAfter=8,
    )

    elements = []

    # Title
    elements.append(Paragraph(f"Daily Section Report", title_style))
    elements.append(Paragraph(
        f"Section: {report['section_name']}  |  "
        f"Date: {report['date']} ({report['weekday']})  |  "
        f"Schedule: {report['section_day']} {report['section_time']}",
        subtitle_style,
    ))
    elements.append(Spacer(1, 6*mm))

    # Summary
    total = report["total_enrolled"]
    present = report["present_count"]
    absent = report["absent_count"]
    no_rec = report["no_record_count"]
    pct = f"{present / total * 100:.0f}%" if total > 0 else "N/A"

    summary_data = [
        ["Total Enrolled", "Present", "Absent", "No Record", "Attendance Rate"],
        [str(total), str(present), str(absent), str(no_rec), pct],
    ]
    summary_table = Table(summary_data, colWidths=[90, 70, 70, 80, 100])
    summary_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e40af")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#f0f4ff")]),
    ]))
    elements.append(summary_table)
    elements.append(Spacer(1, 8*mm))

    # Student list
    elements.append(Paragraph("Student Details", heading_style))

    table_data = [["#", "Last Name", "First Name", "Card ID", "Status"]]
    for i, stu in enumerate(report["students"], 1):
        table_data.append([
            str(i),
            stu["last_name"],
            stu["first_name"],
            stu["card_id"] or "—",
            stu["status"],
        ])

    col_widths = [30, 120, 120, 100, 80]
    student_table = Table(table_data, colWidths=col_widths)
    student_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f4c75")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ALIGN", (0, 0), (0, -1), "CENTER"),
        ("ALIGN", (4, 0), (4, -1), "CENTER"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1),
         [colors.white, colors.HexColor("#f8f9fa")]),
    ]))

    # Colour-code status cells
    for i, stu in enumerate(report["students"], 1):
        if stu["status"] == "Present":
            student_table.setStyle(TableStyle([
                ("TEXTCOLOR", (4, i), (4, i), colors.HexColor("#166534")),
            ]))
        elif stu["status"] == "Absent":
            student_table.setStyle(TableStyle([
                ("TEXTCOLOR", (4, i), (4, i), colors.HexColor("#991b1b")),
            ]))

    elements.append(student_table)
    elements.append(Spacer(1, 10*mm))

    # Footer
    elements.append(Paragraph(
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        ParagraphStyle("Footer", parent=styles["Normal"],
                       fontSize=8, textColor=colors.grey),
    ))

    doc.build(elements)
    log_info(f"PDF generated: {output_path}")
    return output_path


# ═══════════════════════════════════════════════════════════════════════════════
# PDF Generation (Mode B — Full Section Report)
# ═══════════════════════════════════════════════════════════════════════════════


def generate_full_section_pdf(report: dict, output_path: str) -> str:
    """
    Generate a PDF from a Mode-B full section report.

    Args:
        report: dict returned by get_full_section_report().
        output_path: full file path for the PDF.

    Returns:
        The output_path on success.
    """
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib import colors
    from reportlab.lib.units import mm
    from reportlab.platypus import (
        SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak,
    )
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

    # Use landscape for the potentially wide date-column table
    doc = SimpleDocTemplate(output_path, pagesize=landscape(A4),
                            leftMargin=15*mm, rightMargin=15*mm,
                            topMargin=15*mm, bottomMargin=15*mm)

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "FullReportTitle", parent=styles["Title"],
        fontSize=18, spaceAfter=6,
    )
    subtitle_style = ParagraphStyle(
        "FullReportSubtitle", parent=styles["Normal"],
        fontSize=11, textColor=colors.grey, spaceAfter=12,
    )
    heading_style = ParagraphStyle(
        "FullReportHeading", parent=styles["Heading2"],
        fontSize=13, spaceAfter=8,
    )
    cell_style = ParagraphStyle(
        "CellWrap", parent=styles["Normal"],
        fontSize=7, leading=9,
    )

    elements = []

    # Title
    elements.append(Paragraph("Full Section Report", title_style))
    elements.append(Paragraph(
        f"Section: {report['section_name']}  |  "
        f"Schedule: {report['section_day']} {report['section_time']}  |  "
        f"Total sessions: {len(report['session_dates'])}  |  "
        f"Total students: {len(report['students'])}",
        subtitle_style,
    ))
    elements.append(Spacer(1, 6*mm))

    # ── Summary table (one row per student) ───────────────────────────────
    elements.append(Paragraph("Student Summary", heading_style))

    summary_data = [["#", "Last Name", "First Name", "Present", "Absent", "Sessions", "Rate"]]
    for i, stu in enumerate(report["students"], 1):
        summary_data.append([
            str(i),
            stu["last_name"],
            stu["first_name"],
            str(stu["total_present"]),
            str(stu["total_absent"]),
            str(stu["total_sessions"]),
            stu["attendance_pct"],
        ])

    summary_col_widths = [30, 120, 120, 60, 60, 60, 60]
    summary_table = Table(summary_data, colWidths=summary_col_widths)
    summary_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e40af")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ALIGN", (0, 0), (0, -1), "CENTER"),
        ("ALIGN", (3, 0), (-1, -1), "CENTER"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1),
         [colors.white, colors.HexColor("#f8f9fa")]),
    ]))

    # Colour-code the Rate column
    for i, stu in enumerate(report["students"], 1):
        pct_str = stu["attendance_pct"]
        try:
            pct_val = int(pct_str.replace("%", ""))
        except (ValueError, AttributeError):
            pct_val = -1
        if pct_val >= 75:
            clr = colors.HexColor("#166534")
        elif pct_val >= 50:
            clr = colors.HexColor("#92400e")
        else:
            clr = colors.HexColor("#991b1b")
        summary_table.setStyle(TableStyle([
            ("TEXTCOLOR", (6, i), (6, i), clr),
        ]))

    elements.append(summary_table)
    elements.append(Spacer(1, 8*mm))

    # ── Detailed date-by-date attendance grid ─────────────────────────────
    session_dates = report["session_dates"]
    if session_dates and report["students"]:
        elements.append(Paragraph("Detailed Attendance Grid", heading_style))

        # Determine how many date columns fit per page (~250mm usable in landscape)
        max_date_cols = 12
        date_chunks = [
            session_dates[i:i + max_date_cols]
            for i in range(0, len(session_dates), max_date_cols)
        ]

        for chunk_idx, date_chunk in enumerate(date_chunks):
            if chunk_idx > 0:
                elements.append(PageBreak())
                elements.append(Paragraph(
                    f"Detailed Attendance Grid (cont. — dates {chunk_idx * max_date_cols + 1}"
                    f"–{min((chunk_idx + 1) * max_date_cols, len(session_dates))})",
                    heading_style,
                ))

            # Short date labels for column headers (MM-DD)
            short_dates = []
            for d in date_chunk:
                try:
                    short_dates.append(datetime.strptime(d, "%Y-%m-%d").strftime("%m/%d"))
                except ValueError:
                    short_dates.append(d[-5:])

            header = ["Student"] + short_dates
            grid_data = [header]

            for stu in report["students"]:
                row = [Paragraph(f"{stu['last_name']}, {stu['first_name']}", cell_style)]
                for d in date_chunk:
                    status = stu["records"].get(d)
                    if status == "Present":
                        row.append("✓")
                    elif status == "Absent":
                        row.append("✗")
                    else:
                        row.append("—")
                grid_data.append(row)

            name_col_w = 110
            date_col_w = max(35, min(50, int((250 * mm - name_col_w) / len(date_chunk))))
            grid_col_widths = [name_col_w] + [date_col_w] * len(date_chunk)

            grid_table = Table(grid_data, colWidths=grid_col_widths)
            grid_style = [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f4c75")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 7),
                ("FONTSIZE", (0, 1), (-1, -1), 8),
                ("ALIGN", (1, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1),
                 [colors.white, colors.HexColor("#f8f9fa")]),
            ]

            # Colour-code individual status cells
            for row_i, stu in enumerate(report["students"], 1):
                for col_j, d in enumerate(date_chunk, 1):
                    status = stu["records"].get(d)
                    if status == "Present":
                        grid_style.append(
                            ("TEXTCOLOR", (col_j, row_i), (col_j, row_i),
                             colors.HexColor("#166534"))
                        )
                    elif status == "Absent":
                        grid_style.append(
                            ("TEXTCOLOR", (col_j, row_i), (col_j, row_i),
                             colors.HexColor("#991b1b"))
                        )

            grid_table.setStyle(TableStyle(grid_style))
            elements.append(grid_table)
            elements.append(Spacer(1, 4*mm))

    # Footer
    elements.append(Spacer(1, 6*mm))
    elements.append(Paragraph(
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        ParagraphStyle("FullFooter", parent=styles["Normal"],
                       fontSize=8, textColor=colors.grey),
    ))

    doc.build(elements)
    log_info(f"Full section PDF generated: {output_path}")
    return output_path


# ═══════════════════════════════════════════════════════════════════════════════
# Sections-by-day helper (for dynamic section filtering)
# ═══════════════════════════════════════════════════════════════════════════════


def get_sections_for_day(day: str) -> list:
    """Return all sections scheduled for a given English weekday name."""
    all_sections = section_model.get_all_sections()
    return [s for s in all_sections if s["day"].strip().lower() == day.strip().lower()]

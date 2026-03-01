"""
report_tab.py — Unified Report tab in the Admin Panel.

Supports two modes:
  Mode A (Daily Section Report)  — select Date + Section → per-student report + PDF export
  Mode B (Full Section Report)   — select Section only  → all sessions for that section
"""

from __future__ import annotations

from datetime import date, datetime
from tkinter import messagebox, filedialog
from typing import Any, Optional

import customtkinter as ctk
from tkcalendar import Calendar

import controllers.report_controller as report_ctrl
import controllers.section_controller as section_ctrl
from utils.logger import log_info, log_error

_BG = "#1a1a2e"
_CARD_BG = "#0f0f23"
_ROW_BG = "#1e1e35"


class ReportTab(ctk.CTkFrame):
    """Unified Report tab — mounted inside the Admin Panel tab view."""

    def __init__(self, parent: Any, root: Any) -> None:
        super().__init__(parent, fg_color=_BG, corner_radius=0)
        self._app = root

        # Data caches
        self._sections: list = []
        self._section_map: dict[str, int] = {}   # display_name → id

        self._build_ui()

    # ──────────────────────────────────────────────────────────────────────────
    # UI construction
    # ──────────────────────────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        # ── Header ────────────────────────────────────────────────────────────
        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.pack(fill="x", padx=24, pady=(18, 8))
        ctk.CTkLabel(
            hdr, text="Reports",
            font=ctk.CTkFont(size=26, weight="bold"), text_color="#e0e0e0",
        ).pack(side="left")

        # ── Mode selector ─────────────────────────────────────────────────────
        mode_frame = ctk.CTkFrame(self, fg_color=_CARD_BG, corner_radius=10)
        mode_frame.pack(fill="x", padx=24, pady=(0, 10))

        ctk.CTkLabel(
            mode_frame, text="Report Mode:",
            font=ctk.CTkFont(size=13, weight="bold"), text_color="#e0e0e0",
        ).pack(side="left", padx=(16, 8), pady=12)

        self._mode_var = ctk.StringVar(value="daily")
        ctk.CTkRadioButton(
            mode_frame, text="Daily Section Report",
            variable=self._mode_var, value="daily",
            font=ctk.CTkFont(size=13), text_color="#93c5fd",
            command=self._on_mode_change,
        ).pack(side="left", padx=(0, 20), pady=12)

        ctk.CTkRadioButton(
            mode_frame, text="Full Section Report",
            variable=self._mode_var, value="full",
            font=ctk.CTkFont(size=13), text_color="#93c5fd",
            command=self._on_mode_change,
        ).pack(side="left", padx=(0, 16), pady=12)

        # ── Controls bar ──────────────────────────────────────────────────────
        ctrl_frame = ctk.CTkFrame(self, fg_color=_CARD_BG, corner_radius=10)
        ctrl_frame.pack(fill="x", padx=24, pady=(0, 10))

        # Date picker (only for Mode A)
        self._date_label = ctk.CTkLabel(
            ctrl_frame, text="Date:",
            font=ctk.CTkFont(size=13), text_color="#9ca3af",
        )
        self._date_label.pack(side="left", padx=(16, 6), pady=12)

        self._date_btn = ctk.CTkButton(
            ctrl_frame, text=date.today().isoformat(),
            width=130, height=32,
            fg_color="#374151", hover_color="#4b5563",
            font=ctk.CTkFont(size=13),
            command=self._open_calendar,
        )
        self._date_btn.pack(side="left", padx=(0, 16), pady=12)
        self._selected_date: str = date.today().isoformat()

        # Section selector
        ctk.CTkLabel(
            ctrl_frame, text="Section:",
            font=ctk.CTkFont(size=13), text_color="#9ca3af",
        ).pack(side="left", padx=(0, 6), pady=12)

        self._section_var = ctk.StringVar(value="Select section…")
        self._section_combo = ctk.CTkComboBox(
            ctrl_frame, variable=self._section_var,
            values=["Select section…"],
            width=240, height=32,
            font=ctk.CTkFont(size=13), state="readonly",
        )
        self._section_combo.pack(side="left", padx=(0, 16), pady=12)

        # Generate button
        self._generate_btn = ctk.CTkButton(
            ctrl_frame, text="Generate Report", width=160, height=36,
            fg_color="#2563eb", hover_color="#1d4ed8",
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self._generate_report,
        )
        self._generate_btn.pack(side="left", padx=(0, 8), pady=12)

        # PDF export button (Mode A only)
        self._pdf_btn = ctk.CTkButton(
            ctrl_frame, text="📄 Export PDF", width=130, height=36,
            fg_color="#065f46", hover_color="#047857",
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self._export_pdf,
        )
        self._pdf_btn.pack(side="left", padx=(0, 16), pady=12)

        # ── Result area ───────────────────────────────────────────────────────
        self._result_frame = ctk.CTkScrollableFrame(
            self, fg_color="#111125", corner_radius=8,
        )
        self._result_frame.pack(fill="both", expand=True, padx=24, pady=(0, 24))

        # Placeholder
        self._placeholder = ctk.CTkLabel(
            self._result_frame,
            text="Select mode, section (and date for Daily mode), then click Generate Report.",
            font=ctk.CTkFont(size=14), text_color="#6b7280",
        )
        self._placeholder.pack(pady=40)

        # Store last report for PDF export
        self._last_report: Optional[dict] = None
        self._last_mode: Optional[str] = None

    # ──────────────────────────────────────────────────────────────────────────
    # Calendar popup
    # ──────────────────────────────────────────────────────────────────────────

    def _open_calendar(self) -> None:
        """Open a calendar popup to pick a date."""
        cal_win = ctk.CTkToplevel(self._app)
        cal_win.title("Select Date")
        cal_win.geometry("320x320")
        cal_win.configure(fg_color=_BG)
        cal_win.grab_set()
        cal_win.resizable(False, False)

        # Parse current selection
        try:
            cur = datetime.strptime(self._selected_date, "%Y-%m-%d")
        except ValueError:
            cur = datetime.now()

        cal = Calendar(
            cal_win,
            selectmode="day",
            year=cur.year, month=cur.month, day=cur.day,
            background="#1a1a2e",
            foreground="white",
            headersbackground="#0f0f23",
            headersforeground="#93c5fd",
            selectbackground="#2563eb",
            normalbackground="#1e1e35",
            normalforeground="white",
            weekendbackground="#1e1e35",
            weekendforeground="#f87171",
            othermonthbackground="#111125",
            othermonthforeground="#4b5563",
            othermonthwebackground="#111125",
            othermonthweforeground="#4b5563",
            bordercolor="#374151",
            date_pattern="yyyy-mm-dd",
            font=("Segoe UI", 11),
        )
        cal.pack(fill="both", expand=True, padx=10, pady=(10, 5))

        def _confirm():
            self._selected_date = cal.get_date()
            self._date_btn.configure(text=self._selected_date)
            cal_win.destroy()

        ctk.CTkButton(
            cal_win, text="Select", width=100, height=34,
            fg_color="#2563eb", hover_color="#1d4ed8",
            font=ctk.CTkFont(size=13, weight="bold"),
            command=_confirm,
        ).pack(pady=(0, 10))

        # Centre on parent
        cal_win.update_idletasks()
        pw = self._app.winfo_width()
        ph = self._app.winfo_height()
        px = self._app.winfo_x()
        py = self._app.winfo_y()
        cw = cal_win.winfo_reqwidth()
        ch = cal_win.winfo_reqheight()
        cal_win.geometry(f"+{px + (pw - cw)//2}+{py + (ph - ch)//2}")

    # ──────────────────────────────────────────────────────────────────────────
    # Mode change
    # ──────────────────────────────────────────────────────────────────────────

    def _on_mode_change(self) -> None:
        mode = self._mode_var.get()
        if mode == "daily":
            self._date_label.pack(side="left", padx=(16, 6), pady=12)
            self._date_btn.pack(side="left", padx=(0, 16), pady=12)
        else:
            self._date_label.pack_forget()
            self._date_btn.pack_forget()
        # PDF button stays visible in both modes

    # ──────────────────────────────────────────────────────────────────────────
    # Section loading
    # ──────────────────────────────────────────────────────────────────────────

    def _load_sections(self) -> None:
        """Refresh the section dropdown with all sections from the DB."""
        self._sections = section_ctrl.get_all_sections()
        self._section_map.clear()
        names = []
        for s in self._sections:
            display = f"{s['name']}  ({s['day']} {s['time']})"
            names.append(display)
            self._section_map[display] = s["id"]

        if names:
            self._section_combo.configure(values=names)
            if self._section_var.get() not in names:
                self._section_var.set(names[0])
        else:
            self._section_combo.configure(values=["No sections"])
            self._section_var.set("No sections")

    # ──────────────────────────────────────────────────────────────────────────
    # Report generation
    # ──────────────────────────────────────────────────────────────────────────

    def _generate_report(self) -> None:
        sec_display = self._section_var.get()
        section_id = self._section_map.get(sec_display)
        if section_id is None:
            messagebox.showwarning("No Section", "Please select a valid section.", parent=self._app)
            return

        mode = self._mode_var.get()
        try:
            if mode == "daily":
                report = report_ctrl.get_daily_section_report(section_id, self._selected_date)
                self._last_report = report
                self._last_mode = "daily"
                self._render_daily_report(report)
            else:
                report = report_ctrl.get_full_section_report(section_id)
                self._last_report = report
                self._last_mode = "full"
                self._render_full_report(report)

        except Exception as exc:
            log_error(f"Report generation failed: {exc}")
            messagebox.showerror("Error", f"Could not generate report:\n{exc}", parent=self._app)

    # ──────────────────────────────────────────────────────────────────────────
    # Render: Mode A (Daily Section Report)
    # ──────────────────────────────────────────────────────────────────────────

    def _render_daily_report(self, report: dict) -> None:
        """Render Mode A report in the result frame."""
        self._clear_results()

        # ── Summary card ──────────────────────────────────────────────────────
        summary = ctk.CTkFrame(self._result_frame, fg_color=_CARD_BG, corner_radius=10)
        summary.pack(fill="x", padx=8, pady=(8, 12))

        ctk.CTkLabel(
            summary,
            text=f"Daily Section Report — {report['section_name']}",
            font=ctk.CTkFont(size=18, weight="bold"), text_color="#e0e0e0",
        ).pack(padx=16, pady=(14, 2), anchor="w")
        ctk.CTkLabel(
            summary,
            text=f"Date: {report['date']} ({report['weekday']})  |  Schedule: {report['section_day']} {report['section_time']}",
            font=ctk.CTkFont(size=12), text_color="#6b7280",
        ).pack(padx=16, pady=(0, 10), anchor="w")

        # Stats row
        stats_row = ctk.CTkFrame(summary, fg_color="transparent")
        stats_row.pack(fill="x", padx=16, pady=(0, 14))

        total = report["total_enrolled"]
        present = report["present_count"]
        absent = report["absent_count"]
        no_rec = report["no_record_count"]
        pct = f"{present / total * 100:.0f}%" if total > 0 else "N/A"

        for label, value, color in [
            ("Enrolled", str(total), "#93c5fd"),
            ("Present", str(present), "#4ade80"),
            ("Absent", str(absent), "#f87171"),
            ("No Record", str(no_rec), "#fbbf24"),
            ("Rate", pct, "#a78bfa"),
        ]:
            cell = ctk.CTkFrame(stats_row, fg_color="transparent")
            cell.pack(side="left", expand=True)
            ctk.CTkLabel(
                cell, text=value,
                font=ctk.CTkFont(size=24, weight="bold"), text_color=color,
            ).pack()
            ctk.CTkLabel(
                cell, text=label,
                font=ctk.CTkFont(size=11), text_color="#6b7280",
            ).pack()

        # ── Column header ─────────────────────────────────────────────────────
        col_hdr = ctk.CTkFrame(self._result_frame, fg_color=_CARD_BG, corner_radius=0)
        col_hdr.pack(fill="x", padx=8, pady=(0, 2))
        for txt, w in [("#", 40), ("First Name", 160), ("Last Name", 160), ("Card ID", 140), ("Status", 100)]:
            ctk.CTkLabel(
                col_hdr, text=txt, width=w, anchor="w",
                font=ctk.CTkFont(size=12, weight="bold"), text_color="#6b7280",
            ).pack(side="left", padx=6, pady=6)

        # ── Student rows ──────────────────────────────────────────────────────
        for i, stu in enumerate(report["students"], 1):
            status = stu["status"]
            if status == "Present":
                bg = "#0d2b0d"
                status_color = "#4ade80"
            elif status == "Absent":
                bg = "#2b0d0d"
                status_color = "#f87171"
            else:
                bg = _ROW_BG
                status_color = "#fbbf24"

            row = ctk.CTkFrame(self._result_frame, fg_color=bg, corner_radius=6)
            row.pack(fill="x", padx=8, pady=1)

            ctk.CTkLabel(row, text=str(i), width=40, anchor="w",
                         font=ctk.CTkFont(size=12), text_color="#9ca3af").pack(side="left", padx=6, pady=6)
            ctk.CTkLabel(row, text=stu["first_name"], width=160, anchor="w",
                         font=ctk.CTkFont(size=13), text_color="#e0e0e0").pack(side="left", padx=6)
            ctk.CTkLabel(row, text=stu["last_name"], width=160, anchor="w",
                         font=ctk.CTkFont(size=13), text_color="#e0e0e0").pack(side="left", padx=6)
            ctk.CTkLabel(row, text=stu["card_id"] or "—", width=140, anchor="w",
                         font=ctk.CTkFont(size=12), text_color="#6b7280").pack(side="left", padx=6)
            ctk.CTkLabel(row, text=status, width=100, anchor="w",
                         font=ctk.CTkFont(size=13, weight="bold"), text_color=status_color).pack(side="left", padx=6)

        if not report["students"]:
            ctk.CTkLabel(
                self._result_frame,
                text="No students enrolled in this section.",
                font=ctk.CTkFont(size=14), text_color="#6b7280",
            ).pack(pady=30)

    # ──────────────────────────────────────────────────────────────────────────
    # Render: Mode B (Full Section Report)
    # ──────────────────────────────────────────────────────────────────────────

    def _render_full_report(self, report: dict) -> None:
        """Render Mode B report in the result frame."""
        self._clear_results()

        # ── Summary card ──────────────────────────────────────────────────────
        summary = ctk.CTkFrame(self._result_frame, fg_color=_CARD_BG, corner_radius=10)
        summary.pack(fill="x", padx=8, pady=(8, 12))

        ctk.CTkLabel(
            summary,
            text=f"Full Section Report — {report['section_name']}",
            font=ctk.CTkFont(size=18, weight="bold"), text_color="#e0e0e0",
        ).pack(padx=16, pady=(14, 2), anchor="w")
        ctk.CTkLabel(
            summary,
            text=(
                f"Schedule: {report['section_day']} {report['section_time']}  |  "
                f"Total sessions: {len(report['session_dates'])}  |  "
                f"Total students: {len(report['students'])}"
            ),
            font=ctk.CTkFont(size=12), text_color="#6b7280",
        ).pack(padx=16, pady=(0, 14), anchor="w")

        # ── Per-student cards ─────────────────────────────────────────────────
        for stu in report["students"]:
            self._render_student_card(stu, report["session_dates"])

        if not report["students"]:
            ctk.CTkLabel(
                self._result_frame,
                text="No students enrolled in this section.",
                font=ctk.CTkFont(size=14), text_color="#6b7280",
            ).pack(pady=30)

    def _render_student_card(self, stu: dict, session_dates: list[str]) -> None:
        """Render a single student's full attendance history card."""
        card = ctk.CTkFrame(self._result_frame, fg_color=_CARD_BG, corner_radius=8)
        card.pack(fill="x", padx=8, pady=4)

        # Student header
        hdr = ctk.CTkFrame(card, fg_color="transparent")
        hdr.pack(fill="x", padx=12, pady=(10, 4))

        ctk.CTkLabel(
            hdr,
            text=f"{stu['first_name']} {stu['last_name']}",
            font=ctk.CTkFont(size=14, weight="bold"), text_color="#e0e0e0",
        ).pack(side="left")

        pct_color = "#4ade80" if stu["attendance_pct"] not in ("N/A", "0%") else "#f87171"
        ctk.CTkLabel(
            hdr,
            text=f"Attendance: {stu['total_present']}/{stu['total_sessions']}  ({stu['attendance_pct']})",
            font=ctk.CTkFont(size=12, weight="bold"), text_color=pct_color,
        ).pack(side="right")

        # Attendance record grid
        if session_dates:
            grid = ctk.CTkFrame(card, fg_color="transparent")
            grid.pack(fill="x", padx=12, pady=(2, 10))

            # Show records in rows of date-badges
            for d in session_dates:
                status = stu["records"].get(d)
                if status == "Present":
                    badge_bg = "#166534"
                    badge_fg = "#4ade80"
                    badge_txt = f"✓ {d}"
                elif status == "Absent":
                    badge_bg = "#7f1d1d"
                    badge_fg = "#f87171"
                    badge_txt = f"✗ {d}"
                else:
                    badge_bg = "#374151"
                    badge_fg = "#6b7280"
                    badge_txt = f"— {d}"

                ctk.CTkLabel(
                    grid, text=badge_txt,
                    font=ctk.CTkFont(size=11),
                    text_color=badge_fg, fg_color=badge_bg,
                    corner_radius=4, width=130, height=24,
                ).pack(side="left", padx=2, pady=2)
        else:
            ctk.CTkLabel(
                card, text="No sessions recorded yet.",
                font=ctk.CTkFont(size=12), text_color="#6b7280",
            ).pack(padx=12, pady=(0, 10))

    # ──────────────────────────────────────────────────────────────────────────
    # PDF export
    # ──────────────────────────────────────────────────────────────────────────

    def _export_pdf(self) -> None:
        """Export the currently displayed report (Mode A or B) as a PDF."""
        if self._last_report is None or self._last_mode is None:
            messagebox.showinfo(
                "No Report",
                "Please generate a report first.",
                parent=self._app,
            )
            return

        report = self._last_report

        if self._last_mode == "daily":
            default_name = (
                f"Report_{report['section_name']}_{report['date']}.pdf"
                .replace(" ", "_")
            )
        else:
            default_name = (
                f"FullReport_{report['section_name']}.pdf"
                .replace(" ", "_")
            )

        path = filedialog.asksaveasfilename(
            parent=self._app,
            title="Save PDF Report",
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")],
            initialfile=default_name,
        )
        if not path:
            return

        try:
            if self._last_mode == "daily":
                report_ctrl.generate_daily_section_pdf(report, path)
            else:
                report_ctrl.generate_full_section_pdf(report, path)

            messagebox.showinfo(
                "PDF Exported",
                f"Report saved to:\n{path}",
                parent=self._app,
            )
            log_info(f"PDF exported: {path}")
        except Exception as exc:
            log_error(f"PDF export failed: {exc}")
            messagebox.showerror("Error", f"Could not export PDF:\n{exc}", parent=self._app)

    # ──────────────────────────────────────────────────────────────────────────
    # Helpers
    # ──────────────────────────────────────────────────────────────────────────

    def _clear_results(self) -> None:
        for w in self._result_frame.winfo_children():
            w.destroy()

    # ──────────────────────────────────────────────────────────────────────────
    # Public hook
    # ──────────────────────────────────────────────────────────────────────────

    def on_tab_selected(self) -> None:
        """Called by AdminPanel when this tab becomes active — reload sections."""
        self._load_sections()

"""
manual_attendance_dialog.py — Admin manual attendance editor.

Opened from the Students tab in the Admin Panel.
Lets an admin view and change a student's attendance across all their enrolled
sections for any calendar date.
"""

from __future__ import annotations

from datetime import date
from typing import Any

import customtkinter as ctk
from tkinter import messagebox

import controllers.attendance_controller as attendance_ctrl
from utils.logger import log_info


class ManualAttendanceDialog(ctk.CTkToplevel):
    """
    Modal dialog for viewing and manually editing a student's attendance.

    Usage:
        dlg = ManualAttendanceDialog(parent, student_id, student_name)
        parent.wait_window(dlg)
    """

    def __init__(self, parent: Any, student_id: int, student_name: str) -> None:
        super().__init__(parent)
        self.title(f"Attendance — {student_name}")
        self.resizable(True, True)
        self.minsize(640, 400)

        self._student_id   = student_id
        self._student_name = student_name
        self._parent       = parent

        self._date_var = ctk.StringVar(value=date.today().isoformat())

        self._build_ui()
        self._refresh_rows()

        # Activation / centering deferred to first render tick
        self.after(50, self._activate)

    # ──────────────────────────────────────────────────────────────────────────
    # Window management
    # ──────────────────────────────────────────────────────────────────────────

    def _activate(self) -> None:
        self._centre()
        self.grab_set()
        self.lift()
        self.focus_force()
        self.attributes("-topmost", True)
        self.after(200, lambda: self.attributes("-topmost", False))

    def _centre(self) -> None:
        self.update_idletasks()
        pw = self._parent.winfo_width()
        ph = self._parent.winfo_height()
        px = self._parent.winfo_x()
        py = self._parent.winfo_y()
        w  = max(self.winfo_width(), 680)
        h  = max(self.winfo_height(), 480)
        x  = px + max(0, (pw - w) // 2)
        y  = py + max(0, (ph - h) // 2)
        self.geometry(f"{w}x{h}+{x}+{y}")

    # ──────────────────────────────────────────────────────────────────────────
    # UI construction
    # ──────────────────────────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        self.configure(fg_color="#1a1a2e")

        # ── Header ────────────────────────────────────────────────────────────
        hdr = ctk.CTkFrame(self, fg_color="#0f0f23", corner_radius=0, height=60)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)

        ctk.CTkLabel(
            hdr,
            text=f"📋  {self._student_name}",
            font=ctk.CTkFont(size=17, weight="bold"),
            text_color="#e0e0e0",
        ).pack(side="left", padx=20)

        ctk.CTkButton(
            hdr, text="✕  Close", width=90, height=34,
            fg_color="#374151", hover_color="#7f1d1d",
            font=ctk.CTkFont(size=13),
            command=self.destroy,
        ).pack(side="right", padx=14, pady=12)

        # ── Date selector ─────────────────────────────────────────────────────
        date_bar = ctk.CTkFrame(self, fg_color="#111125", corner_radius=0, height=50)
        date_bar.pack(fill="x")
        date_bar.pack_propagate(False)

        ctk.CTkLabel(
            date_bar, text="Date:",
            font=ctk.CTkFont(size=13), text_color="#9ca3af",
        ).pack(side="left", padx=(20, 6), pady=12)

        self._date_entry = ctk.CTkEntry(
            date_bar,
            textvariable=self._date_var,
            width=130, height=32,
            font=ctk.CTkFont(size=13),
            placeholder_text="YYYY-MM-DD",
        )
        self._date_entry.pack(side="left", pady=12)
        self._date_entry.bind("<Return>", lambda _e: self._refresh_rows())

        ctk.CTkButton(
            date_bar, text="Today", width=70, height=32,
            fg_color="#374151", hover_color="#4b5563",
            font=ctk.CTkFont(size=12),
            command=self._go_today,
        ).pack(side="left", padx=8, pady=12)

        ctk.CTkButton(
            date_bar, text="Refresh ↺", width=90, height=32,
            fg_color="#1e40af", hover_color="#1d4ed8",
            font=ctk.CTkFont(size=12),
            command=self._refresh_rows,
        ).pack(side="left", padx=(0, 8), pady=12)

        self._date_status = ctk.CTkLabel(
            date_bar, text="",
            font=ctk.CTkFont(size=12), text_color="#f87171",
        )
        self._date_status.pack(side="left", padx=8)

        # ── Column header ─────────────────────────────────────────────────────
        col_hdr = ctk.CTkFrame(self, fg_color="#0f0f23", corner_radius=0, height=32)
        col_hdr.pack(fill="x", padx=0)
        col_hdr.pack_propagate(False)

        for txt, w in [("Section", 220), ("Schedule", 160), ("Status", 100), ("Actions", 200)]:
            ctk.CTkLabel(
                col_hdr, text=txt, width=w,
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color="#6b7280", anchor="w",
            ).pack(side="left", padx=8)

        # ── Scrollable rows area ──────────────────────────────────────────────
        self._rows_frame = ctk.CTkScrollableFrame(
            self, fg_color="#111125", corner_radius=0,
        )
        self._rows_frame.pack(fill="both", expand=True, pady=(0, 0))

        # ── Footer hint ───────────────────────────────────────────────────────
        footer = ctk.CTkFrame(self, fg_color="#0f0f23", corner_radius=0, height=32)
        footer.pack(fill="x")
        footer.pack_propagate(False)

        ctk.CTkLabel(
            footer,
            text="Changes are saved immediately.  "
                 "Marking a section not on the selected weekday will still create a session for that date.",
            font=ctk.CTkFont(size=10),
            text_color="#4b5563",
        ).pack(side="left", padx=14)

    # ──────────────────────────────────────────────────────────────────────────
    # Data + rendering
    # ──────────────────────────────────────────────────────────────────────────

    def _go_today(self) -> None:
        self._date_var.set(date.today().isoformat())
        self._refresh_rows()

    def _refresh_rows(self) -> None:
        """Re-query the DB and rebuild the section rows."""
        date_str = self._date_var.get().strip()

        # Basic date validation
        try:
            date.fromisoformat(date_str)
            self._date_status.configure(text="")
        except ValueError:
            self._date_status.configure(
                text=f"  ✕ Invalid date format — use YYYY-MM-DD"
            )
            return

        # Clear previous rows
        for w in self._rows_frame.winfo_children():
            w.destroy()

        try:
            rows = attendance_ctrl.get_student_attendance_overview(self._student_id, date_str)
        except Exception as exc:
            messagebox.showerror("Error", f"Could not load attendance:\n{exc}", parent=self)
            return

        if not rows:
            ctk.CTkLabel(
                self._rows_frame,
                text="Student is not enrolled in any sections.",
                font=ctk.CTkFont(size=14), text_color="#6b7280",
            ).pack(pady=30)
            return

        for row in rows:
            self._render_section_row(row, date_str)

    def _render_section_row(self, row: dict, date_str: str) -> None:
        status: str | None = row["status"]   # 'Present', 'Absent', or None

        # Row background by status
        if status == "Present":
            bg = "#0d2b0d"
        elif status == "Absent":
            bg = "#2b0d0d"
        else:
            bg = "#1e1e35"

        frame = ctk.CTkFrame(self._rows_frame, fg_color=bg, corner_radius=6)
        frame.pack(fill="x", padx=6, pady=2)

        # Section name
        ctk.CTkLabel(
            frame,
            text=row["section_name"],
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#e0e0e0", width=220, anchor="w",
        ).pack(side="left", padx=(12, 4), pady=8)

        # Schedule
        schedule = f"{row['day']}  {row['time']}".strip()
        ctk.CTkLabel(
            frame,
            text=schedule or "—",
            font=ctk.CTkFont(size=12),
            text_color="#9ca3af", width=160, anchor="w",
        ).pack(side="left", padx=4)

        # Status badge
        if status == "Present":
            badge_text, badge_color = "● Present", "#4ade80"
        elif status == "Absent":
            badge_text, badge_color = "● Absent",  "#f87171"
        else:
            badge_text, badge_color = "○ No Record", "#6b7280"

        ctk.CTkLabel(
            frame,
            text=badge_text,
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=badge_color, width=100, anchor="w",
        ).pack(side="left", padx=4)

        # Action buttons
        btn_frame = ctk.CTkFrame(frame, fg_color="transparent")
        btn_frame.pack(side="left", padx=8, pady=6)

        present_color = "#166534" if status == "Present" else "#374151"
        ctk.CTkButton(
            btn_frame, text="✓ Present", width=90, height=28,
            fg_color=present_color, hover_color="#166534",
            font=ctk.CTkFont(size=12),
            command=lambda sid=row["section_id"]: self._set(sid, date_str, "Present"),
        ).pack(side="left", padx=(0, 4))

        absent_color = "#7f1d1d" if status == "Absent" else "#374151"
        ctk.CTkButton(
            btn_frame, text="✗ Absent", width=90, height=28,
            fg_color=absent_color, hover_color="#7f1d1d",
            font=ctk.CTkFont(size=12),
            command=lambda sid=row["section_id"]: self._set(sid, date_str, "Absent"),
        ).pack(side="left")

    # ──────────────────────────────────────────────────────────────────────────
    # Action handler
    # ──────────────────────────────────────────────────────────────────────────

    def _set(self, section_id: int, date_str: str, target_status: str) -> None:
        ok, err = attendance_ctrl.set_student_attendance(
            self._student_id, section_id, date_str, target_status
        )
        if ok:
            log_info(
                f"ManualAttendance: student={self._student_id} "
                f"section={section_id} date={date_str} → {target_status}"
            )
            self._refresh_rows()
        else:
            messagebox.showerror("Error", f"Could not update attendance:\n{err}", parent=self)

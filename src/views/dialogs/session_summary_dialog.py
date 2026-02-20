"""
session_summary_dialog.py — End-of-session absent summary popup (Task 1.16).

Shows total enrolled, present/absent counts, and the named absent list.
Also allows last-minute manual attendance toggles before confirming.
"""

from __future__ import annotations

from typing import Callable, Optional

import customtkinter as ctk

import controllers.attendance_controller as attendance_controller
from controllers.session_controller import SessionSummary
from utils.logger import log_info


class SessionSummaryDialog(ctk.CTkToplevel):
    """
    Modal end-session dialog.

    After construction call .wait_window().
    .confirmed is True if the user clicked "Confirm & Close Session".
    """

    def __init__(
        self,
        parent: ctk.CTk,
        summary: SessionSummary,
        on_confirm: Optional[Callable[[], None]] = None,
    ) -> None:
        super().__init__(parent)
        self.title("End Session — Summary")
        self.resizable(False, False)
        self.grab_set()

        self._summary = summary
        self._on_confirm = on_confirm
        self.confirmed: bool = False

        self._build_ui()
        self._centre(parent)

    def _centre(self, parent: ctk.CTk) -> None:
        self.update_idletasks()
        pw = parent.winfo_width()
        ph = parent.winfo_height()
        px = parent.winfo_x()
        py = parent.winfo_y()
        dw = self.winfo_reqwidth()
        dh = min(self.winfo_reqheight(), ph - 80)
        x = px + (pw - dw) // 2
        y = py + (ph - dh) // 2
        self.geometry(f"+{x}+{y}")

    def _build_ui(self) -> None:
        self.configure(fg_color="#1a1a2e")
        s = self._summary

        # ── Title ─────────────────────────────────────────────────────────────
        ctk.CTkLabel(
            self,
            text="Session Complete",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color="#e0e0e0",
        ).pack(padx=32, pady=(24, 2))

        ctk.CTkLabel(
            self,
            text=f"Section: {s.section_name}",
            font=ctk.CTkFont(size=14),
            text_color="#a0a0b0",
        ).pack(padx=32, pady=(0, 16))

        # ── Stats row ─────────────────────────────────────────────────────────
        stats_frame = ctk.CTkFrame(self, fg_color="#0f0f23", corner_radius=10)
        stats_frame.pack(padx=32, pady=(0, 16), fill="x")

        for label, value, color in [
            ("Enrolled", str(s.total_enrolled), "#e0e0e0"),
            ("Present",  str(s.present_count),  "#4ade80"),
            ("Absent",   str(s.absent_count),   "#f87171"),
        ]:
            col = ctk.CTkFrame(stats_frame, fg_color="transparent")
            col.pack(side="left", expand=True, pady=14)
            ctk.CTkLabel(
                col, text=value, font=ctk.CTkFont(size=28, weight="bold"),
                text_color=color,
            ).pack()
            ctk.CTkLabel(
                col, text=label, font=ctk.CTkFont(size=12),
                text_color="#808090",
            ).pack()

        # ── Absent student list ────────────────────────────────────────────────
        if s.absent_students:
            ctk.CTkLabel(
                self,
                text="Absent Students",
                font=ctk.CTkFont(size=15, weight="bold"),
                text_color="#e0e0e0",
                anchor="w",
            ).pack(padx=32, pady=(0, 6), fill="x")

            list_frame = ctk.CTkScrollableFrame(
                self, height=min(len(s.absent_students) * 46, 240),
                fg_color="#0f0f23", corner_radius=8,
            )
            list_frame.pack(padx=32, pady=(0, 16), fill="x")

            for abs_student in s.absent_students:
                row_frame = ctk.CTkFrame(list_frame, fg_color="transparent")
                row_frame.pack(fill="x", pady=2)

                ctk.CTkLabel(
                    row_frame,
                    text=f"{abs_student.last_name}, {abs_student.first_name}",
                    font=ctk.CTkFont(size=14),
                    text_color="#f0f0f0",
                    anchor="w",
                ).pack(side="left", padx=8, pady=4)

                # Last-minute toggle: mark Present
                toggle_btn = ctk.CTkButton(
                    row_frame,
                    text="Mark Present",
                    width=120,
                    height=32,
                    fg_color="#2563eb",
                    hover_color="#1d4ed8",
                    font=ctk.CTkFont(size=12),
                    command=lambda sid=abs_student.student_id, btn=None: self._toggle_present(  # noqa: E501
                        sid, row_frame
                    ),
                )
                toggle_btn.pack(side="right", padx=8)
        else:
            ctk.CTkLabel(
                self,
                text="All enrolled students are present!",
                font=ctk.CTkFont(size=14),
                text_color="#4ade80",
            ).pack(padx=32, pady=(0, 16))

        # ── Buttons ───────────────────────────────────────────────────────────
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(padx=32, pady=(0, 24))

        ctk.CTkButton(
            btn_frame,
            text="Cancel (keep session open)",
            width=200,
            height=44,
            fg_color="#374151",
            hover_color="#4b5563",
            command=self._cancel,
            font=ctk.CTkFont(size=13),
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            btn_frame,
            text="Confirm & Close Session",
            width=220,
            height=44,
            fg_color="#dc2626",
            hover_color="#b91c1c",
            command=self._confirm,
            font=ctk.CTkFont(size=14, weight="bold"),
        ).pack(side="left")

        self.protocol("WM_DELETE_WINDOW", self._cancel)

    def _toggle_present(self, student_id: int, row_frame: ctk.CTkFrame) -> None:
        """Toggle absent → present for a student directly from this dialog."""
        new_status = attendance_controller.toggle_attendance(
            self._summary.session_id, student_id
        )
        if new_status == "Present":
            # Disable the toggle button and dim the row to show it's been handled
            for widget in row_frame.winfo_children():
                if isinstance(widget, ctk.CTkButton):
                    widget.configure(
                        state="disabled",
                        text="Present ✓",
                        fg_color="#16a34a",
                    )
            log_info(
                f"Summary dialog: toggled student_id={student_id} → Present"
            )

    def _confirm(self) -> None:
        self.confirmed = True
        if self._on_confirm:
            self._on_confirm()
        self.destroy()

    def _cancel(self) -> None:
        self.confirmed = False
        self.destroy()

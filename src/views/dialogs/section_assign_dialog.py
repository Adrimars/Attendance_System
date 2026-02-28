"""
section_assign_dialog.py — Assign sections to an existing student after an RFID tap.

Triggered by AttendanceTab when process_rfid_passive() returns NO_SECTIONS
(student is known but has zero sections enrolled).

The student's name is displayed for confirmation.  The user picks one or more
sections via checkboxes and confirms.  On close the dialog exposes
``section_ids`` (list of chosen section ids).  The attendance tab then enrolls
the student and marks them present.
"""

from __future__ import annotations

from typing import Optional

import customtkinter as ctk
from tkinter import messagebox

import controllers.section_controller as section_controller
import controllers.student_controller as student_ctrl
from utils.logger import log_info


class SectionAssignDialog(ctk.CTkToplevel):
    """
    Modal dialog to assign sections to an already-registered student who
    currently has no section enrolments.

    Usage::

        dlg = SectionAssignDialog(parent, student_id, first_name, last_name)
        parent.wait_window(dlg)
        if dlg.confirmed:
            # dlg.section_ids contains the newly enrolled section ids
    """

    def __init__(
        self,
        parent: ctk.CTk,
        student_id: int,
        first_name: str,
        last_name: str,
        pre_selected: list[int] | None = None,
    ) -> None:
        super().__init__(parent)
        self.title("Assign Sections")
        self.resizable(False, False)
        self.grab_set()

        self._student_id = student_id
        self._first_name = first_name
        self._last_name  = last_name
        self._pre_selected = set(pre_selected) if pre_selected else set()

        self.confirmed: bool = False
        self.section_ids: list[int] = []

        self._sections = section_controller.get_all_sections()
        self._section_vars: dict[int, ctk.BooleanVar] = {}

        self._build_ui()
        self._centre(parent)

    # ─────────────────────────────────────────────────────────────────────────
    # Layout
    # ─────────────────────────────────────────────────────────────────────────

    def _centre(self, parent: ctk.CTk) -> None:
        self.update_idletasks()
        pw, ph = parent.winfo_width(), parent.winfo_height()
        px, py = parent.winfo_x(), parent.winfo_y()
        dw = self.winfo_reqwidth()
        dh = self.winfo_reqheight()
        self.geometry(f"+{px + (pw - dw) // 2}+{py + (ph - dh) // 2}")

    def _build_ui(self) -> None:
        self.configure(fg_color="#1a1a2e")
        pad = {"padx": 32, "pady": 6}

        # ── Title ─────────────────────────────────────────────────────────────
        ctk.CTkLabel(
            self,
            text="No Sections Assigned",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color="#e0e0e0",
        ).pack(padx=32, pady=(24, 2))

        ctk.CTkLabel(
            self,
            text=f"{self._first_name} {self._last_name}",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#93c5fd",
        ).pack(padx=32, pady=(0, 4))

        ctk.CTkLabel(
            self,
            text="This student has no sections enrolled.\n"
                 "Please select their section(s) below.",
            font=ctk.CTkFont(size=13),
            text_color="#9ca3af",
            justify="center",
        ).pack(padx=32, pady=(0, 12))

        # ── Section checkboxes ────────────────────────────────────────────────
        ctk.CTkLabel(
            self, text="Sections *",
            font=ctk.CTkFont(size=13), text_color="#c0c0d0", anchor="w",
        ).pack(fill="x", padx=32, pady=(0, 4))

        sec_scroll = ctk.CTkScrollableFrame(
            self, fg_color="#0f0f23", corner_radius=8,
            height=min(200, max(60, len(self._sections) * 36)),
            width=360,
        )
        sec_scroll.pack(padx=32, pady=(0, 6))

        if self._sections:
            for sec in self._sections:
                var = ctk.BooleanVar(value=(sec["id"] in self._pre_selected))
                self._section_vars[sec["id"]] = var
                ctk.CTkCheckBox(
                    sec_scroll,
                    text=f"{sec['name']}  ({sec['day']} {sec['time']})",
                    variable=var,
                    font=ctk.CTkFont(size=13),
                    text_color="#d0d0e0",
                    checkbox_width=20, checkbox_height=20,
                ).pack(anchor="w", padx=10, pady=4)
        else:
            ctk.CTkLabel(
                sec_scroll,
                text="No sections available — add sections via the Sections tab.",
                font=ctk.CTkFont(size=12), text_color="#6b7280",
            ).pack(padx=10, pady=10)

        # ── Status label ──────────────────────────────────────────────────────
        self._status_lbl = ctk.CTkLabel(
            self, text="", font=ctk.CTkFont(size=12), text_color="#ff6b6b",
        )
        self._status_lbl.pack(padx=32, pady=(4, 6))

        # ── Buttons ───────────────────────────────────────────────────────────
        btn_row = ctk.CTkFrame(self, fg_color="transparent")
        btn_row.pack(padx=32, pady=(0, 24))

        ctk.CTkButton(
            btn_row, text="Skip for Now", width=140, height=44,
            fg_color="#374151", hover_color="#4b5563",
            font=ctk.CTkFont(size=13),
            command=self._skip,
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            btn_row, text="Assign & Mark Present", width=220, height=44,
            fg_color="#16a34a", hover_color="#15803d",
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self._confirm,
        ).pack(side="left")

        self.protocol("WM_DELETE_WINDOW", self._skip)

    # ─────────────────────────────────────────────────────────────────────────
    # Actions
    # ─────────────────────────────────────────────────────────────────────────

    def _confirm(self) -> None:
        selected_ids = [
            sec_id for sec_id, var in self._section_vars.items() if var.get()
        ]
        if not selected_ids:
            self._status_lbl.configure(text="Please select at least one section.")
            return

        # Persist the section enrolments via the controller (MVC-compliant)
        ok, msg = student_ctrl.update_student_sections(self._student_id, selected_ids)
        if not ok:
            self._status_lbl.configure(text=msg)
            return

        log_info(
            f"SectionAssignDialog: student_id={self._student_id} "
            f"({self._first_name} {self._last_name}) assigned sections={selected_ids}"
        )
        self.confirmed = True
        self.section_ids = selected_ids
        self.destroy()

    def _skip(self) -> None:
        self.confirmed = False
        self.section_ids = []
        self.destroy()

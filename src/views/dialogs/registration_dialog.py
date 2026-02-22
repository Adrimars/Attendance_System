"""
registration_dialog.py — Register a new student after an unknown RFID card tap.

Triggered by AttendanceTab when process_rfid_passive() returns UNKNOWN_CARD.
The card_id is pre-filled; the user enters first name, last name, and selects
one or more sections.  On confirmation calls
student_controller.register_student_with_sections() and exposes student_id.
"""

from __future__ import annotations

from typing import Optional

import customtkinter as ctk

import controllers.student_controller as student_controller
import controllers.section_controller as section_controller
from utils.logger import log_info


class RegistrationDialog(ctk.CTkToplevel):
    """
    Modal dialog to register a new student for an unknown RFID card.

    Usage::

        dlg = RegistrationDialog(parent, card_id)
        parent.wait_window(dlg)
        if dlg.student_id is not None:
            # registration succeeded; student_id is the new row id
    """

    def __init__(self, parent: ctk.CTk, card_id: str) -> None:
        super().__init__(parent)
        self.title("Register New Student")
        self.resizable(False, False)
        self.grab_set()

        self.card_id: str = card_id
        self.student_id: Optional[int] = None   # set on successful save
        self.section_ids: list[int] = []        # set on successful save

        self._sections = section_controller.get_all_sections()
        self._section_vars: dict[int, ctk.BooleanVar] = {}

        self._build_ui()
        self._centre(parent)

    # ──────────────────────────────────────────────────────────────────────────
    # Layout
    # ──────────────────────────────────────────────────────────────────────────

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

        ctk.CTkLabel(
            self,
            text="Register New Student",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color="#e0e0e0",
        ).pack(padx=32, pady=(24, 2))

        # Card ID badge (read-only)
        ctk.CTkLabel(
            self,
            text=f"Card ID:  {self.card_id}",
            font=ctk.CTkFont(size=13),
            text_color="#a0a0b0",
        ).pack(padx=32, pady=(0, 14))

        # ── First name ────────────────────────────────────────────────────────
        ctk.CTkLabel(
            self, text="First Name *", font=ctk.CTkFont(size=13),
            text_color="#c0c0d0", anchor="w",
        ).pack(fill="x", **pad)
        self._first_entry = ctk.CTkEntry(
            self, placeholder_text="First name",
            width=340, height=44, font=ctk.CTkFont(size=15),
        )
        self._first_entry.pack(**pad)
        self._first_entry.focus_set()

        # ── Last name ─────────────────────────────────────────────────────────
        ctk.CTkLabel(
            self, text="Last Name *", font=ctk.CTkFont(size=13),
            text_color="#c0c0d0", anchor="w",
        ).pack(fill="x", **pad)
        self._last_entry = ctk.CTkEntry(
            self, placeholder_text="Last name",
            width=340, height=44, font=ctk.CTkFont(size=15),
        )
        self._last_entry.pack(**pad)

        # ── Section assignment (checkboxes) ───────────────────────────────────
        ctk.CTkLabel(
            self, text="Sections", font=ctk.CTkFont(size=13),
            text_color="#c0c0d0", anchor="w",
        ).pack(fill="x", padx=32, pady=(10, 4))

        sec_scroll = ctk.CTkScrollableFrame(
            self, fg_color="#0f0f23", corner_radius=8,
            height=min(180, max(60, len(self._sections) * 36)),
            width=340,
        )
        sec_scroll.pack(padx=32, pady=(0, 6))

        if self._sections:
            for sec in self._sections:
                var = ctk.BooleanVar(value=False)
                self._section_vars[sec["id"]] = var
                ctk.CTkCheckBox(
                    sec_scroll,
                    text=f"{sec['name']}  ({sec['day']} {sec['time']})",
                    variable=var,
                    font=ctk.CTkFont(size=13),
                    text_color="#d0d0e0",
                    checkbox_width=20, checkbox_height=20,
                ).pack(anchor="w", padx=8, pady=4)
        else:
            ctk.CTkLabel(
                sec_scroll,
                text="No sections available — add sections via admin panel.",
                font=ctk.CTkFont(size=12),
                text_color="#6b7280",
            ).pack(padx=8, pady=8)

        # ── Status label ──────────────────────────────────────────────────────
        self._status_lbl = ctk.CTkLabel(
            self, text="", font=ctk.CTkFont(size=12), text_color="#ff6b6b",
        )
        self._status_lbl.pack(padx=32, pady=(4, 6))

        # ── Buttons ───────────────────────────────────────────────────────────
        btn_row = ctk.CTkFrame(self, fg_color="transparent")
        btn_row.pack(padx=32, pady=(0, 24))

        ctk.CTkButton(
            btn_row, text="Cancel", width=140, height=44,
            fg_color="#374151", hover_color="#4b5563",
            font=ctk.CTkFont(size=14),
            command=self._cancel,
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            btn_row, text="Register & Mark Present", width=220, height=44,
            fg_color="#16a34a", hover_color="#15803d",
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self._confirm,
        ).pack(side="left")

        self._last_entry.bind("<Return>", lambda _e: self._confirm())
        self.protocol("WM_DELETE_WINDOW", self._cancel)

    # ──────────────────────────────────────────────────────────────────────────
    # Actions
    # ──────────────────────────────────────────────────────────────────────────

    def _confirm(self) -> None:
        first = self._first_entry.get().strip()
        last  = self._last_entry.get().strip()
        selected_ids = [
            sec_id for sec_id, var in self._section_vars.items() if var.get()
        ]

        result = student_controller.register_student_with_sections(
            first, last, self.card_id, selected_ids
        )

        if result.success:
            self.student_id = result.student_id
            self.section_ids = selected_ids
            log_info(
                f"RegistrationDialog: registered student_id={self.student_id} "
                f"sections={selected_ids}"
            )
            self.destroy()
        else:
            self._status_lbl.configure(text=result.message)

    def _cancel(self) -> None:
        self.student_id = None
        self.destroy()

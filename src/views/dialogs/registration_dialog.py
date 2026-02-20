"""
registration_dialog.py — Popup for registering a new student after an unknown card tap.

Triggered by AttendanceTab when process_card_tap() returns UNKNOWN_CARD.
On confirmation, returns the new student_id (or None if cancelled).
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

    After construction call .wait_window() and check .student_id to know if
    registration succeeded.
    """

    def __init__(self, parent: ctk.CTk, card_id: str) -> None:
        super().__init__(parent)
        self.title("Register New Student")
        self.resizable(False, False)
        self.grab_set()

        self.card_id: str = card_id
        self.student_id: Optional[int] = None   # Set on successful registration

        self._sections = section_controller.get_all_sections()

        self._build_ui()
        self._centre(parent)

    def _centre(self, parent: ctk.CTk) -> None:
        self.update_idletasks()
        pw = parent.winfo_width()
        ph = parent.winfo_height()
        px = parent.winfo_x()
        py = parent.winfo_y()
        dw = self.winfo_reqwidth()
        dh = self.winfo_reqheight()
        x = px + (pw - dw) // 2
        y = py + (ph - dh) // 2
        self.geometry(f"+{x}+{y}")

    def _build_ui(self) -> None:
        self.configure(fg_color="#1a1a2e")
        pad = {"padx": 32, "pady": 8}

        ctk.CTkLabel(
            self,
            text="Register New Student",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color="#e0e0e0",
        ).pack(padx=32, pady=(24, 4))

        ctk.CTkLabel(
            self,
            text=f"Card ID: {self.card_id}",
            font=ctk.CTkFont(size=12),
            text_color="#a0a0b0",
        ).pack(padx=32, pady=(0, 12))

        # First name
        ctk.CTkLabel(
            self, text="First Name *", font=ctk.CTkFont(size=13),
            text_color="#c0c0d0", anchor="w",
        ).pack(fill="x", **pad)
        self._first_name_entry = ctk.CTkEntry(
            self, placeholder_text="First name",
            width=300, height=44, font=ctk.CTkFont(size=15),
        )
        self._first_name_entry.pack(**pad)
        self._first_name_entry.focus_set()

        # Last name
        ctk.CTkLabel(
            self, text="Last Name *", font=ctk.CTkFont(size=13),
            text_color="#c0c0d0", anchor="w",
        ).pack(fill="x", **pad)
        self._last_name_entry = ctk.CTkEntry(
            self, placeholder_text="Last name",
            width=300, height=44, font=ctk.CTkFont(size=15),
        )
        self._last_name_entry.pack(**pad)

        # Optional section
        ctk.CTkLabel(
            self, text="Section (optional)", font=ctk.CTkFont(size=13),
            text_color="#c0c0d0", anchor="w",
        ).pack(fill="x", **pad)

        section_names = ["(none)"] + [s["name"] for s in self._sections]
        self._section_var = ctk.StringVar(value="(none)")
        self._section_menu = ctk.CTkOptionMenu(
            self,
            values=section_names,
            variable=self._section_var,
            width=300,
            height=40,
            font=ctk.CTkFont(size=14),
        )
        self._section_menu.pack(**pad)

        # Status label
        self._status_label = ctk.CTkLabel(
            self, text="", font=ctk.CTkFont(size=12), text_color="#ff6b6b",
        )
        self._status_label.pack(padx=32, pady=(4, 8))

        # Buttons
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(padx=32, pady=(0, 24))

        ctk.CTkButton(
            btn_frame,
            text="Cancel",
            width=140,
            height=44,
            fg_color="#374151",
            hover_color="#4b5563",
            command=self._cancel,
            font=ctk.CTkFont(size=14),
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            btn_frame,
            text="Register & Mark Present",
            width=200,
            height=44,
            fg_color="#16a34a",
            hover_color="#15803d",
            command=self._confirm,
            font=ctk.CTkFont(size=14, weight="bold"),
        ).pack(side="left")

        # Keyboard shortcuts
        self._last_name_entry.bind("<Return>", lambda _e: self._confirm())
        self.protocol("WM_DELETE_WINDOW", self._cancel)

    def _get_selected_section_id(self) -> Optional[int]:
        """Return the selected section id, or None if '(none)' is selected."""
        selected_name = self._section_var.get()
        if selected_name == "(none)":
            return None
        for s in self._sections:
            if s["name"] == selected_name:
                return s["id"]
        return None

    def _confirm(self) -> None:
        first_name = self._first_name_entry.get().strip()
        last_name  = self._last_name_entry.get().strip()
        section_id = self._get_selected_section_id()

        result = student_controller.register_new_student(
            first_name, last_name, self.card_id, section_id
        )

        if result.success:
            self.student_id = result.student_id
            log_info(
                f"Registration dialog: registered student_id={self.student_id}"
            )
            self.destroy()
        else:
            self._status_label.configure(text=result.message)

    def _cancel(self) -> None:
        self.student_id = None
        self.destroy()

"""
pin_dialog.py — Admin PIN entry dialog shown on application startup.

Shows a modal dialog that prompts for the admin PIN.
- Returns True if the correct PIN is entered.
- Returns False if the dialog is cancelled or 5 attempts are exceeded.
- If no PIN has been configured (empty string in settings), a first-time setup
  flow asks the user to create a PIN.
"""

from __future__ import annotations

import hashlib
import customtkinter as ctk
from typing import Optional

import models.settings_model as settings_model
from utils.logger import log_info, log_warning


def _hash_pin(pin: str) -> str:
    """Return SHA-256 hex digest of the PIN."""
    return hashlib.sha256(pin.encode()).hexdigest()


class PinDialog(ctk.CTkToplevel):
    """
    Modal PIN entry dialog.

    After construction call .wait_window() and check .granted to know if
    access was granted.
    """

    MAX_ATTEMPTS = 5

    def __init__(self, parent: ctk.CTk) -> None:
        super().__init__(parent)
        self.title("Admin PIN")
        self.resizable(False, False)
        self.grab_set()  # modal

        self.granted: bool = False
        self._attempts: int = 0

        stored_hash = settings_model.get_setting("admin_pin") or ""
        self._is_first_run: bool = stored_hash == ""
        self._stored_hash: str = stored_hash

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
        pad = {"padx": 30, "pady": 10}

        if self._is_first_run:
            title_text = "Create Admin PIN"
            subtitle_text = "No PIN is set. Create one to protect the application."
        else:
            title_text = "Enter Admin PIN"
            subtitle_text = "Enter your admin PIN to continue."

        ctk.CTkLabel(
            self,
            text=title_text,
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color="#e0e0e0",
        ).pack(**pad, pady=(24, 4))

        ctk.CTkLabel(
            self,
            text=subtitle_text,
            font=ctk.CTkFont(size=13),
            text_color="#a0a0b0",
        ).pack(padx=30, pady=(0, 10))

        self._pin_entry = ctk.CTkEntry(
            self,
            placeholder_text="PIN",
            show="●",
            width=220,
            height=44,
            font=ctk.CTkFont(size=16),
        )
        self._pin_entry.pack(**pad)
        self._pin_entry.focus_set()

        if self._is_first_run:
            self._confirm_entry = ctk.CTkEntry(
                self,
                placeholder_text="Confirm PIN",
                show="●",
                width=220,
                height=44,
                font=ctk.CTkFont(size=16),
            )
            self._confirm_entry.pack(**pad)
            self._confirm_entry.bind("<Return>", lambda _e: self._submit())
        else:
            self._confirm_entry = None  # type: ignore[assignment]

        self._status_label = ctk.CTkLabel(
            self,
            text="",
            font=ctk.CTkFont(size=12),
            text_color="#ff6b6b",
        )
        self._status_label.pack(padx=30, pady=(0, 6))

        btn_text = "Set PIN" if self._is_first_run else "Unlock"
        ctk.CTkButton(
            self,
            text=btn_text,
            width=220,
            height=44,
            command=self._submit,
            font=ctk.CTkFont(size=15, weight="bold"),
            fg_color="#2563eb",
            hover_color="#1d4ed8",
        ).pack(**pad, pady=(0, 24))

        self._pin_entry.bind("<Return>", lambda _e: self._submit())
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _submit(self) -> None:
        pin = self._pin_entry.get().strip()

        if not pin:
            self._status_label.configure(text="PIN cannot be empty.")
            return

        if self._is_first_run:
            confirm = self._confirm_entry.get().strip()
            if pin != confirm:
                self._status_label.configure(text="PINs do not match. Try again.")
                return
            settings_model.set_setting("admin_pin", _hash_pin(pin))
            log_info("Admin PIN created for the first time.")
            self.granted = True
            self.destroy()
            return

        # Normal login
        self._attempts += 1
        if _hash_pin(pin) == self._stored_hash:
            log_info("Admin PIN accepted.")
            self.granted = True
            self.destroy()
        else:
            remaining = self.MAX_ATTEMPTS - self._attempts
            log_warning(f"Incorrect PIN attempt {self._attempts}.")
            if remaining <= 0:
                self._status_label.configure(
                    text="Too many failed attempts. Application will close."
                )
                self.after(2000, self.destroy)
            else:
                self._status_label.configure(
                    text=f"Incorrect PIN. {remaining} attempt(s) remaining."
                )
                self._pin_entry.delete(0, "end")

    def _on_close(self) -> None:
        self.granted = False
        self.destroy()


def prompt_pin(parent: ctk.CTk) -> bool:
    """
    Show the PIN dialog and return True if access is granted.

    Args:
        parent: The root CTk window (needed for modal centring).
    """
    dlg = PinDialog(parent)
    parent.wait_window(dlg)
    return dlg.granted

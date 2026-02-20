"""
settings_tab.py — Settings tab (Phase 1 skeleton; Phase 2 full implementation).

Phase 1 provides:
- Admin PIN change
- Language placeholder
- Database info display
Full import/backup/export are Phase 2 features.
"""

from __future__ import annotations

import customtkinter as ctk
from tkinter import messagebox
import hashlib

import models.settings_model as settings_model
from utils.logger import log_info


def _hash_pin(pin: str) -> str:
    return hashlib.sha256(pin.encode()).hexdigest()


class SettingsTab(ctk.CTkFrame):
    """Settings management tab."""

    def __init__(self, parent: ctk.CTkFrame, root: ctk.CTk) -> None:
        super().__init__(parent, fg_color="#1a1a2e", corner_radius=0)
        self._app = root
        self._build_ui()

    def _build_ui(self) -> None:
        ctk.CTkLabel(
            self, text="Settings",
            font=ctk.CTkFont(size=26, weight="bold"), text_color="#e0e0e0",
        ).pack(padx=24, pady=(18, 14), anchor="w")

        # ── PIN change ───────────────────────────────────────────────────────
        pin_frame = ctk.CTkFrame(self, fg_color="#0f0f23", corner_radius=10)
        pin_frame.pack(fill="x", padx=24, pady=(0, 12))

        ctk.CTkLabel(
            pin_frame, text="Change Admin PIN",
            font=ctk.CTkFont(size=15, weight="bold"), text_color="#e0e0e0",
        ).pack(padx=16, pady=(12, 6), anchor="w")

        row1 = ctk.CTkFrame(pin_frame, fg_color="transparent")
        row1.pack(fill="x", padx=16, pady=4)
        ctk.CTkLabel(row1, text="New PIN:", width=120, font=ctk.CTkFont(size=13),
                     text_color="#c0c0d0").pack(side="left")
        self._new_pin = ctk.CTkEntry(row1, show="●", width=200, height=38,
                                     font=ctk.CTkFont(size=14))
        self._new_pin.pack(side="left", padx=(0, 8))

        row2 = ctk.CTkFrame(pin_frame, fg_color="transparent")
        row2.pack(fill="x", padx=16, pady=4)
        ctk.CTkLabel(row2, text="Confirm PIN:", width=120, font=ctk.CTkFont(size=13),
                     text_color="#c0c0d0").pack(side="left")
        self._confirm_pin = ctk.CTkEntry(row2, show="●", width=200, height=38,
                                         font=ctk.CTkFont(size=14))
        self._confirm_pin.pack(side="left", padx=(0, 8))

        self._pin_status = ctk.CTkLabel(pin_frame, text="", font=ctk.CTkFont(size=12),
                                        text_color="#ff6b6b")
        self._pin_status.pack(padx=16, pady=(0, 4))

        ctk.CTkButton(
            pin_frame, text="Save PIN", width=140, height=38,
            fg_color="#2563eb", hover_color="#1d4ed8",
            command=self._save_pin,
        ).pack(padx=16, pady=(0, 14), anchor="w")

        # ── Absence threshold ────────────────────────────────────────────────
        thresh_frame = ctk.CTkFrame(self, fg_color="#0f0f23", corner_radius=10)
        thresh_frame.pack(fill="x", padx=24, pady=(0, 12))

        ctk.CTkLabel(
            thresh_frame, text="Absence Threshold",
            font=ctk.CTkFont(size=15, weight="bold"), text_color="#e0e0e0",
        ).pack(padx=16, pady=(12, 6), anchor="w")

        thresh_row = ctk.CTkFrame(thresh_frame, fg_color="transparent")
        thresh_row.pack(fill="x", padx=16, pady=(0, 4))
        ctk.CTkLabel(thresh_row, text="Max absences before alert:", width=220,
                     font=ctk.CTkFont(size=13), text_color="#c0c0d0").pack(side="left")
        self._thresh_entry = ctk.CTkEntry(thresh_row, width=80, height=38,
                                          font=ctk.CTkFont(size=14))
        self._thresh_entry.pack(side="left", padx=(0, 8))
        current_thresh = settings_model.get_setting("absence_threshold") or "3"
        self._thresh_entry.insert(0, current_thresh)

        self._thresh_status = ctk.CTkLabel(thresh_frame, text="",
                                           font=ctk.CTkFont(size=12), text_color="#ff6b6b")
        self._thresh_status.pack(padx=16, pady=(0, 4))

        ctk.CTkButton(
            thresh_frame, text="Save Threshold", width=160, height=38,
            fg_color="#2563eb", hover_color="#1d4ed8",
            command=self._save_threshold,
        ).pack(padx=16, pady=(0, 14), anchor="w")

        # ── Phase 2 placeholders ─────────────────────────────────────────────
        ctk.CTkLabel(
            self,
            text="Google Sheets integration and database backup are available in Phase 2.",
            font=ctk.CTkFont(size=13), text_color="#4b5563",
        ).pack(padx=24, pady=12, anchor="w")

    def _save_pin(self) -> None:
        new = self._new_pin.get().strip()
        confirm = self._confirm_pin.get().strip()
        if not new:
            self._pin_status.configure(text="PIN cannot be empty.")
            return
        if new != confirm:
            self._pin_status.configure(text="PINs do not match.")
            return
        settings_model.set_setting("admin_pin", _hash_pin(new))
        self._new_pin.delete(0, "end")
        self._confirm_pin.delete(0, "end")
        self._pin_status.configure(text="PIN updated successfully.", text_color="#4ade80")
        log_info("Admin PIN changed via settings.")
        self.after(3000, lambda: self._pin_status.configure(text=""))

    def _save_threshold(self) -> None:
        val = self._thresh_entry.get().strip()
        try:
            int_val = int(val)
            if int_val < 0:
                raise ValueError
        except ValueError:
            self._thresh_status.configure(text="Please enter a positive integer.")
            return
        settings_model.set_setting("absence_threshold", str(int_val))
        self._thresh_status.configure(
            text=f"Threshold set to {int_val}.", text_color="#4ade80"
        )
        log_info(f"Absence threshold set to {int_val}.")
        self.after(3000, lambda: self._thresh_status.configure(text=""))

    def on_tab_selected(self) -> None:
        pass

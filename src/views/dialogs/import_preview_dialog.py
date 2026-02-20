"""
import_preview_dialog.py — Legacy Google Sheets import preview dialog.

Phase 2 feature. Stub created for folder completeness.
"""

from __future__ import annotations
import customtkinter as ctk


class ImportPreviewDialog(ctk.CTkToplevel):
    """Placeholder — implemented in Phase 2 (Task 2.7)."""

    def __init__(self, parent: ctk.CTk) -> None:
        super().__init__(parent)
        self.title("Import Preview")
        self.grab_set()
        ctk.CTkLabel(
            self,
            text="Import feature coming in Phase 2.",
            font=ctk.CTkFont(size=14),
        ).pack(padx=40, pady=40)
        ctk.CTkButton(self, text="Close", command=self.destroy).pack(pady=(0, 20))
        self.protocol("WM_DELETE_WINDOW", self.destroy)

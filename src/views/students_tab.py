"""
students_tab.py — Student management tab (Phase 2 Task 2.1).

Phase 1 stub: shows a placeholder message but the tab is navigable as required
by the Phase 1 exit criterion "App launches full-screen with tab navigation".
Full CRUD implementation is in Phase 2.
"""

from __future__ import annotations
import customtkinter as ctk


class StudentsTab(ctk.CTkFrame):
    """Students management tab — full implementation in Phase 2."""

    def __init__(self, parent: ctk.CTkFrame, root: ctk.CTk) -> None:
        super().__init__(parent, fg_color="#1a1a2e", corner_radius=0)
        self._app = root
        self._build_ui()

    def _build_ui(self) -> None:
        ctk.CTkLabel(
            self,
            text="Students",
            font=ctk.CTkFont(size=26, weight="bold"),
            text_color="#e0e0e0",
        ).pack(padx=24, pady=(24, 8), anchor="w")

        ctk.CTkLabel(
            self,
            text="Student management is available in Phase 2.\n"
                 "Students are created automatically when an unknown card is tapped"
                 " on the Attendance tab.",
            font=ctk.CTkFont(size=14),
            text_color="#6b7280",
            justify="left",
        ).pack(padx=24, pady=12, anchor="w")

    def on_tab_selected(self) -> None:
        pass

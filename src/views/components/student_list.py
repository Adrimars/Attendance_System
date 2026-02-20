"""
student_list.py — Reusable sortable/searchable student list widget (Phase 2).

Phase 1 stub. Full implementation with sort/search will be added during Phase 2
when the Students tab is built out.
"""

from __future__ import annotations
import customtkinter as ctk


class StudentListWidget(ctk.CTkScrollableFrame):
    """
    Reusable widget that renders a paginated, sortable, searchable student table.

    Phase 2 implementation.  Stub only for Phase 1.
    """

    def __init__(self, parent: ctk.CTkFrame, **kwargs) -> None:  # type: ignore[override]
        super().__init__(parent, **kwargs)
        ctk.CTkLabel(
            self,
            text="Student list widget — Phase 2.",
            font=ctk.CTkFont(size=13),
            text_color="#6b7280",
        ).pack(padx=16, pady=16)

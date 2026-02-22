"""
students_tab.py — Student management tab (Phase 2, Tasks 2.1 & 2.2).

Features:
• Full student list with columns: Name, RFID, Sections
• Real-time search box (filters by name or card ID)
• Sortable columns (click header → toggle asc/desc)
• Add / Edit / Delete buttons per row  +  top-level Add button
• Delegates all data mutations to student_controller
"""

from __future__ import annotations

from typing import Any, Optional

import customtkinter as ctk
from tkinter import messagebox

import controllers.student_controller as student_ctrl
from views.dialogs.student_edit_dialog import StudentEditDialog
from views.dialogs.manual_attendance_dialog import ManualAttendanceDialog
from utils.logger import log_info, log_warning


# Column definitions: (header label, dict key, display width)
_COLUMNS: list[tuple[str, str, int]] = [
    ("Name",         "full_name",      260),
    ("RFID",         "card_id",        200),
    ("Sections",     "sections",       280),
    ("Attendance %", "attendance_pct", 110),
]


class StudentsTab(ctk.CTkFrame):
    """Students management tab — fully implemented in Phase 2."""

    def __init__(self, parent: Any, root: Any) -> None:
        super().__init__(parent, fg_color="#1a1a2e", corner_radius=0)
        self._app = root

        self._all_rows: list[dict] = []       # full data from controller
        self._display_rows: list[dict] = []   # after search + sort

        self._sort_key: str = "full_name"
        self._sort_asc: bool = True
        self._search_var = ctk.StringVar()
        self._search_var.trace_add("write", self._on_search_change)

        self._build_ui()
        self._load()

    # ──────────────────────────────────────────────────────────────────────────
    # UI construction
    # ──────────────────────────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        # ── Header row ────────────────────────────────────────────────────────
        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.pack(fill="x", padx=24, pady=(18, 8))

        ctk.CTkLabel(
            hdr, text="Students",
            font=ctk.CTkFont(size=26, weight="bold"), text_color="#e0e0e0",
        ).pack(side="left")

        ctk.CTkButton(
            hdr, text="+ Add Student", width=150, height=40,
            fg_color="#2563eb", hover_color="#1d4ed8",
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self._add_student,
        ).pack(side="right", padx=4)

        # ── Search bar ────────────────────────────────────────────────────────
        search_frame = ctk.CTkFrame(self, fg_color="#0f0f23", corner_radius=8)
        search_frame.pack(fill="x", padx=24, pady=(0, 8))

        ctk.CTkLabel(
            search_frame, text="🔍", font=ctk.CTkFont(size=14), text_color="#6b7280",
        ).pack(side="left", padx=(12, 4), pady=6)

        self._search_entry = ctk.CTkEntry(
            search_frame,
            textvariable=self._search_var,
            placeholder_text="Search by name or card ID…",
            width=400, height=36,
            font=ctk.CTkFont(size=13),
            fg_color="transparent",
            border_width=0,
        )
        self._search_entry.pack(side="left", padx=(0, 12), pady=4)

        self._count_label = ctk.CTkLabel(
            search_frame, text="",
            font=ctk.CTkFont(size=12), text_color="#6b7280",
        )
        self._count_label.pack(side="right", padx=16)

        # ── Column headers ────────────────────────────────────────────────────
        self._col_hdr = ctk.CTkFrame(self, fg_color="#0f0f23", corner_radius=0)
        self._col_hdr.pack(fill="x", padx=24)
        self._col_buttons: dict[str, ctk.CTkButton] = {}

        for label, key, width in _COLUMNS:
            btn = ctk.CTkButton(
                self._col_hdr,
                text=label,
                width=width,
                height=32,
                fg_color="transparent",
                hover_color="#1e293b",
                text_color="#a0aec0",
                font=ctk.CTkFont(size=12, weight="bold"),
                anchor="w",
                command=lambda k=key: self._sort_by(k),
            )
            btn.pack(side="left", padx=4, pady=4)
            self._col_buttons[key] = btn

        # Spacer for action buttons column
        ctk.CTkLabel(
            self._col_hdr, text="", width=300,
        ).pack(side="left", padx=4)

        # ── Scrollable list ───────────────────────────────────────────────────
        self._list_frame = ctk.CTkScrollableFrame(
            self, fg_color="#111125", corner_radius=0,
        )
        self._list_frame.pack(fill="both", expand=True, padx=24, pady=(0, 24))

    # ──────────────────────────────────────────────────────────────────────────
    # Data loading + filtering
    # ──────────────────────────────────────────────────────────────────────────

    def _load(self) -> None:
        """Reload all students from DB and re-render."""
        try:
            raw = student_ctrl.get_all_students_with_sections()
        except Exception as exc:
            log_warning(f"StudentsTab: failed to load students — {exc}")
            messagebox.showerror("Error", f"Could not load students:\n{exc}", parent=self._app)
            return

        # Add a combined 'full_name' key for sorting/display
        for row in raw:
            row["full_name"] = f"{row['last_name']}, {row['first_name']}"

        self._all_rows = raw
        self._apply_filter()

    def _apply_filter(self) -> None:
        """Apply current search query + sort, then re-render."""
        query = self._search_var.get().strip().lower()

        if query:
            filtered = [
                r for r in self._all_rows
                if query in r["full_name"].lower()
                or query in r["card_id"].lower()
                or query in r["sections"].lower()
            ]
        else:
            filtered = list(self._all_rows)

        # Sort
        filtered.sort(
            key=lambda r: str(r.get(self._sort_key, "")).lower(),
            reverse=not self._sort_asc,
        )

        self._display_rows = filtered
        self._render_rows()
        self._update_sort_indicators()
        self._count_label.configure(
            text=f"{len(filtered)} of {len(self._all_rows)} student(s)"
        )

    # ──────────────────────────────────────────────────────────────────────────
    # Rendering
    # ──────────────────────────────────────────────────────────────────────────

    def _render_rows(self) -> None:
        for w in self._list_frame.winfo_children():
            w.destroy()

        if not self._display_rows:
            ctk.CTkLabel(
                self._list_frame,
                text="No students found." if self._all_rows else
                     "No students yet. Click '+ Add Student' to get started.",
                font=ctk.CTkFont(size=14), text_color="#6b7280",
            ).pack(pady=40)
            return

        for row_data in self._display_rows:
            self._render_row(row_data)

    def _render_row(self, row_data: dict) -> None:
        is_inactive = row_data.get("is_inactive", False)
        row_bg = "#2d0d0d" if is_inactive else "#1e1e35"  # dark red tint for inactive
        row = ctk.CTkFrame(
            self._list_frame, fg_color=row_bg, corner_radius=6,
        )
        row.pack(fill="x", pady=2, padx=4)

        # Name (+ INACTIVE badge if applicable)
        name_text = row_data["full_name"]
        name_color = "#ff6b6b" if is_inactive else "#e0e0e0"
        ctk.CTkLabel(
            row, text=name_text,
            font=ctk.CTkFont(size=13), text_color=name_color,
            width=260, anchor="w",
        ).pack(side="left", padx=(12, 4), pady=8)

        # RFID
        rfid_text  = row_data["card_id"] if row_data["card_id"] else "—"
        rfid_color = "#d0d0e0" if row_data["card_id"] else "#4b5563"
        ctk.CTkLabel(
            row, text=rfid_text,
            font=ctk.CTkFont(size=12), text_color=rfid_color,
            width=200, anchor="w",
        ).pack(side="left", padx=4)

        # Sections
        ctk.CTkLabel(
            row, text=row_data["sections"],
            font=ctk.CTkFont(size=12), text_color="#9ca3af",
            width=280, anchor="w",
        ).pack(side="left", padx=4)

        # Attendance %
        pct_text  = row_data.get("attendance_pct", "—")
        pct_color = "#4ade80" if not is_inactive else "#f87171"
        ctk.CTkLabel(
            row, text=pct_text,
            font=ctk.CTkFont(size=12, weight="bold"), text_color=pct_color,
            width=110, anchor="w",
        ).pack(side="left", padx=4)

        # Action buttons
        btn_frame = ctk.CTkFrame(row, fg_color="transparent", width=296)
        btn_frame.pack(side="right", padx=8)
        btn_frame.pack_propagate(False)

        ctk.CTkButton(
            btn_frame, text="Attendance", width=94, height=32,
            fg_color="#065f46", hover_color="#047857",
            font=ctk.CTkFont(size=12),
            command=lambda sid=row_data["id"], n=row_data["full_name"]:
                self._open_attendance_dialog(sid, n),
        ).pack(side="left", padx=(0, 4))

        ctk.CTkButton(
            btn_frame, text="Edit", width=86, height=32,
            fg_color="#374151", hover_color="#4b5563",
            font=ctk.CTkFont(size=12),
            command=lambda sid=row_data["id"]: self._edit_student(sid),
        ).pack(side="left", padx=(0, 4))

        ctk.CTkButton(
            btn_frame, text="Delete", width=86, height=32,
            fg_color="#7f1d1d", hover_color="#991b1b",
            font=ctk.CTkFont(size=12),
            command=lambda sid=row_data["id"], n=row_data["full_name"]:
                self._delete_student(sid, n),
        ).pack(side="left")

    # ──────────────────────────────────────────────────────────────────────────
    # Sort helpers
    # ──────────────────────────────────────────────────────────────────────────

    def _sort_by(self, key: str) -> None:
        if self._sort_key == key:
            self._sort_asc = not self._sort_asc
        else:
            self._sort_key = key
            self._sort_asc = True
        self._apply_filter()

    def _update_sort_indicators(self) -> None:
        for key, btn in self._col_buttons.items():
            label = next(
                (lbl for lbl, k, _ in _COLUMNS if k == key), key
            )
            if key == self._sort_key:
                arrow = " ▲" if self._sort_asc else " ▼"
                btn.configure(text=label + arrow, text_color="#e0e0e0")
            else:
                btn.configure(text=label, text_color="#a0aec0")

    # ──────────────────────────────────────────────────────────────────────────
    # CRUD actions
    # ──────────────────────────────────────────────────────────────────────────

    def _add_student(self) -> None:
        dlg = StudentEditDialog(self._app, student_id=None)
        self._app.wait_window(dlg)
        if dlg.saved:
            self._load()

    def _edit_student(self, student_id: int) -> None:
        dlg = StudentEditDialog(self._app, student_id=student_id)
        self._app.wait_window(dlg)
        if dlg.saved:
            self._load()

    def _open_attendance_dialog(self, student_id: int, full_name: str) -> None:
        dlg = ManualAttendanceDialog(self._app, student_id, full_name)
        self._app.wait_window(dlg)

    def _delete_student(self, student_id: int, full_name: str) -> None:
        if not messagebox.askyesno(
            "Delete Student",
            f"Delete student '{full_name}'?\n\n"
            "All their attendance records will also be permanently deleted.",
            parent=self._app,
        ):
            return

        ok, msg = student_ctrl.delete_student(student_id)
        if ok:
            log_info(f"StudentsTab: deleted student_id={student_id} '{full_name}'")
            self._load()
        else:
            messagebox.showerror("Error", msg, parent=self._app)

    # ──────────────────────────────────────────────────────────────────────────
    # Event callbacks
    # ──────────────────────────────────────────────────────────────────────────

    def _on_search_change(self, *_args: object) -> None:
        """Called whenever the search box text changes."""
        self._apply_filter()

    # ──────────────────────────────────────────────────────────────────────────
    # Public hook
    # ──────────────────────────────────────────────────────────────────────────

    def on_tab_selected(self) -> None:
        """Called by App when this tab becomes active — reload data."""
        self._load()


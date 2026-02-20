"""
attendance_tab.py — Main attendance screen (Tasks 1.13, 1.15).

Features:
- Section selector dropdown
- Start / End Session buttons
- Hidden RFID Entry widget (always focused; fires on Enter key)
- Live student list with name + colour-coded status
- Green/Red/Yellow background flash (2 s) on card tap
- Manual attendance toggle (click row → toggles; method = 'Manual')
- Triggers Registration Dialog on unknown card
- Triggers Session Summary Dialog on End Session
"""

from __future__ import annotations

from typing import Optional
import customtkinter as ctk

import controllers.attendance_controller as attendance_ctrl
import controllers.session_controller as session_ctrl
import controllers.section_controller as section_ctrl
from controllers.attendance_controller import TapResultType
from controllers.session_controller import SessionSummary
from views.dialogs.registration_dialog import RegistrationDialog
from views.dialogs.session_summary_dialog import SessionSummaryDialog
from utils.logger import log_info, log_error, log_warning

# ── Flash colours ────────────────────────────────────────────────────────────
_FLASH_GREEN  = "#166534"   # known student → present
_FLASH_RED    = "#7f1d1d"   # unknown card
_FLASH_YELLOW = "#713f12"   # duplicate tap
_BASE_BG      = "#1a1a2e"   # default background
_FLASH_MS     = 2500         # flash duration in milliseconds


class AttendanceTab(ctk.CTkFrame):
    """The Attendance tab mounted inside the main App tabview."""

    def __init__(self, parent: ctk.CTkFrame, root: ctk.CTk) -> None:
        super().__init__(parent, fg_color=_BASE_BG, corner_radius=0)
        self._app = root
        self._session_id: Optional[int] = None
        self._flash_job: Optional[str] = None   # after() job id

        self._build_ui()
        self._refresh_sections()

    # ──────────────────────────────────────────────────────────────────────────
    # UI construction
    # ──────────────────────────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        # ── Top bar ──────────────────────────────────────────────────────────
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", padx=24, pady=(18, 8))

        ctk.CTkLabel(
            top,
            text="Attendance",
            font=ctk.CTkFont(size=26, weight="bold"),
            text_color="#e0e0e0",
        ).pack(side="left")

        # ── Session controls ─────────────────────────────────────────────────
        ctrl_frame = ctk.CTkFrame(self, fg_color="#0f0f23", corner_radius=10)
        ctrl_frame.pack(fill="x", padx=24, pady=(0, 10))

        ctk.CTkLabel(
            ctrl_frame,
            text="Section:",
            font=ctk.CTkFont(size=14),
            text_color="#c0c0d0",
        ).pack(side="left", padx=(16, 8), pady=10)

        self._section_var = ctk.StringVar(value="— select section —")
        self._section_menu = ctk.CTkOptionMenu(
            ctrl_frame,
            variable=self._section_var,
            values=["— select section —"],
            width=260,
            height=40,
            font=ctk.CTkFont(size=14),
            command=self._on_section_changed,
        )
        self._section_menu.pack(side="left", padx=(0, 12), pady=10)

        self._start_btn = ctk.CTkButton(
            ctrl_frame,
            text="▶  Start Session",
            width=160,
            height=40,
            fg_color="#16a34a",
            hover_color="#15803d",
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self._start_session,
        )
        self._start_btn.pack(side="left", padx=(0, 8), pady=10)

        self._end_btn = ctk.CTkButton(
            ctrl_frame,
            text="■  End Session",
            width=160,
            height=40,
            fg_color="#dc2626",
            hover_color="#b91c1c",
            font=ctk.CTkFont(size=14, weight="bold"),
            state="disabled",
            command=self._end_session,
        )
        self._end_btn.pack(side="left", padx=(0, 16), pady=10)

        self._session_label = ctk.CTkLabel(
            ctrl_frame,
            text="No active session",
            font=ctk.CTkFont(size=12),
            text_color="#6b7280",
        )
        self._session_label.pack(side="left", padx=(0, 16))

        # ── Feedback banner (flash area) ─────────────────────────────────────
        self._banner = ctk.CTkFrame(self, fg_color=_BASE_BG, corner_radius=8, height=70)
        self._banner.pack(fill="x", padx=24, pady=(0, 10))
        self._banner.pack_propagate(False)

        self._feedback_label = ctk.CTkLabel(
            self._banner,
            text="Tap a card to record attendance",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color="#c0c0d0",
        )
        self._feedback_label.pack(expand=True)

        # ── Hidden RFID input ─────────────────────────────────────────────────
        # Invisible entry widget; card reader fires Enter → triggers _on_rfid_enter
        self._rfid_entry = ctk.CTkEntry(
            self,
            width=1,
            height=1,
            fg_color=_BASE_BG,
            border_width=0,
            text_color=_BASE_BG,
        )
        self._rfid_entry.pack()
        self._rfid_entry.bind("<Return>", self._on_rfid_enter)
        # Keep focus on the hidden entry so card reads are always captured
        self._rfid_entry.bind("<FocusOut>", self._reclaim_focus)
        # Also bind tab/click anywhere on frame to restore focus
        self.bind("<Button-1>", lambda _e: self._rfid_entry.focus_set())
        self._rfid_entry.focus_set()

        # ── Student list ──────────────────────────────────────────────────────
        list_header = ctk.CTkFrame(self, fg_color="#0f0f23", corner_radius=0)
        list_header.pack(fill="x", padx=24)

        for col, width in [("Student", 300), ("Card ID", 180), ("Status", 120), ("Method", 90)]:
            ctk.CTkLabel(
                list_header,
                text=col,
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color="#6b7280",
                width=width,
                anchor="w",
            ).pack(side="left", padx=8, pady=6)

        self._list_frame = ctk.CTkScrollableFrame(
            self,
            fg_color="#111125",
            corner_radius=0,
        )
        self._list_frame.pack(fill="both", expand=True, padx=24, pady=(0, 24))
        self._student_rows: list[ctk.CTkFrame] = []

    # ──────────────────────────────────────────────────────────────────────────
    # Data helpers
    # ──────────────────────────────────────────────────────────────────────────

    def _refresh_sections(self) -> None:
        """Reload section dropdown from DB."""
        sections = section_ctrl.get_all_sections()
        self._sections = sections
        if sections:
            names = [s["name"] for s in sections]
            self._section_menu.configure(values=names)
            self._section_var.set(names[0])
        else:
            self._section_menu.configure(values=["— no sections —"])
            self._section_var.set("— no sections —")

    def _get_selected_section_id(self) -> Optional[int]:
        """Return the id of the currently selected section, or None."""
        name = self._section_var.get()
        for s in self._sections:
            if s["name"] == name:
                return s["id"]
        return None

    # ──────────────────────────────────────────────────────────────────────────
    # Event handlers
    # ──────────────────────────────────────────────────────────────────────────

    def _on_section_changed(self, _value: str) -> None:
        if self._session_id is None:
            self._clear_student_list()

    def _start_session(self) -> None:
        section_id = self._get_selected_section_id()
        if section_id is None:
            self._show_error("Please select a section before starting a session.")
            return

        result = session_ctrl.start_session(section_id)
        if result.success:
            self._session_id = result.session_id
            self._start_btn.configure(state="disabled")
            self._end_btn.configure(state="normal")
            self._section_menu.configure(state="disabled")
            self._session_label.configure(
                text=f"Session #{self._session_id} active",
                text_color="#4ade80",
            )
            self._refresh_student_list()
            self._rfid_entry.focus_set()
            log_info(f"AttendanceTab: session {self._session_id} started.")
        else:
            self._show_error(result.message)

    def _end_session(self) -> None:
        if self._session_id is None:
            return

        summary: Optional[SessionSummary] = session_ctrl.end_session(self._session_id)
        if summary is None:
            self._show_error("Failed to generate session summary. Check the logs.")
            return

        # Show summary dialog BEFORE actually committing the close
        # (the summary dialog allows last-minute toggles; end_session already
        #  wrote absent records, so the dialog toggles are live in DB)
        dlg = SessionSummaryDialog(
            self._app,
            summary,
            on_confirm=None,  # session already closed by session_ctrl.end_session
        )
        self._app.wait_window(dlg)

        if dlg.confirmed:
            self._session_id = None
            self._start_btn.configure(state="normal")
            self._end_btn.configure(state="disabled")
            self._section_menu.configure(state="normal")
            self._session_label.configure(
                text="No active session", text_color="#6b7280"
            )
            self._clear_student_list()
            self._flash(_BASE_BG, "Session closed.")
        else:
            # User cancelled — the session was already closed in DB.
            # Re-open it by updating status back to active would be complex;
            # instead log a warning. The session is finalized either way.
            log_warning(
                "End session dialog cancelled but session was already closed in DB."
            )
            self._session_id = None
            self._start_btn.configure(state="normal")
            self._end_btn.configure(state="disabled")
            self._section_menu.configure(state="normal")
            self._session_label.configure(
                text="No active session", text_color="#6b7280"
            )
            self._clear_student_list()

    def _on_rfid_enter(self, _event: object) -> None:
        """Fired when the RFID reader sends Enter after the card ID."""
        card_id = self._rfid_entry.get().strip()
        self._rfid_entry.delete(0, "end")

        if not card_id:
            return

        tap_result = attendance_ctrl.process_card_tap(card_id, self._session_id)

        if tap_result.result_type == TapResultType.KNOWN_PRESENT:
            self._flash(_FLASH_GREEN, tap_result.message)
            self._refresh_student_list()

        elif tap_result.result_type == TapResultType.DUPLICATE_TAP:
            self._flash(_FLASH_YELLOW, tap_result.message)

        elif tap_result.result_type == TapResultType.UNKNOWN_CARD:
            self._flash(_FLASH_RED, "Unknown card — please register the student.")
            self._open_registration(card_id)

        elif tap_result.result_type == TapResultType.NO_SESSION:
            self._set_feedback("⚠  Start a session first.", "#f59e0b")

        elif tap_result.result_type == TapResultType.ERROR:
            self._flash(_BASE_BG, "")
            self._show_error(tap_result.message)

        self._rfid_entry.focus_set()

    def _reclaim_focus(self, _event: object) -> None:
        """Re-focus hidden entry after a tiny delay (lets dialog open first)."""
        self.after(100, self._rfid_entry.focus_set)

    # ──────────────────────────────────────────────────────────────────────────
    # Registration dialog
    # ──────────────────────────────────────────────────────────────────────────

    def _open_registration(self, card_id: str) -> None:
        dlg = RegistrationDialog(self._app, card_id)
        self._app.wait_window(dlg)

        if dlg.student_id is not None and self._session_id is not None:
            success = attendance_ctrl.record_attendance_after_registration(
                self._session_id, dlg.student_id
            )
            if success:
                self._flash(_FLASH_GREEN, "Student registered and marked present.")
                self._refresh_student_list()
            else:
                self._show_error("Registration succeeded but attendance could not be recorded.")
        else:
            self._flash(_BASE_BG, "Registration cancelled.")

        self._rfid_entry.focus_set()

    # ──────────────────────────────────────────────────────────────────────────
    # Student list rendering + manual toggle (Task 1.15)
    # ──────────────────────────────────────────────────────────────────────────

    def _clear_student_list(self) -> None:
        for row in self._student_rows:
            row.destroy()
        self._student_rows.clear()

    def _refresh_student_list(self) -> None:
        self._clear_student_list()
        if self._session_id is None:
            return

        records = session_ctrl.get_live_attendance(self._session_id)
        for rec in records:
            self._add_student_row(rec)

    def _add_student_row(self, rec: dict) -> None:
        status: str   = rec["status"]
        method: str   = rec.get("method", "")
        student_id: int = rec["student_id"]

        # Row background based on status
        if status == "Present":
            row_fg = "#0d2b0d"
        elif status == "Absent":
            row_fg = "#2b0d0d"
        else:
            row_fg = "#1e1e35"

        row = ctk.CTkFrame(self._list_frame, fg_color=row_fg, corner_radius=6)
        row.pack(fill="x", pady=2, padx=4)
        self._student_rows.append(row)

        # Name
        ctk.CTkLabel(
            row,
            text=f"{rec['last_name']}, {rec['first_name']}",
            font=ctk.CTkFont(size=14),
            text_color="#e0e0e0",
            width=300,
            anchor="w",
        ).pack(side="left", padx=8, pady=6)

        # Card ID
        ctk.CTkLabel(
            row,
            text=rec.get("card_id") or "—",
            font=ctk.CTkFont(size=12),
            text_color="#9ca3af",
            width=180,
            anchor="w",
        ).pack(side="left", padx=8)

        # Status label (colour-coded)
        status_color = "#4ade80" if status == "Present" else (
            "#f87171" if status == "Absent" else "#9ca3af"
        )
        ctk.CTkLabel(
            row,
            text=status,
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=status_color,
            width=120,
            anchor="w",
        ).pack(side="left", padx=8)

        # Method
        ctk.CTkLabel(
            row,
            text=method or "—",
            font=ctk.CTkFont(size=11),
            text_color="#6b7280",
            width=90,
            anchor="w",
        ).pack(side="left", padx=8)

        # Manual toggle button (Task 1.15)
        if self._session_id is not None:
            toggle_text = "Mark Absent" if status == "Present" else "Mark Present"
            toggle_color = "#374151" if status == "Present" else "#1d4ed8"
            ctk.CTkButton(
                row,
                text=toggle_text,
                width=110,
                height=32,
                fg_color=toggle_color,
                hover_color="#4b5563",
                font=ctk.CTkFont(size=12),
                command=lambda sid=student_id: self._manual_toggle(sid),
            ).pack(side="right", padx=8)

    def _manual_toggle(self, student_id: int) -> None:
        """Manual attendance toggle for a student row (sets method='Manual')."""
        if self._session_id is None:
            return
        new_status = attendance_ctrl.toggle_attendance(self._session_id, student_id)
        if new_status is None:
            self._show_error("Could not toggle attendance. The student may not have an attendance record yet. Tap the card first, or ensure the student is enrolled in this section.")
        else:
            self._refresh_student_list()
        self._rfid_entry.focus_set()

    # ──────────────────────────────────────────────────────────────────────────
    # Flash / feedback helpers
    # ──────────────────────────────────────────────────────────────────────────

    def _flash(self, colour: str, message: str) -> None:
        """Flash the banner background for _FLASH_MS milliseconds."""
        if self._flash_job is not None:
            try:
                self.after_cancel(self._flash_job)
            except Exception:
                pass
            self._flash_job = None

        self._banner.configure(fg_color=colour)
        self._feedback_label.configure(text=message)

        if colour != _BASE_BG:
            self._flash_job = self.after(
                _FLASH_MS, lambda: self._flash(_BASE_BG, "Tap a card to record attendance")
            )

    def _set_feedback(self, message: str, colour: str = "#c0c0d0") -> None:
        self._feedback_label.configure(text=message, text_color=colour)

    def _show_error(self, message: str) -> None:
        from tkinter import messagebox
        messagebox.showerror("Error", message, parent=self._app)

    # ──────────────────────────────────────────────────────────────────────────
    # Public hook  (called by App when this tab is selected)
    # ──────────────────────────────────────────────────────────────────────────

    def on_tab_selected(self) -> None:
        """Called by App whenever the Attendance tab becomes active."""
        self._refresh_sections()
        self._rfid_entry.focus_set()

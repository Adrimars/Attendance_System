"""
attendance_tab.py — Passive attendance screen (Phase 3 redesign).

Always-on RFID listening — no manual session start/end required.

Behaviour on RFID tap:
  * Known card  -> mark student Present in every section they are enrolled in
                   that is scheduled for today.  Green flash.
  * Duplicate   -> student already fully marked today.  Yellow flash.
  * Unknown card -> open RegistrationDialog so the student can be added and
                   their card paired immediately.  Red flash.

The "Today's Log" list refreshes after every tap, showing all attendance
records created during the current calendar day.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Optional

import customtkinter as ctk

import controllers.attendance_controller as attendance_ctrl
import controllers.section_controller as section_ctrl
from controllers.attendance_controller import TapResultType, PassiveTapResult
from views.dialogs.registration_dialog import RegistrationDialog
from views.dialogs.section_assign_dialog import SectionAssignDialog
from utils.logger import log_info, log_error, log_warning

# -- Colour palette -------------------------------------------------------
_FLASH_GREEN  = "#166534"
_FLASH_RED    = "#7f1d1d"
_FLASH_YELLOW = "#713f12"
_BASE_BG      = "#1a1a2e"
_FLASH_MS     = 2500


class AttendanceTab(ctk.CTkFrame):
    """The Attendance tab -- mounted directly in the main App window."""

    def __init__(self, parent: Any, root: Any) -> None:
        super().__init__(parent, fg_color=_BASE_BG, corner_radius=0)
        self._app  = root
        self._flash_job: Optional[str] = None

        self._build_ui()
        self._refresh_today_sections()
        self._refresh_log()

    # -------------------------------------------------------------------------
    # UI construction
    # -------------------------------------------------------------------------

    def _build_ui(self) -> None:
        # -- Title bar --------------------------------------------------------
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", padx=24, pady=(18, 4))

        ctk.CTkLabel(
            top,
            text="Attendance",
            font=ctk.CTkFont(size=26, weight="bold"),
            text_color="#e0e0e0",
        ).pack(side="left")

        self._date_lbl = ctk.CTkLabel(
            top,
            text=self._today_label(),
            font=ctk.CTkFont(size=14),
            text_color="#6b7280",
        )
        self._date_lbl.pack(side="right")

        # -- Today's sections info bar ----------------------------------------
        self._sections_bar = ctk.CTkFrame(
            self, fg_color="#0f0f23", corner_radius=8, height=44,
        )
        self._sections_bar.pack(fill="x", padx=24, pady=(0, 6))
        self._sections_bar.pack_propagate(False)

        self._sections_lbl = ctk.CTkLabel(
            self._sections_bar,
            text="Loading sections...",
            font=ctk.CTkFont(size=13),
            text_color="#a0a0b0",
        )
        self._sections_lbl.pack(side="left", padx=14)

        # Listening status indicator (right side of sections bar)
        self._listen_dot = ctk.CTkLabel(
            self._sections_bar,
            text="● LISTENING",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#4ade80",
        )
        self._listen_dot.pack(side="right", padx=14)

        # [SIMULATION] Toggle button — remove this button to hide the feature
        #DELETABLE !!!!!
        self._sim_toggle_btn = ctk.CTkButton(
            self._sections_bar,
            text="💻  Sim",
            width=72, height=28,
            fg_color="#78350f", hover_color="#92400e",
            font=ctk.CTkFont(size=11),
            command=self._toggle_sim_panel,
        )
        self._sim_toggle_btn.pack(side="right", padx=(0, 6), pady=8)

        # -- Feedback / flash banner -------------------------------------------
        self._banner = ctk.CTkFrame(self, fg_color=_BASE_BG, corner_radius=8, height=80)
        self._banner.pack(fill="x", padx=24, pady=(0, 8))
        self._banner.pack_propagate(False)

        self._feedback_lbl = ctk.CTkLabel(
            self._banner,
            text="Waiting for card tap...",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color="#c0c0d0",
        )
        self._feedback_lbl.pack(expand=True)

        # -- Hidden RFID capture entry ----------------------------------------
        self._rfid_entry = ctk.CTkEntry(
            self, width=1, height=1,
            fg_color=_BASE_BG, border_width=0, text_color=_BASE_BG,
        )
        self._rfid_entry.pack()
        self._rfid_entry.bind("<Return>", self._on_rfid_enter)
        self._rfid_entry.bind("<FocusIn>",  lambda _e: self._set_listening(True))
        self._rfid_entry.bind("<FocusOut>", self._on_rfid_focus_out)
        self.bind("<Button-1>", lambda _e: self._rfid_entry.focus_set())
        self._rfid_entry.focus_set()

        # -- [SIMULATION] Panel (hidden by default) ---------------------------
        #DELETABLE!!!
        # To REMOVE simulation entirely: delete _build_sim_panel() call here
        # and delete the _build_sim_panel / _toggle_sim_panel / _sim_submit methods.
        self._build_sim_panel()

        # -- Today's log list -------------------------------------------------
        self._log_hdr = ctk.CTkFrame(self, fg_color="#0f0f23", corner_radius=0)
        self._log_hdr.pack(fill="x", padx=24)

        for col, width in [
            ("Student",  280),
            ("Section",  220),
            ("Status",    90),
            ("Method",    80),
            ("Time",     130),
        ]:
            ctk.CTkLabel(
                self._log_hdr, text=col,
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color="#6b7280", width=width, anchor="w",
            ).pack(side="left", padx=8, pady=6)

        self._log_frame = ctk.CTkScrollableFrame(
            self, fg_color="#111125", corner_radius=0,
        )
        self._log_frame.pack(fill="both", expand=True, padx=24, pady=(0, 24))

    # -------------------------------------------------------------------------
    # Data helpers
    # -------------------------------------------------------------------------

    @staticmethod
    def _today_label() -> str:
        return datetime.now().strftime("%A, %d %B %Y")

    @staticmethod
    def _today_date() -> str:
        return date.today().isoformat()

    def _refresh_today_sections(self) -> None:
        """Update the sections info bar with sections scheduled for today."""
        today_day = datetime.now().strftime("%A")
        all_secs  = section_ctrl.get_all_sections()
        today_secs = [
            s for s in all_secs
            if s["day"].strip().lower() == today_day.lower()
        ]
        if today_secs:
            names = ",  ".join(
                f"{s['name']} ({s['time']})" for s in today_secs
            )
            text = f"Today ({today_day}):  {names}"
        else:
            text = f"No sections scheduled for today ({today_day})"
        self._sections_lbl.configure(text=text)

    def _refresh_log(self) -> None:
        """Rebuild the today's-log list from the DB."""
        for w in self._log_frame.winfo_children():
            w.destroy()

        records = attendance_ctrl.get_today_log()
        if not records:
            ctk.CTkLabel(
                self._log_frame,
                text="No taps recorded today.",
                font=ctk.CTkFont(size=13),
                text_color="#6b7280",
            ).pack(pady=20)
            return

        for rec in records:
            self._add_log_row(rec)

    def _add_log_row(self, rec: dict) -> None:
        status = rec["status"]
        row_fg = (
            "#0d2b0d" if status == "Present" else
            "#2b0d0d" if status == "Absent"  else
            "#1e1e35"
        )
        row = ctk.CTkFrame(self._log_frame, fg_color=row_fg, corner_radius=6)
        row.pack(fill="x", pady=2, padx=4)

        ctk.CTkLabel(
            row,
            text=f"{rec['last_name']}, {rec['first_name']}",
            font=ctk.CTkFont(size=14), text_color="#e0e0e0",
            width=280, anchor="w",
        ).pack(side="left", padx=8, pady=6)

        ctk.CTkLabel(
            row,
            text=rec.get("section_name", "---"),
            font=ctk.CTkFont(size=13), text_color="#93c5fd",
            width=220, anchor="w",
        ).pack(side="left", padx=8)

        status_color = "#4ade80" if status == "Present" else "#f87171"
        ctk.CTkLabel(
            row,
            text=status,
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=status_color, width=90, anchor="w",
        ).pack(side="left", padx=8)

        ctk.CTkLabel(
            row,
            text=rec.get("method", "---") or "---",
            font=ctk.CTkFont(size=11), text_color="#6b7280",
            width=80, anchor="w",
        ).pack(side="left", padx=8)

        ts = rec.get("timestamp", "")
        try:
            from datetime import timezone
            dt = datetime.fromisoformat(ts).astimezone(timezone.utc).astimezone()
            ts_str = dt.strftime("%H:%M:%S")
        except Exception:
            ts_str = ts[:19] if ts else "---"

        ctk.CTkLabel(
            row,
            text=ts_str,
            font=ctk.CTkFont(size=12), text_color="#9ca3af",
            width=130, anchor="w",
        ).pack(side="left", padx=8)

    # -------------------------------------------------------------------------
    # RFID event handler
    # -------------------------------------------------------------------------

    # =========================================================================
    #DELETABLE SIMULATION CODE BLOCK STARTS HERE !!!
    # [SIMULATION] — keyboard emulation of RFID hardware
    # To remove: delete _build_sim_panel() call in _build_ui(), delete this
    # entire block, and delete the "Sim" button lines in _build_ui().
    # =========================================================================

    def _build_sim_panel(self) -> None:
        """Build the simulation input panel (hidden by default)."""
        self._sim_panel = ctk.CTkFrame(
            self, fg_color="#1c0f00", corner_radius=8, border_width=1,
            border_color="#92400e",
        )
        # NOT packed yet — shown only when toggled on

        ctk.CTkLabel(
            self._sim_panel,
            text="⚠  SIMULATION MODE — type a 10-digit card ID and press Enter",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#fbbf24",
        ).pack(side="left", padx=14, pady=8)

        self._sim_entry = ctk.CTkEntry(
            self._sim_panel,
            placeholder_text="0000000000",
            width=160, height=32,
            font=ctk.CTkFont(size=14),
        )
        self._sim_entry.pack(side="left", padx=(0, 8), pady=8)
        self._sim_entry.bind("<Return>", self._sim_submit)

        ctk.CTkButton(
            self._sim_panel,
            text="Tap",
            width=60, height=32,
            fg_color="#2563eb", hover_color="#1d4ed8",
            command=self._sim_submit,
        ).pack(side="left", pady=8)

        self._sim_visible = False

    def _toggle_sim_panel(self) -> None:
        self._sim_visible = not self._sim_visible
        if self._sim_visible:
            # Insert panel between the hidden RFID entry and the log header
            self._sim_panel.pack(fill="x", padx=24, pady=(0, 6), before=self._log_hdr)
            self._sim_toggle_btn.configure(fg_color="#92400e")
            self._sim_entry.focus_set()
        else:
            self._sim_panel.pack_forget()
            self._sim_toggle_btn.configure(fg_color="#78350f")
            self._rfid_entry.focus_set()

    def _sim_submit(self, _event: object = None) -> None:
        """Process a manually typed card ID exactly like a hardware tap."""
        card_id = self._sim_entry.get().strip()
        self._sim_entry.delete(0, "end")
        if not card_id:
            self._sim_entry.focus_set()
            return

        if not (card_id.isdigit() and len(card_id) == 10):
            self._flash(_FLASH_RED, f"Sim: invalid format '{card_id}'  (10 digits required)")
            self._sim_entry.focus_set()
            return

        # Call processing logic directly — never touch _rfid_entry focus from here
        self._process_card(card_id)
        self._sim_entry.focus_set()

    # =========================================================================
    # [END SIMULATION]
    # =========================================================================

    # -------------------------------------------------------------------------
    # Focus management
    # -------------------------------------------------------------------------

    def _on_rfid_focus_out(self, _event: object) -> None:
        """Called whenever the hidden RFID entry loses focus."""
        self._set_listening(False)
        # Only try to reclaim focus when sim panel is hidden AND no modal is open
        if not getattr(self, "_sim_visible", False):
            self.after(200, self._try_refocus)

    def _try_refocus(self) -> None:
        """Give focus back to the RFID entry unless something else needs it."""
        if getattr(self, "_sim_visible", False):
            return  # sim panel is handling focus
        try:
            # grab_current() is non-None when a modal dialog (AdminPanel, etc.) is open
            if self.winfo_toplevel().grab_current() is not None:
                self.after(500, self._try_refocus)  # wait and retry
                return
            self._rfid_entry.focus_set()
        except Exception as exc:
            log_warning(f"_try_refocus failed: {exc}")

    def _set_listening(self, active: bool) -> None:
        if active:
            self._listen_dot.configure(text="● LISTENING", text_color="#4ade80")
        else:
            self._listen_dot.configure(text="◌ IDLE",      text_color="#6b7280")

    # -------------------------------------------------------------------------
    # RFID / card processing
    # -------------------------------------------------------------------------

    def _on_rfid_enter(self, _event: object) -> None:
        """Fired when the RFID reader sends Enter after the card data."""
        card_id = self._rfid_entry.get().strip()
        self._rfid_entry.delete(0, "end")
        if not card_id:
            return
        # ── 10-digit guard ───────────────────────────────────────────
        if not (card_id.isdigit() and len(card_id) == 10):
            self._flash(_FLASH_RED, f"Invalid card format: '{card_id}'  (expected 10 digits)")
            return
        self._process_card(card_id)

    def _process_card(self, card_id: str) -> None:
        """Shared processing logic for both hardware taps and simulation."""
        result = attendance_ctrl.process_rfid_passive(card_id)

        if result.result_type == TapResultType.KNOWN_PRESENT:
            self._flash(_FLASH_GREEN, result.message)
            self._refresh_log()

        elif result.result_type == TapResultType.DUPLICATE_TAP:
            self._flash(_FLASH_YELLOW, result.message)

        elif result.result_type == TapResultType.UNKNOWN_CARD:
            self._flash(_FLASH_RED, "Unknown card -- please complete registration.")
            self._open_registration(card_id)

        elif result.result_type == TapResultType.NO_SECTIONS:
            self._flash(_FLASH_YELLOW, result.message)
            self._open_section_assign(result)

        elif result.result_type == TapResultType.ERROR:
            self._flash(_BASE_BG, "")
            from tkinter import messagebox
            messagebox.showerror("Tap Error", result.message, parent=self._app)

    # -------------------------------------------------------------------------
    # Section assignment (known student, no sections enrolled)
    # -------------------------------------------------------------------------

    def _open_section_assign(self, tap_result: PassiveTapResult) -> None:
        """Open the section assignment dialog for a student with zero enrolments."""
        # Guard: these are always set for NO_SECTIONS results
        if tap_result.student_id is None or not tap_result.first_name or not tap_result.last_name:
            return
        dlg = SectionAssignDialog(
            self._app,
            student_id=tap_result.student_id,
            first_name=tap_result.first_name,
            last_name=tap_result.last_name,
        )
        self._app.wait_window(dlg)

        if dlg.confirmed and dlg.section_ids:
            marked = attendance_ctrl.mark_present_for_enrolled_sections(
                tap_result.student_id, dlg.section_ids
            )
            if marked:
                self._flash(
                    _FLASH_GREEN,
                    f"{tap_result.first_name} {tap_result.last_name} — "
                    f"sections assigned & marked present in {len(marked)} section(s).",
                )
            else:
                self._flash(_FLASH_GREEN, "Sections assigned.")
            self._refresh_log()
            self._refresh_today_sections()
        else:
            self._flash(_BASE_BG, "Section assignment skipped.")

        if getattr(self, "_sim_visible", False):
            self._sim_entry.focus_set()
        else:
            self._rfid_entry.focus_set()

    # -------------------------------------------------------------------------
    # Registration
    # -------------------------------------------------------------------------

    def _open_registration(self, card_id: str) -> None:
        dlg = RegistrationDialog(self._app, card_id)
        self._app.wait_window(dlg)

        if dlg.student_id is not None:
            # Mark the student present in every section they enrolled in right now
            # (all enrolled sections for today, not filtered by day-of-week).
            marked = attendance_ctrl.mark_present_for_enrolled_sections(
                dlg.student_id, dlg.section_ids
            )
            if marked:
                self._flash(
                    _FLASH_GREEN,
                    f"Registered & marked present in {len(marked)} section(s).",
                )
            else:
                self._flash(_FLASH_GREEN, "Student registered.")
            self._refresh_log()
            self._refresh_today_sections()
        else:
            self._flash(_BASE_BG, "Registration cancelled.")

        # Restore appropriate focus after dialog closes
        if getattr(self, "_sim_visible", False):
            self._sim_entry.focus_set()
        else:
            self._rfid_entry.focus_set()

    # -------------------------------------------------------------------------
    # Flash banner
    # -------------------------------------------------------------------------

    def _flash(self, colour: str, message: str) -> None:
        if self._flash_job:
            self.after_cancel(self._flash_job)
        self._banner.configure(fg_color=colour)
        self._feedback_lbl.configure(text=message)
        self._flash_job = self.after(_FLASH_MS, self._reset_banner)

    def _reset_banner(self) -> None:
        self._banner.configure(fg_color=_BASE_BG)
        self._feedback_lbl.configure(
            text="Waiting for card tap...", text_color="#c0c0d0"
        )
        self._flash_job = None

    # -------------------------------------------------------------------------
    # Tab lifecycle callback
    # -------------------------------------------------------------------------

    def on_tab_selected(self) -> None:
        """Called by App whenever the Attendance tab is focused."""
        self._date_lbl.configure(text=self._today_label())
        self._refresh_today_sections()
        self._refresh_log()
        self._rfid_entry.focus_set()

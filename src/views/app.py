"""
app.py — Main CustomTkinter application window (Phase 3 redesign).

Responsibilities:
- Full-screen launch on Windows with forced window focus.
- Attendance view occupies the full window (no tab bar on the main screen).
- Ctrl+P opens the admin panel (PIN-protected) for management tasks.
"""

from __future__ import annotations

import sys
import customtkinter as ctk

from views.attendance_tab import AttendanceTab
from utils.logger import log_info, log_error, log_warning
from utils.backup import create_backup
from models.database import close_connection

_BACKUP_INTERVAL_MS = 4 * 60 * 60 * 1000  # 4 hours


class App(ctk.CTk):
    """Root application window."""

    def __init__(self) -> None:
        super().__init__()
        self.title("RFID Attendance System")

        # ── Windowed ──────────────────────────────────────────────────────────
        self.geometry("1280x800")
        self.minsize(900, 600)
        self.configure(fg_color="#1a1a2e")

        # Ctrl+P → admin panel
        self.bind("<Control-p>", self._open_admin_panel)
        self.bind("<Control-P>", self._open_admin_panel)

        # Force focus on Windows
        self.after(100, self._force_focus)

        # Periodic auto-backup every 4 hours (first backup runs on startup)
        self.after(0, self._schedule_auto_backup)

        # ── Build UI ──────────────────────────────────────────────────────────
        self._build_ui()

    # ──────────────────────────────────────────────────────────────────────────
    # UI construction
    # ──────────────────────────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        # Title bar
        title_bar = ctk.CTkFrame(self, fg_color="#0f0f23", height=56, corner_radius=0)
        title_bar.pack(fill="x")
        title_bar.pack_propagate(False)

        ctk.CTkLabel(
            title_bar,
            text="RFID Dance Class Attendance",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color="#e0e0e0",
        ).pack(side="left", padx=20)

        # Admin panel hint
        ctk.CTkLabel(
            title_bar,
            text="Ctrl+P  Admin",
            font=ctk.CTkFont(size=11),
            text_color="#374151",
        ).pack(side="right", padx=(0, 8))

        # Quit button
        ctk.CTkButton(
            title_bar,
            text="✕  Quit",
            width=90, height=36,
            fg_color="#374151", hover_color="#7f1d1d",
            font=ctk.CTkFont(size=13),
            command=self._quit,
        ).pack(side="right", padx=(16, 4), pady=10)

        # Attendance view fills the rest of the window
        self._attendance_tab = AttendanceTab(self, root=self)
        self._attendance_tab.pack(fill="both", expand=True)

    # ──────────────────────────────────────────────────────────────────────────
    # Admin panel (Ctrl+P)
    # ──────────────────────────────────────────────────────────────────────────

    def _open_admin_panel(self, _event: object = None) -> None:
        """Prompt for PIN then open the admin panel."""
        from views.dialogs.pin_dialog import prompt_pin
        from views.admin_panel import AdminPanel

        if not prompt_pin(self):
            log_info("Admin panel access denied — wrong PIN or cancelled.")
            return

        log_info("Admin panel opened.")
        panel = AdminPanel(self)
        self.wait_window(panel)

        # Refresh attendance view after admin panel closes (sections may have changed)
        self._attendance_tab.on_tab_selected()

    # ──────────────────────────────────────────────────────────────────────────
    # Helpers
    # ──────────────────────────────────────────────────────────────────────────

    def _force_focus(self) -> None:
        try:
            self.lift()
            self.focus_force()
        except Exception as exc:
            log_warning(f"_force_focus failed: {exc}")

    def _quit(self) -> None:
        log_info("Application quit requested.")
        try:
            close_connection()
        except Exception as exc:
            log_warning(f"DB close on quit failed: {exc}")
        try:
            self.destroy()
        except Exception as exc:
            log_warning(f"Window destroy on quit failed: {exc}")
        sys.exit(0)

    def _schedule_auto_backup(self) -> None:
        """Create a backup now then reschedule every 4 hours."""
        # DB_PATH import deferred to avoid circular import at module level
        from models.database import DB_PATH
        create_backup(DB_PATH)
        self.after(_BACKUP_INTERVAL_MS, self._schedule_auto_backup)

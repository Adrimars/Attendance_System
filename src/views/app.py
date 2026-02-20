"""
app.py — Main CustomTkinter application window (Task 1.12).

Responsibilities:
- Full-screen launch on Windows with forced window focus.
- Tab-based single-window navigation: Attendance | Sections | Students | Settings.
- Enforces admin PIN on startup via pin_dialog.
- Routes tab-selection callbacks so each tab can re-focus the RFID entry.
"""

from __future__ import annotations

import sys
import customtkinter as ctk

from views.dialogs.pin_dialog import prompt_pin
from views.attendance_tab import AttendanceTab
from views.students_tab import StudentsTab
from views.sections_tab import SectionsTab
from views.settings_tab import SettingsTab
from utils.logger import log_info, log_error


class App(ctk.CTk):
    """Root application window."""

    def __init__(self) -> None:
        super().__init__()
        self.title("RFID Attendance System")

        # ── Full-screen ───────────────────────────────────────────────────────
        self.attributes("-fullscreen", True)
        self.configure(fg_color="#1a1a2e")

        # Allow Escape to exit full-screen (dev convenience; remove for prod)
        self.bind("<Escape>", self._exit_fullscreen)

        # Force focus on Windows
        self.after(100, self._force_focus)

        # ── PIN guard ─────────────────────────────────────────────────────────
        # Rendered after the window is visible so the dialog has a proper parent
        self.after(200, self._check_pin)

        # ── Build UI skeleton ─────────────────────────────────────────────────
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

        # Quit button
        ctk.CTkButton(
            title_bar,
            text="✕  Quit",
            width=90,
            height=36,
            fg_color="#374151",
            hover_color="#7f1d1d",
            font=ctk.CTkFont(size=13),
            command=self._quit,
        ).pack(side="right", padx=16, pady=10)

        # Tab view
        self._tabview = ctk.CTkTabview(
            self,
            fg_color="#1a1a2e",
            segmented_button_fg_color="#0f0f23",
            segmented_button_selected_color="#2563eb",
            segmented_button_selected_hover_color="#1d4ed8",
            segmented_button_unselected_color="#0f0f23",
            segmented_button_unselected_hover_color="#1e293b",
            text_color="#e0e0e0",
            corner_radius=0,
        )
        self._tabview.pack(fill="both", expand=True)

        # Create tabs
        for tab_name in ("Attendance", "Sections", "Students", "Settings"):
            self._tabview.add(tab_name)

        # Mount tab frames
        self._attendance_tab = AttendanceTab(
            self._tabview.tab("Attendance"), root=self
        )
        self._attendance_tab.pack(fill="both", expand=True)

        self._sections_tab = SectionsTab(
            self._tabview.tab("Sections"), root=self
        )
        self._sections_tab.pack(fill="both", expand=True)

        self._students_tab = StudentsTab(
            self._tabview.tab("Students"), root=self
        )
        self._students_tab.pack(fill="both", expand=True)

        self._settings_tab = SettingsTab(
            self._tabview.tab("Settings"), root=self
        )
        self._settings_tab.pack(fill="both", expand=True)

        # Tab change callback
        self._tabview.configure(command=self._on_tab_change)

    # ──────────────────────────────────────────────────────────────────────────
    # PIN guard
    # ──────────────────────────────────────────────────────────────────────────

    def _check_pin(self) -> None:
        """Show PIN dialog. Quit if access is denied."""
        granted = prompt_pin(self)
        if not granted:
            log_error("PIN verification failed — shutting down.")
            self._quit()
        else:
            log_info("PIN verification successful.")
            # Ensure RFID entry is focused after PIN dialog closes
            self._attendance_tab.on_tab_selected()

    # ──────────────────────────────────────────────────────────────────────────
    # Helpers
    # ──────────────────────────────────────────────────────────────────────────

    def _on_tab_change(self) -> None:
        tab_name = self._tabview.get()
        log_info(f"Tab changed to: {tab_name}")
        tab_map = {
            "Attendance": self._attendance_tab,
            "Sections":   self._sections_tab,
            "Students":   self._students_tab,
            "Settings":   self._settings_tab,
        }
        tab = tab_map.get(tab_name)
        if tab and hasattr(tab, "on_tab_selected"):
            tab.on_tab_selected()

    def _force_focus(self) -> None:
        """Bring the window to the foreground on Windows."""
        try:
            self.lift()
            self.focus_force()
        except Exception:
            pass

    def _exit_fullscreen(self, _event: object = None) -> None:
        self.attributes("-fullscreen", False)

    def _quit(self) -> None:
        log_info("Application quit requested.")
        try:
            self.destroy()
        except Exception:
            pass
        sys.exit(0)

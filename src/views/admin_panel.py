"""
admin_panel.py — Admin Panel (Phase 3).

Opened by pressing Ctrl+P on the main attendance screen.
A PIN prompt appears first (via the existing PinDialog); only if the correct
PIN is entered does the admin panel open.

The panel contains the full management tabs:
  - Sections   (section CRUD)
  - Students   (student CRUD + RFID assignment)
  - Settings   (PIN change, threshold, backup, import)
"""

from __future__ import annotations

import customtkinter as ctk

from views.sections_tab import SectionsTab
from views.students_tab import StudentsTab
from views.settings_tab import SettingsTab
from utils.logger import log_info


class AdminPanel(ctk.CTkToplevel):
    """
    Admin panel Toplevel window.  Create and call .wait_window() — the constructor
    already calls grab_set() so it behaves modally.
    """

    def __init__(self, parent: ctk.CTk) -> None:
        super().__init__(parent)
        self.title("Admin Panel")
        self.minsize(800, 600)
        self.resizable(True, True)

        self._app = parent
        self.configure(fg_color="#1a1a2e")

        self._build_ui()

        # Defer window management until after the first render tick.
        # On Windows with a fullscreen parent, CTkToplevel children won't
        # draw unless we wait for the event loop to map the window first.
        self._parent = parent
        self.after(50, self._activate)

        log_info("AdminPanel opened.")

    def _activate(self) -> None:
        """Size, centre, and bring to front after first render."""
        self._centre(self._parent)
        self.lift()
        self.focus_force()
        self.grab_set()
        self.attributes("-topmost", True)
        self.after(200, lambda: self.attributes("-topmost", False))

    # ──────────────────────────────────────────────────────────────────────────
    # Layout
    # ──────────────────────────────────────────────────────────────────────────

    def _centre(self, parent: ctk.CTk) -> None:
        """Centre the panel over the parent window."""
        w, h = 1100, 720
        self.update_idletasks()
        pw, ph = parent.winfo_width(), parent.winfo_height()
        px, py = parent.winfo_x(), parent.winfo_y()
        x = px + max(0, (pw - w) // 2)
        y = py + max(0, (ph - h) // 2)
        self.geometry(f"{w}x{h}+{x}+{y}")

    def _build_ui(self) -> None:
        # ── Title bar ─────────────────────────────────────────────────────────
        title_bar = ctk.CTkFrame(
            self, fg_color="#0f0f23", height=52, corner_radius=0,
        )
        title_bar.pack(fill="x")
        title_bar.pack_propagate(False)

        ctk.CTkLabel(
            title_bar,
            text="⚙  Admin Panel",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color="#e0e0e0",
        ).pack(side="left", padx=18)

        ctk.CTkButton(
            title_bar,
            text="✕  Close",
            width=90, height=34,
            fg_color="#374151", hover_color="#7f1d1d",
            font=ctk.CTkFont(size=13),
            command=self._close,
        ).pack(side="right", padx=14, pady=9)

        # ── Tab view ──────────────────────────────────────────────────────────
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

        for tab_name in ("Sections", "Students", "Settings"):
            self._tabview.add(tab_name)

        # Mount management tabs — each takes (parent_frame, root=toplevel_root)
        # We pass `self` as root so dialogs spawned from these tabs are centred
        # on the admin panel instead of the main window.
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

        self._tabview.configure(command=self._on_tab_change)

        # Load data for the first (default) tab
        self._sections_tab.on_tab_selected()

    # ──────────────────────────────────────────────────────────────────────────
    # Callbacks
    # ──────────────────────────────────────────────────────────────────────────

    def _on_tab_change(self) -> None:
        tab_name = self._tabview.get()
        log_info(f"AdminPanel tab: {tab_name}")
        tab_map = {
            "Sections": self._sections_tab,
            "Students": self._students_tab,
            "Settings": self._settings_tab,
        }
        tab = tab_map.get(tab_name)
        if tab and hasattr(tab, "on_tab_selected"):
            tab.on_tab_selected()

    def _close(self) -> None:
        log_info("AdminPanel closed.")
        self.destroy()

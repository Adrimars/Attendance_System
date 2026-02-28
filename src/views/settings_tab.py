"""
settings_tab.py — Full Admin Panel (Phase 2, Tasks 2.6 & 2.9).

Sections:
  1. Change Admin PIN
  2. Absence Threshold
  3. Language (placeholder — active in Phase 3)
  4. Google Credentials Path (file picker)
  5. Database Backup
  6. Legacy Google Sheets Import
"""

from __future__ import annotations

import os
import sqlite3
from datetime import datetime
from pathlib import Path
from tkinter import messagebox, filedialog
from typing import Any, Optional

import customtkinter as ctk

import controllers.attendance_controller as attendance_ctrl
import models.settings_model as settings_model
from utils.localization import t, set_language
from utils.logger import log_info, log_error
from utils.pin_utils import hash_pin, verify_pin


# ── Helpers ───────────────────────────────────────────────────────────────────



def _perform_backup() -> tuple[bool, str]:
    """
    Back up attendance.db to backups/attendance_YYYY-MM-DD_HHMMSS.db
    using the SQLite backup() API (WAL-safe).

    Returns:
        (True, dest_path)  on success.
        (False, error_msg) on failure.
    """
    from utils.backup import create_backup
    from models.database import DB_PATH
    return create_backup(DB_PATH)


# ── Section frame factory ──────────────────────────────────────────────────────

def _section(parent: Any, title: str) -> ctk.CTkFrame:
    """Create a titled card frame."""
    frame = ctk.CTkFrame(parent, fg_color="#0f0f23", corner_radius=10)
    frame.pack(fill="x", padx=24, pady=(0, 12))
    ctk.CTkLabel(
        frame, text=title,
        font=ctk.CTkFont(size=15, weight="bold"), text_color="#e0e0e0",
    ).pack(padx=16, pady=(12, 6), anchor="w")
    return frame


# ── Main tab class ─────────────────────────────────────────────────────────────

class SettingsTab(ctk.CTkFrame):
    """Settings / Admin Panel tab."""

    def __init__(self, parent: Any, root: Any) -> None:
        super().__init__(parent, fg_color="#1a1a2e", corner_radius=0)
        self._app = root
        self._build_ui()

    # ──────────────────────────────────────────────────────────────────────────
    # UI construction
    # ──────────────────────────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        # Outer scrollable container so the panel doesn't clip on small screens
        outer = ctk.CTkScrollableFrame(self, fg_color="#1a1a2e", corner_radius=0)
        outer.pack(fill="both", expand=True)

        ctk.CTkLabel(
            outer, text="Settings",
            font=ctk.CTkFont(size=26, weight="bold"), text_color="#e0e0e0",
        ).pack(padx=24, pady=(18, 14), anchor="w")

        self._build_pin_section(outer)
        self._build_threshold_section(outer)
        self._build_section_mode_section(outer)
        self._build_language_section(outer)
        self._build_credentials_section(outer)
        self._build_backup_section(outer)
        self._build_import_section(outer)
        self._build_sheets_summary_section(outer)
        self._build_inactive_section(outer)
        self._build_daily_report_section(outer)

    # ── 1. PIN change ─────────────────────────────────────────────────────────

    def _build_pin_section(self, outer: ctk.CTkScrollableFrame) -> None:
        frame = _section(outer, "Change Admin PIN")

        row1 = ctk.CTkFrame(frame, fg_color="transparent")
        row1.pack(fill="x", padx=16, pady=4)
        ctk.CTkLabel(
            row1, text="Current PIN:", width=130,
            font=ctk.CTkFont(size=13), text_color="#c0c0d0",
        ).pack(side="left")
        self._current_pin = ctk.CTkEntry(
            row1, show="●", width=200, height=38, font=ctk.CTkFont(size=14),
        )
        self._current_pin.pack(side="left")

        row2 = ctk.CTkFrame(frame, fg_color="transparent")
        row2.pack(fill="x", padx=16, pady=4)
        ctk.CTkLabel(
            row2, text="New PIN:", width=130,
            font=ctk.CTkFont(size=13), text_color="#c0c0d0",
        ).pack(side="left")
        self._new_pin = ctk.CTkEntry(
            row2, show="●", width=200, height=38, font=ctk.CTkFont(size=14),
        )
        self._new_pin.pack(side="left")

        row3 = ctk.CTkFrame(frame, fg_color="transparent")
        row3.pack(fill="x", padx=16, pady=4)
        ctk.CTkLabel(
            row3, text="Confirm New PIN:", width=130,
            font=ctk.CTkFont(size=13), text_color="#c0c0d0",
        ).pack(side="left")
        self._confirm_pin = ctk.CTkEntry(
            row3, show="●", width=200, height=38, font=ctk.CTkFont(size=14),
        )
        self._confirm_pin.pack(side="left")

        self._pin_status = ctk.CTkLabel(
            frame, text="", font=ctk.CTkFont(size=12), text_color="#ff6b6b",
        )
        self._pin_status.pack(padx=16, pady=(0, 4))

        ctk.CTkButton(
            frame, text="Save PIN", width=140, height=38,
            fg_color="#2563eb", hover_color="#1d4ed8",
            command=self._save_pin,
        ).pack(padx=16, pady=(0, 14), anchor="w")

    # ── 2. Absence threshold ──────────────────────────────────────────────────

    def _build_threshold_section(self, outer: ctk.CTkScrollableFrame) -> None:
        frame = _section(outer, "Absence Threshold")

        row = ctk.CTkFrame(frame, fg_color="transparent")
        row.pack(fill="x", padx=16, pady=(0, 4))
        ctk.CTkLabel(
            row, text="Max absences before alert:", width=220,
            font=ctk.CTkFont(size=13), text_color="#c0c0d0",
        ).pack(side="left")
        self._thresh_entry = ctk.CTkEntry(
            row, width=80, height=38, font=ctk.CTkFont(size=14),
        )
        self._thresh_entry.pack(side="left", padx=(0, 8))
        cur = settings_model.get_setting("absence_threshold") or "3"
        self._thresh_entry.insert(0, cur)

        self._thresh_status = ctk.CTkLabel(
            frame, text="", font=ctk.CTkFont(size=12), text_color="#ff6b6b",
        )
        self._thresh_status.pack(padx=16, pady=(0, 4))

        ctk.CTkButton(
            frame, text="Save Threshold", width=160, height=38,
            fg_color="#2563eb", hover_color="#1d4ed8",
            command=self._save_threshold,
        ).pack(padx=16, pady=(0, 14), anchor="w")


    # ── 2b. Section Mode ─────────────────────────────────────────────────────

    def _build_section_mode_section(self, outer: ctk.CTkScrollableFrame) -> None:
        frame = _section(outer, "Section Mode")

        self._section_mode_var = ctk.BooleanVar(
            value=settings_model.get_setting("section_mode") == "1"
        )

        row = ctk.CTkFrame(frame, fg_color="transparent")
        row.pack(fill="x", padx=16, pady=6)

        ctk.CTkSwitch(
            row, text="Enable Section Mode",
            variable=self._section_mode_var,
            font=ctk.CTkFont(size=13), text_color="#c0c0d0",
            command=self._toggle_section_mode,
        ).pack(side="left")

        ctk.CTkLabel(
            row,
            text="When ON, each RFID scan opens a section picker before marking present.",
            font=ctk.CTkFont(size=11), text_color="#6b7280", wraplength=400,
        ).pack(side="left", padx=(16, 0))

    def _toggle_section_mode(self) -> None:
        val = "1" if self._section_mode_var.get() else "0"
        settings_model.set_setting("section_mode", val)

    # ── 3. Language ───────────────────────────────────────────────────────────

    def _build_language_section(self, outer: ctk.CTkScrollableFrame) -> None:
        frame = _section(outer, t("lang_section"))

        row = ctk.CTkFrame(frame, fg_color="transparent")
        row.pack(fill="x", padx=16, pady=(0, 4))
        ctk.CTkLabel(
            row, text=t("lang_label"), width=180,
            font=ctk.CTkFont(size=13), text_color="#c0c0d0",
        ).pack(side="left")

        current_lang = settings_model.get_setting("language") or "en"
        self._lang_var = ctk.StringVar(
            value="English" if current_lang == "en" else "Türkçe"
        )
        lang_menu = ctk.CTkOptionMenu(
            row, values=["English", "Türkçe"],
            variable=self._lang_var,
            width=180, height=38,
            command=self._save_language,
        )
        lang_menu.pack(side="left")

        self._lang_status = ctk.CTkLabel(
            frame, text="", font=ctk.CTkFont(size=12), text_color="#4ade80",
        )
        self._lang_status.pack(padx=16, pady=(0, 14), anchor="w")

    # ── 4. Google Credentials ─────────────────────────────────────────────────

    def _build_credentials_section(self, outer: ctk.CTkScrollableFrame) -> None:
        frame = _section(outer, "Google Credentials")

        ctk.CTkLabel(
            frame,
            text="Path to the service-account JSON key file for Google Sheets access.",
            font=ctk.CTkFont(size=12), text_color="#6b7280",
        ).pack(padx=16, pady=(0, 6), anchor="w")

        row = ctk.CTkFrame(frame, fg_color="transparent")
        row.pack(fill="x", padx=16, pady=(0, 4))

        saved_path = settings_model.get_setting("google_credentials_path") or ""
        self._creds_var = ctk.StringVar(value=saved_path)
        self._creds_entry = ctk.CTkEntry(
            row, textvariable=self._creds_var,
            width=360, height=38, font=ctk.CTkFont(size=12),
            placeholder_text="No credentials file selected",
        )
        self._creds_entry.pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            row, text="Browse…", width=100, height=38,
            fg_color="#374151", hover_color="#4b5563",
            font=ctk.CTkFont(size=12),
            command=self._browse_credentials,
        ).pack(side="left")

        ctk.CTkButton(
            row, text="🗑  Delete Path", width=130, height=38,
            fg_color="#7f1d1d", hover_color="#991b1b",
            font=ctk.CTkFont(size=12),
            command=self._delete_credentials_path,
        ).pack(side="left", padx=(8, 0))

        self._creds_status = ctk.CTkLabel(
            frame, text="", font=ctk.CTkFont(size=12), text_color="#ff6b6b",
        )
        self._creds_status.pack(padx=16, pady=(0, 4))

        ctk.CTkButton(
            frame, text="Save Path", width=120, height=38,
            fg_color="#2563eb", hover_color="#1d4ed8",
            command=self._save_credentials_path,
        ).pack(padx=16, pady=(0, 14), anchor="w")

    # ── 5. Database backup ────────────────────────────────────────────────────

    def _build_backup_section(self, outer: ctk.CTkScrollableFrame) -> None:
        frame = _section(outer, "Database Backup")

        ctk.CTkLabel(
            frame,
            text="Creates a timestamped copy of attendance.db in the backups/ folder.",
            font=ctk.CTkFont(size=12), text_color="#6b7280",
        ).pack(padx=16, pady=(0, 6), anchor="w")

        self._backup_status = ctk.CTkLabel(
            frame, text="", font=ctk.CTkFont(size=12), text_color="#ff6b6b",
        )
        self._backup_status.pack(padx=16, pady=(0, 4))

        btn_row = ctk.CTkFrame(frame, fg_color="transparent")
        btn_row.pack(fill="x", padx=16, pady=(0, 14))

        ctk.CTkButton(
            btn_row, text="⬇  Backup Now", width=170, height=42,
            fg_color="#374151", hover_color="#4b5563",
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self._backup_now,
        ).pack(side="left", padx=(0, 10))

        ctk.CTkButton(
            btn_row, text="⬆  Restore Backup…", width=190, height=42,
            fg_color="#7c3aed", hover_color="#6d28d9",
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self._restore_backup,
        ).pack(side="left")

    # ── 6. Legacy import ──────────────────────────────────────────────────────

    def _build_import_section(self, outer: ctk.CTkScrollableFrame) -> None:
        frame = _section(outer, "Legacy Google Sheets Import")

        ctk.CTkLabel(
            frame,
            text="Import students from a legacy attendance Google Sheet.\n"
                 "Uses the attendance threshold and credentials path configured above.",
            font=ctk.CTkFont(size=12), text_color="#6b7280",
            justify="left",
        ).pack(padx=16, pady=(0, 6), anchor="w")

        ctk.CTkButton(
            frame, text="Open Import Wizard…", width=200, height=42,
            fg_color="#7c3aed", hover_color="#6d28d9",
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self._open_import,
        ).pack(padx=16, pady=(0, 14), anchor="w")

    # ──────────────────────────────────────────────────────────────────────────
    # Action handlers
    # ──────────────────────────────────────────────────────────────────────────

    def _save_pin(self) -> None:
        current  = self._current_pin.get().strip()
        new_pin  = self._new_pin.get().strip()
        confirm  = self._confirm_pin.get().strip()

        stored_hash = settings_model.get_setting("admin_pin") or ""

        if stored_hash:
            matched, _upgrade = verify_pin(current, stored_hash)
            if not matched:
                self._pin_status.configure(
                    text="Current PIN is incorrect.", text_color="#ff6b6b"
                )
                return
        if not new_pin:
            self._pin_status.configure(
                text="New PIN cannot be empty.", text_color="#ff6b6b"
            )
            return
        if new_pin != confirm:
            self._pin_status.configure(
                text="New PINs do not match.", text_color="#ff6b6b"
            )
            return

        try:
            settings_model.set_setting("admin_pin", hash_pin(new_pin))
        except Exception as exc:
            log_error(f"settings_tab: failed to save PIN — {exc}")
            messagebox.showerror("Error", f"Could not save PIN:\n{exc}", parent=self._app)
            return

        self._current_pin.delete(0, "end")
        self._new_pin.delete(0, "end")
        self._confirm_pin.delete(0, "end")
        self._pin_status.configure(
            text="✓ PIN updated successfully.", text_color="#4ade80"
        )
        log_info("Admin PIN changed via settings tab.")
        self.after(3000, lambda: self._pin_status.configure(text=""))

    def _save_threshold(self) -> None:
        val = self._thresh_entry.get().strip()
        try:
            iv = int(val)
            if iv < 0:
                raise ValueError
        except ValueError:
            self._thresh_status.configure(
                text="Please enter a positive integer.", text_color="#ff6b6b"
            )
            return
        try:
            settings_model.set_setting("absence_threshold", str(iv))
        except Exception as exc:
            log_error(f"settings_tab: failed to save threshold — {exc}")
            messagebox.showerror("Error", f"Could not save threshold:\n{exc}", parent=self._app)
            return
        self._thresh_status.configure(
            text=f"✓ Threshold set to {iv}.", text_color="#4ade80"
        )
        log_info(f"Absence threshold set to {iv}.")
        self.after(3000, lambda: self._thresh_status.configure(text=""))

    def _save_language(self, value: str) -> None:
        code = "en" if value == "English" else "tr"
        try:
            settings_model.set_setting("language", code)
        except Exception as exc:
            log_error(f"settings_tab: failed to save language — {exc}")
            messagebox.showerror("Error", f"Could not save language setting:\n{exc}", parent=self._app)
            return
        # Apply the language globally and live-update the attendance tab if reachable
        set_language(code)
        # _app is AdminPanel; _app._app is the root App (which owns _attendance_tab)
        root_app = getattr(self._app, "_app", self._app)
        att_tab = getattr(root_app, "_attendance_tab", None)
        if att_tab is not None:
            att_tab._apply_language()
        log_info(f"Language preference set to '{code}'.")
        self._lang_status.configure(text=t("lang_restart_note"))
        self.after(5000, lambda: self._lang_status.configure(text=""))

    def _browse_credentials(self) -> None:
        path = filedialog.askopenfilename(
            title="Select Google Service Account JSON",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            parent=self,
        )
        if path:
            self._creds_var.set(path)

    def _save_credentials_path(self) -> None:
        path = self._creds_var.get().strip()
        if not path:
            self._creds_status.configure(
                text="Path cannot be empty.", text_color="#ff6b6b"
            )
            return
        if not os.path.isfile(path):
            self._creds_status.configure(
                text="File not found — please check the path.", text_color="#f59e0b"
            )
            return
        try:
            settings_model.set_setting("google_credentials_path", path)
        except Exception as exc:
            log_error(f"settings_tab: failed to save credentials path — {exc}")
            messagebox.showerror("Error", f"Could not save credentials path:\n{exc}", parent=self._app)
            return
        self._creds_status.configure(
            text="✓ Credentials path saved.", text_color="#4ade80"
        )
        log_info(f"Google credentials path updated: {path}")
        self.after(3000, lambda: self._creds_status.configure(text=""))

    def _delete_credentials_path(self) -> None:
        """Clear the saved Google credentials path from the entry and the database."""
        if not messagebox.askyesno(
            "Delete Credentials Path",
            "Remove the saved Google credentials path?\n"
            "You will need to select a new JSON file before using Google Sheets features.",
            parent=self._app,
        ):
            return
        try:
            settings_model.set_setting("google_credentials_path", "")
        except Exception as exc:
            log_error(f"settings_tab: failed to delete credentials path — {exc}")
            messagebox.showerror("Error", f"Could not remove credentials path:\n{exc}", parent=self._app)
            return
        self._creds_var.set("")
        self._creds_status.configure(
            text="✓ Credentials path removed.", text_color="#4ade80"
        )
        log_info("Google credentials path cleared by user.")
        self.after(3000, lambda: self._creds_status.configure(text=""))

    def _restore_backup(self) -> None:
        """Pick a backup file, safety-backup the live DB, overwrite it, then close."""
        from models.database import DB_PATH, close_connection
        backup_dir = Path(DB_PATH).parent / "backups"
        backup_dir.mkdir(exist_ok=True)

        chosen = filedialog.askopenfilename(
            title="Select a backup to restore",
            initialdir=str(backup_dir),
            filetypes=[("SQLite database", "*.db"), ("All files", "*.*")],
            parent=self._app,
        )
        if not chosen:
            return

        # Validate that the chosen file is a real SQLite database
        try:
            probe = sqlite3.connect(chosen)
            probe.execute("SELECT count(*) FROM sqlite_master;")
            probe.close()
        except sqlite3.DatabaseError:
            messagebox.showerror(
                "Invalid File",
                "The selected file is not a valid SQLite database.",
                parent=self._app,
            )
            return

        if not messagebox.askyesno(
            "Confirm Restore",
            f"Restore from:\n{chosen}\n\n"
            "A safety backup of the current database will be created first.\n"
            "The application will close after restoring — reopen it to continue.\n\n"
            "Proceed?",
            parent=self._app,
        ):
            return

        # Create a safety backup of the current live database first
        _perform_backup()

        # Close existing DB connections before overwriting
        try:
            close_connection()
        except Exception:
            pass

        try:
            # Use SQLite backup API for safe restore
            src_conn = sqlite3.connect(chosen)
            dst_conn = sqlite3.connect(str(DB_PATH))
            with dst_conn:
                src_conn.backup(dst_conn)
            dst_conn.close()
            src_conn.close()
            log_info(f"Database restored from backup: {chosen}")
        except (OSError, sqlite3.Error) as exc:
            log_error(f"Restore failed: {exc}")
            messagebox.showerror("Restore Failed", str(exc), parent=self._app)
            return

        messagebox.showinfo(
            "Restore Complete",
            "Database restored successfully.\nThe application will now close.",
            parent=self._app,
        )
        # Destroy the root App (not just the AdminPanel) so stale connections are gone
        root_app = getattr(self._app, "_app", self._app)
        root_app.destroy()

    def _backup_now(self) -> None:
        ok, result = _perform_backup()
        if ok:
            self._backup_status.configure(
                text=f"✓ Backup saved to:\n{result}", text_color="#4ade80"
            )
            messagebox.showinfo(
                "Backup Complete",
                f"Database backed up successfully:\n{result}",
                parent=self._app,
            )
        else:
            self._backup_status.configure(
                text=f"❌ Backup failed: {result}", text_color="#ff6b6b"
            )
            messagebox.showerror(
                "Backup Failed", f"Could not create backup:\n{result}", parent=self._app
            )
        self.after(5000, lambda: self._backup_status.configure(text=""))

    def _open_import(self) -> None:
        from views.dialogs.import_preview_dialog import ImportPreviewDialog
        dlg = ImportPreviewDialog(self._app)
        self._app.wait_window(dlg)
        if dlg.imported_count > 0:
            messagebox.showinfo(
                "Import Successful",
                f"{dlg.imported_count} student(s) were imported into the database.",
                parent=self._app,
            )

    def _push_sheets_summary(self) -> None:
        """Save the URL setting, then push the attendance summary to Google Sheets."""
        import threading

        url = self._sheets_summary_url.get().strip()
        if not url:
            self._sheets_summary_status.configure(
                text="Please enter a spreadsheet URL.", text_color="#ff6b6b"
            )
            self.after(4000, lambda: self._sheets_summary_status.configure(text=""))
            return

        # Persist the URL so it survives restarts
        try:
            settings_model.set_setting("sheets_summary_url", url)
        except Exception as exc:
            log_error(f"settings_tab: failed to save sheets_summary_url — {exc}")

        self._sheets_summary_status.configure(
            text="Pushing to Google Sheets…", text_color="#93c5fd"
        )

        self._push_result: tuple = (False, "")

        def _bg_push() -> None:
            self._push_result = attendance_ctrl.push_summary_to_sheets(url)

        thread = threading.Thread(target=_bg_push, daemon=True)
        thread.start()
        self._poll_push_thread(thread)

    def _poll_push_thread(self, thread) -> None:
        import threading
        if thread.is_alive():
            self.after(100, lambda: self._poll_push_thread(thread))
            return
        ok, result = self._push_result
        if ok:
            self._sheets_summary_status.configure(
                text=f"✓ {result}", text_color="#4ade80"
            )
            messagebox.showinfo("Push Complete", result, parent=self._app)
        else:
            self._sheets_summary_status.configure(
                text=f"❌ {result}", text_color="#ff6b6b"
            )
            messagebox.showerror("Push Failed", result, parent=self._app)
        self.after(6000, lambda: self._sheets_summary_status.configure(text=""))

    # ──────────────────────────────────────────────────────────────────────────
    # Public hook
    # ──────────────────────────────────────────────────────────────────────────

    # ── 8. Google Sheets Summary ─────────────────────────────────────────────

    def _build_sheets_summary_section(self, outer: ctk.CTkScrollableFrame) -> None:
        frame = _section(outer, "Google Sheets Summary")

        ctk.CTkLabel(
            frame,
            text="Push a per-student attendance summary (attended/total) to a dedicated\n"
                 "'Attendance Summary' worksheet in the given Google Spreadsheet.",
            font=ctk.CTkFont(size=12), text_color="#6b7280",
            justify="left",
        ).pack(padx=16, pady=(0, 6), anchor="w")

        url_row = ctk.CTkFrame(frame, fg_color="transparent")
        url_row.pack(fill="x", padx=16, pady=(0, 4))

        ctk.CTkLabel(
            url_row, text="Spreadsheet URL", width=140,
            font=ctk.CTkFont(size=13), text_color="#c0c0d0",
        ).pack(side="left")

        saved_url = settings_model.get_setting("sheets_summary_url") or ""
        self._sheets_summary_url = ctk.CTkEntry(
            url_row, width=440, height=38, font=ctk.CTkFont(size=12),
            placeholder_text="https://docs.google.com/spreadsheets/d/…",
        )
        self._sheets_summary_url.pack(side="left", fill="x", expand=True)
        if saved_url:
            self._sheets_summary_url.insert(0, saved_url)

        self._sheets_summary_status = ctk.CTkLabel(
            frame, text="", font=ctk.CTkFont(size=12), text_color="#4ade80",
            wraplength=600, justify="left",
        )
        self._sheets_summary_status.pack(padx=16, pady=(0, 4), anchor="w")

        ctk.CTkButton(
            frame, text="Push Summary to Sheets", width=220, height=42,
            fg_color="#166534", hover_color="#15803d",
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self._push_sheets_summary,
        ).pack(padx=16, pady=(0, 14), anchor="w")

    # ── Public hook ───────────────────────────────────────────────────────────

    # ── 9. Inactive Students ───────────────────────────────────────────

    def _build_inactive_section(self, outer: ctk.CTkScrollableFrame) -> None:
        frame = _section(outer, "Inactive Students")

        ctk.CTkLabel(
            frame,
            text="Students are automatically flagged inactive when they have"
                 " N consecutive absences.\n"
                 "An inactive student still scans normally but their banner flashes"
                 " purple as a visual alert.",
            font=ctk.CTkFont(size=12), text_color="#6b7280",
            justify="left", wraplength=580,
        ).pack(padx=16, pady=(0, 6), anchor="w")

        row = ctk.CTkFrame(frame, fg_color="transparent")
        row.pack(fill="x", padx=16, pady=(0, 4))
        ctk.CTkLabel(
            row, text="Consecutive absences to mark inactive:", width=280,
            font=ctk.CTkFont(size=13), text_color="#c0c0d0",
        ).pack(side="left")
        self._inactive_thresh_entry = ctk.CTkEntry(
            row, width=80, height=38, font=ctk.CTkFont(size=14),
        )
        self._inactive_thresh_entry.pack(side="left", padx=(0, 8))
        cur_thresh = settings_model.get_setting("inactive_threshold") or "3"
        self._inactive_thresh_entry.insert(0, cur_thresh)

        self._inactive_status = ctk.CTkLabel(
            frame, text="", font=ctk.CTkFont(size=12), text_color="#4ade80",
            wraplength=580, justify="left",
        )
        self._inactive_status.pack(padx=16, pady=(0, 4), anchor="w")

        btn_row = ctk.CTkFrame(frame, fg_color="transparent")
        btn_row.pack(fill="x", padx=16, pady=(0, 14))

        ctk.CTkButton(
            btn_row, text="Save Threshold", width=160, height=38,
            fg_color="#2563eb", hover_color="#1d4ed8",
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self._save_inactive_threshold,
        ).pack(side="left", padx=(0, 10))

        ctk.CTkButton(
            btn_row, text="Refresh Inactive Status Now", width=220, height=38,
            fg_color="#374151", hover_color="#4b5563",
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self._refresh_inactive_status,
        ).pack(side="left")

    # ── 10. Daily Report ──────────────────────────────────────────────

    def _build_daily_report_section(self, outer: ctk.CTkScrollableFrame) -> None:
        frame = _section(outer, "Daily Report")

        ctk.CTkLabel(
            frame,
            text="Generate a summary of today\'s attendance.\n"
                 "Inactive students are excluded from all totals.",
            font=ctk.CTkFont(size=12), text_color="#6b7280",
            justify="left",
        ).pack(padx=16, pady=(0, 6), anchor="w")

        ctk.CTkButton(
            frame, text="Show Daily Report", width=200, height=42,
            fg_color="#0f4c75", hover_color="#1b6ca8",
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self._show_daily_report,
        ).pack(padx=16, pady=(0, 14), anchor="w")

    # ─────────────────────────────────────────────────────────────────────────────
    # Inactive handlers
    # ─────────────────────────────────────────────────────────────────────────────

    def _save_inactive_threshold(self) -> None:
        val = self._inactive_thresh_entry.get().strip()
        try:
            iv = int(val)
            if iv < 1:
                raise ValueError
        except ValueError:
            self._inactive_status.configure(
                text="Please enter a positive integer (minimum 1).",
                text_color="#ff6b6b",
            )
            return
        try:
            settings_model.set_setting("inactive_threshold", str(iv))
        except Exception as exc:
            log_error(f"settings_tab: failed to save inactive_threshold — {exc}")
            messagebox.showerror("Error", f"Could not save setting:\n{exc}", parent=self._app)
            return
        self._inactive_status.configure(
            text=f"✓ Inactive threshold set to {iv} consecutive absences.",
            text_color="#4ade80",
        )
        log_info(f"Inactive threshold set to {iv}.")
        self.after(3000, lambda: self._inactive_status.configure(text=""))

    def _refresh_inactive_status(self) -> None:
        """Recompute inactive flags for all students and report how many changed."""
        try:
            became_inactive, became_active = attendance_ctrl.refresh_inactive_status_all()
            msg = (
                f"✓ Done — {became_inactive} student(s) newly inactive, "
                f"{became_active} re-activated."
            )
            self._inactive_status.configure(text=msg, text_color="#4ade80")
            messagebox.showinfo("Inactive Status Refreshed", msg, parent=self._app)
        except Exception as exc:
            log_error(f"_refresh_inactive_status: {exc}")
            messagebox.showerror("Error", str(exc), parent=self._app)
        self.after(5000, lambda: self._inactive_status.configure(text=""))

    def _show_daily_report(self) -> None:
        """Build and display a today\'s attendance report in a popup dialog."""
        from datetime import date as _date
        today = _date.today().isoformat()
        try:
            report = attendance_ctrl.get_daily_report(today)
        except Exception as exc:
            log_error(f"_show_daily_report: {exc}")
            messagebox.showerror("Error", f"Could not generate report:\n{exc}", parent=self._app)
            return

        dlg = ctk.CTkToplevel(self._app)
        dlg.title(f"Daily Report — {today}")
        dlg.geometry("560x520")
        dlg.configure(fg_color="#1a1a2e")
        dlg.grab_set()
        dlg.resizable(False, False)

        # Title
        ctk.CTkLabel(
            dlg, text=f"Daily Attendance Report",
            font=ctk.CTkFont(size=20, weight="bold"), text_color="#e0e0e0",
        ).pack(padx=24, pady=(20, 4), anchor="w")
        ctk.CTkLabel(
            dlg, text=today,
            font=ctk.CTkFont(size=13), text_color="#6b7280",
        ).pack(padx=24, pady=(0, 16), anchor="w")

        # Summary card
        summary_frame = ctk.CTkFrame(dlg, fg_color="#0f0f23", corner_radius=10)
        summary_frame.pack(fill="x", padx=24, pady=(0, 14))

        total   = report["total_active"]
        present = report["present_count"]
        absent  = report["absent_count"]
        pct     = f"{present / total * 100:.0f}%" if total > 0 else "N/A"

        stats = [
            ("Active Students", str(total),   "#93c5fd"),
            ("Present",         str(present), "#4ade80"),
            ("Absent",          str(absent),  "#f87171"),
            ("Attendance Rate", pct,           "#fbbf24"),
        ]
        stat_row = ctk.CTkFrame(summary_frame, fg_color="transparent")
        stat_row.pack(fill="x", padx=16, pady=14)
        for label, value, color in stats:
            cell = ctk.CTkFrame(stat_row, fg_color="transparent")
            cell.pack(side="left", expand=True)
            ctk.CTkLabel(
                cell, text=value,
                font=ctk.CTkFont(size=28, weight="bold"), text_color=color,
            ).pack()
            ctk.CTkLabel(
                cell, text=label,
                font=ctk.CTkFont(size=11), text_color="#6b7280",
            ).pack()

        # Per-section breakdown
        ctk.CTkLabel(
            dlg, text="Per-Section Breakdown",
            font=ctk.CTkFont(size=14, weight="bold"), text_color="#e0e0e0",
        ).pack(padx=24, pady=(0, 8), anchor="w")

        sec_scroll = ctk.CTkScrollableFrame(dlg, fg_color="#111125", corner_radius=8)
        sec_scroll.pack(fill="both", expand=True, padx=24, pady=(0, 16))

        sections = report["sections"]
        if not sections:
            ctk.CTkLabel(
                sec_scroll,
                text="No sections scheduled today.",
                font=ctk.CTkFont(size=13), text_color="#6b7280",
            ).pack(pady=20)
        else:
            # Header
            hdr = ctk.CTkFrame(sec_scroll, fg_color="transparent")
            hdr.pack(fill="x", padx=4, pady=(4, 2))
            for text, w in [("Section", 240), ("Present", 90), ("Absent", 90), ("Total", 90), ("Rate", 80)]:
                ctk.CTkLabel(
                    hdr, text=text, width=w, anchor="w",
                    font=ctk.CTkFont(size=11, weight="bold"), text_color="#6b7280",
                ).pack(side="left", padx=4)
            for sec in sections:
                sec_total   = sec["total"]
                sec_present = sec["present"]
                sec_pct     = f"{sec_present / sec_total * 100:.0f}%" if sec_total > 0 else "N/A"
                fr = ctk.CTkFrame(sec_scroll, fg_color="#1e1e35", corner_radius=6)
                fr.pack(fill="x", pady=2, padx=4)
                for text, w, color in [
                    (sec["name"],      240, "#e0e0e0"),
                    (str(sec_present), 90,  "#4ade80"),
                    (str(sec["absent"]), 90, "#f87171"),
                    (str(sec_total),   90,  "#93c5fd"),
                    (sec_pct,          80,  "#fbbf24"),
                ]:
                    ctk.CTkLabel(
                        fr, text=text, width=w, anchor="w",
                        font=ctk.CTkFont(size=13), text_color=color,
                    ).pack(side="left", padx=(8 if text == sec["name"] else 4), pady=6)

        ctk.CTkButton(
            dlg, text="Close", width=100, height=36,
            fg_color="#374151", hover_color="#4b5563",
            command=dlg.destroy,
        ).pack(pady=(0, 16))

    def on_tab_selected(self) -> None:
        pass

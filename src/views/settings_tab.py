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

import hashlib
import os
import shutil
from datetime import datetime
from pathlib import Path
from tkinter import messagebox, filedialog
from typing import Any, Optional

import customtkinter as ctk

import models.settings_model as settings_model
from utils.logger import log_info, log_error


# ── Helpers ───────────────────────────────────────────────────────────────────

def _hash_pin(pin: str) -> str:
    return hashlib.sha256(pin.encode()).hexdigest()


def _perform_backup() -> tuple[bool, str]:
    """
    Copy attendance.db to backups/attendance_YYYY-MM-DD_HHMMSS.db.

    Returns:
        (True, dest_path)  on success.
        (False, error_msg) on failure.
    """
    from models.database import DB_PATH
    src = Path(DB_PATH)
    if not src.exists():
        return False, f"Database file not found:\n{src}"

    backup_dir = src.parent / "backups"
    backup_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    dest = backup_dir / f"attendance_{timestamp}.db"

    try:
        shutil.copy2(str(src), str(dest))
        log_info(f"Database backup created: {dest}")
        return True, str(dest)
    except OSError as exc:
        log_error(f"Backup failed: {exc}")
        return False, str(exc)


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

    def __init__(self, parent: ctk.CTkFrame, root: ctk.CTk) -> None:
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
        self._build_language_section(outer)
        self._build_credentials_section(outer)
        self._build_backup_section(outer)
        self._build_import_section(outer)

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

    # ── 3. Language (placeholder) ─────────────────────────────────────────────

    def _build_language_section(self, outer: ctk.CTkScrollableFrame) -> None:
        frame = _section(outer, "Language  (Phase 3)")

        row = ctk.CTkFrame(frame, fg_color="transparent")
        row.pack(fill="x", padx=16, pady=(0, 4))
        ctk.CTkLabel(
            row, text="Interface language:", width=180,
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

        ctk.CTkLabel(
            frame,
            text="Language switching will be fully active in Phase 3.",
            font=ctk.CTkFont(size=11), text_color="#4b5563",
        ).pack(padx=16, pady=(0, 14), anchor="w")

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

        ctk.CTkButton(
            frame, text="⬇  Backup Now", width=170, height=42,
            fg_color="#374151", hover_color="#4b5563",
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self._backup_now,
        ).pack(padx=16, pady=(0, 14), anchor="w")

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

        if stored_hash and _hash_pin(current) != stored_hash:
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
            settings_model.set_setting("admin_pin", _hash_pin(new_pin))
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
        log_info(f"Language preference set to '{code}' (will apply in Phase 3).")

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

    # ──────────────────────────────────────────────────────────────────────────
    # Public hook
    # ──────────────────────────────────────────────────────────────────────────

    def on_tab_selected(self) -> None:
        pass

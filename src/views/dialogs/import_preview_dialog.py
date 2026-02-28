"""
import_preview_dialog.py — Legacy Google Sheets import preview dialog.
(Phase 2, Task 2.8)

Flow:
  1. User enters a Google Sheet URL and sets an attendance threshold.
  2. "Preview" button calls import_controller.preview_import().
  3. Results shown: total / with RFID / without RFID / session count / will-import / will-skip.
  4. "Confirm Import" commits the rows; "Cancel" discards.
"""

from __future__ import annotations

import threading
from typing import Optional

import customtkinter as ctk
from tkinter import messagebox

import controllers.import_controller as import_ctrl
import models.settings_model as settings_model
from utils.logger import log_info, log_error


class ImportPreviewDialog(ctk.CTkToplevel):
    """
    Modal dialog for legacy Google Sheets import.

    After construction call ``parent.wait_window(dlg)`` and check
    ``dlg.imported_count`` (> 0 means something was committed).
    """

    def __init__(self, parent: ctk.CTk) -> None:
        super().__init__(parent)
        self.title("Import from Google Sheets")
        self.resizable(False, False)
        self.grab_set()

        self.imported_count: int = 0
        self._preview: Optional[import_ctrl.ImportPreview] = None

        self._build_ui()
        self._centre(parent)
        self.protocol("WM_DELETE_WINDOW", self.destroy)

    # ──────────────────────────────────────────────────────────────────────────
    # Layout
    # ──────────────────────────────────────────────────────────────────────────

    def _centre(self, parent: ctk.CTk) -> None:
        self.update_idletasks()
        pw, ph = parent.winfo_width(), parent.winfo_height()
        px, py = parent.winfo_x(), parent.winfo_y()
        dw, dh = self.winfo_reqwidth(), self.winfo_reqheight()
        self.geometry(f"+{px + (pw - dw) // 2}+{py + (ph - dh) // 2}")

    def _build_ui(self) -> None:
        self.configure(fg_color="#1a1a2e")
        pad = {"padx": 28, "pady": 6}

        ctk.CTkLabel(
            self, text="Import from Google Sheets",
            font=ctk.CTkFont(size=20, weight="bold"), text_color="#e0e0e0",
        ).pack(padx=28, pady=(22, 10))

        # ── Sheet URL ─────────────────────────────────────────────────────────
        ctk.CTkLabel(
            self, text="Google Sheet URL *",
            font=ctk.CTkFont(size=13), text_color="#c0c0d0", anchor="w",
        ).pack(fill="x", **pad)
        self._url_entry = ctk.CTkEntry(
            self, width=520, height=40, font=ctk.CTkFont(size=13),
            placeholder_text="https://docs.google.com/spreadsheets/d/…",
        )
        self._url_entry.pack(**pad)
        self._url_entry.focus_set()

        # ── Threshold ─────────────────────────────────────────────────────────
        thresh_row = ctk.CTkFrame(self, fg_color="transparent")
        thresh_row.pack(fill="x", **pad)

        ctk.CTkLabel(
            thresh_row, text="Minimum attendance to import (sessions):",
            font=ctk.CTkFont(size=13), text_color="#c0c0d0",
        ).pack(side="left")

        current_thresh = settings_model.get_setting("absence_threshold") or "3"
        self._thresh_entry = ctk.CTkEntry(
            thresh_row, width=70, height=36, font=ctk.CTkFont(size=13),
        )
        self._thresh_entry.pack(side="left", padx=(8, 0))
        self._thresh_entry.insert(0, current_thresh)

        # ── Preview button ────────────────────────────────────────────────────
        self._preview_btn = ctk.CTkButton(
            self, text="Load Preview", width=160, height=40,
            fg_color="#374151", hover_color="#4b5563",
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self._load_preview,
        )
        self._preview_btn.pack(**pad)

        # ── Status / loading label ────────────────────────────────────────────
        self._status = ctk.CTkLabel(
            self, text="",
            font=ctk.CTkFont(size=12), text_color="#9ca3af",
        )
        self._status.pack(padx=28, pady=(0, 4))

        # ── Preview results panel (hidden until preview loads) ────────────────
        self._results_frame = ctk.CTkFrame(
            self, fg_color="#0f0f23", corner_radius=10,
        )
        # Not packed initially

        # Summary row inside results_frame
        self._summary_frame = ctk.CTkFrame(
            self._results_frame, fg_color="transparent",
        )
        self._summary_frame.pack(fill="x", padx=16, pady=(12, 6))

        self._summary_labels: dict[str, ctk.CTkLabel] = {}
        for key in ("Total rows", "With RFID", "Without RFID",
                    "Sessions found", "Will import", "Will skip"):
            col = ctk.CTkFrame(self._summary_frame, fg_color="#1e1e35", corner_radius=6)
            col.pack(side="left", padx=4)
            ctk.CTkLabel(
                col, text=key,
                font=ctk.CTkFont(size=10), text_color="#6b7280",
            ).pack(padx=10, pady=(6, 0))
            lbl = ctk.CTkLabel(
                col, text="—",
                font=ctk.CTkFont(size=18, weight="bold"), text_color="#e0e0e0",
            )
            lbl.pack(padx=10, pady=(0, 6))
            self._summary_labels[key] = lbl

        # Student list inside results_frame
        ctk.CTkLabel(
            self._results_frame,
            text="Students to be imported (first 50 shown):",
            font=ctk.CTkFont(size=12), text_color="#9ca3af",
        ).pack(padx=16, pady=(8, 4), anchor="w")

        self._student_list = ctk.CTkScrollableFrame(
            self._results_frame, width=520, height=220,
            fg_color="#111125", corner_radius=8,
        )
        self._student_list.pack(padx=16, pady=(0, 14))

        # ── Action buttons ────────────────────────────────────────────────────
        btn_row = ctk.CTkFrame(self, fg_color="transparent")
        btn_row.pack(padx=28, pady=(6, 24))

        ctk.CTkButton(
            btn_row, text="Cancel", width=130, height=42,
            fg_color="#374151", hover_color="#4b5563",
            font=ctk.CTkFont(size=13),
            command=self.destroy,
        ).pack(side="left", padx=(0, 8))

        self._confirm_btn = ctk.CTkButton(
            btn_row, text="Confirm Import", width=170, height=42,
            fg_color="#16a34a", hover_color="#15803d",
            font=ctk.CTkFont(size=14, weight="bold"),
            state="disabled",
            command=self._confirm_import,
        )
        self._confirm_btn.pack(side="left")

    # ──────────────────────────────────────────────────────────────────────────
    # Preview
    # ──────────────────────────────────────────────────────────────────────────

    def _load_preview(self) -> None:
        url = self._url_entry.get().strip()
        if not url:
            self._status.configure(
                text="Please enter a Google Sheet URL.", text_color="#ff6b6b"
            )
            return

        thresh_str = self._thresh_entry.get().strip()
        try:
            thresh = int(thresh_str)
            if thresh < 0:
                raise ValueError
        except ValueError:
            self._status.configure(
                text="Threshold must be a non-negative integer.", text_color="#ff6b6b"
            )
            return

        self._status.configure(
            text="⏳ Connecting to Google Sheets…", text_color="#9ca3af"
        )
        self._preview_btn.configure(state="disabled")

        # Run in background thread to avoid blocking UI
        self._preview_result: tuple = (None, "")
        thread = threading.Thread(
            target=self._bg_load_preview, args=(url, thresh), daemon=True
        )
        thread.start()
        self._poll_preview_thread(thread)

    def _bg_load_preview(self, url: str, thresh: int) -> None:
        """Background thread target for preview_import."""
        try:
            self._preview_result = import_ctrl.preview_import(url, thresh)
        except Exception as exc:
            log_error(f"ImportPreviewDialog: unexpected error — {exc}")
            self._preview_result = (None, str(exc))

    def _poll_preview_thread(self, thread: threading.Thread) -> None:
        if thread.is_alive():
            self.after(100, lambda: self._poll_preview_thread(thread))
            return

        self._preview_btn.configure(state="normal")
        preview, err = self._preview_result

        if preview is None:
            self._status.configure(text=f"❌ {err}", text_color="#ff6b6b")
            return

        self._preview = preview
        self._populate_results(preview)

        if preview.will_import == 0:
            self._status.configure(
                text="No students meet the import criteria.",
                text_color="#f59e0b",
            )
            self._confirm_btn.configure(state="disabled")
        else:
            self._status.configure(
                text=f"✓ Preview ready — {preview.will_import} student(s) will be imported.",
                text_color="#4ade80",
            )
            self._confirm_btn.configure(state="normal")

    def _populate_results(self, preview: import_ctrl.ImportPreview) -> None:
        """Fill the summary stats and student list."""
        mappings = {
            "Total rows":    str(preview.total_rows),
            "With RFID":     str(preview.with_rfid),
            "Without RFID":  str(preview.without_rfid),
            "Sessions found": str(preview.session_count),
            "Will import":   str(preview.will_import),
            "Will skip":     str(preview.will_skip),
        }
        for key, val in mappings.items():
            self._summary_labels[key].configure(text=val)

        # Show results frame
        self._results_frame.pack(fill="x", padx=28, pady=(0, 8))

        # Populate student list (cap at 50 for performance)
        for w in self._student_list.winfo_children():
            w.destroy()

        to_show = [r for r in preview.students if r.include][:50]
        for row in to_show:
            item = ctk.CTkFrame(self._student_list, fg_color="#1e1e35", corner_radius=6)
            item.pack(fill="x", pady=2, padx=4)

            name_str = f"{row.last_name}, {row.first_name}"
            ctk.CTkLabel(
                item, text=name_str,
                font=ctk.CTkFont(size=12), text_color="#e0e0e0",
                width=230, anchor="w",
            ).pack(side="left", padx=(10, 4), pady=6)

            rfid_txt   = row.card_id if row.card_id else "No RFID"
            rfid_color = "#d0d0e0" if row.card_id else "#6b7280"
            ctk.CTkLabel(
                item, text=rfid_txt,
                font=ctk.CTkFont(size=11), text_color=rfid_color,
                width=160, anchor="w",
            ).pack(side="left", padx=4)

            ctk.CTkLabel(
                item,
                text=f"{row.attendance_count} sessions",
                font=ctk.CTkFont(size=11), text_color="#9ca3af",
                width=90, anchor="w",
            ).pack(side="left", padx=4)

    # ──────────────────────────────────────────────────────────────────────────
    # Confirm
    # ──────────────────────────────────────────────────────────────────────────

    def _confirm_import(self) -> None:
        if self._preview is None:
            return

        self._confirm_btn.configure(state="disabled")
        self._status.configure(text="⏳ Importing…", text_color="#9ca3af")

        # Run in background thread
        self._import_result: tuple = (0, 0, "")
        thread = threading.Thread(
            target=self._bg_commit_import, daemon=True
        )
        thread.start()
        self._poll_import_thread(thread)

    def _bg_commit_import(self) -> None:
        """Background thread target for commit_import."""
        try:
            self._import_result = import_ctrl.commit_import(self._preview)
        except Exception as exc:
            log_error(f"ImportPreviewDialog: commit error — {exc}")
            self._import_result = (0, 0, str(exc))

    def _poll_import_thread(self, thread: threading.Thread) -> None:
        if thread.is_alive():
            self.after(100, lambda: self._poll_import_thread(thread))
            return

        imported, skipped, err = self._import_result

        if err:
            self._status.configure(text=f"❌ {err}", text_color="#ff6b6b")
            messagebox.showerror("Import Error", err, parent=self)
            self._confirm_btn.configure(state="normal")
            return

        self.imported_count = imported
        log_info(
            f"Import completed: imported={imported} skipped={skipped}"
        )
        messagebox.showinfo(
            "Import Complete",
            f"Import finished.\n\n"
            f"  Imported: {imported} student(s)\n"
            f"  Skipped:  {skipped} (already exist or card conflict)",
            parent=self,
        )
        self.destroy()


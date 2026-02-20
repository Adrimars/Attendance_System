"""
student_edit_dialog.py — Add / Edit student dialog (Phase 2, Tasks 2.1 & 2.2).

Supports two modes:
  • Add mode  (student_id is None)  — create a new student with no RFID card.
  • Edit mode (student_id provided) — edit name, section memberships, and RFID.

After construction call ``parent.wait_window(dlg)`` and check ``dlg.saved``.
"""

from __future__ import annotations

from typing import Optional

import customtkinter as ctk
from tkinter import messagebox

import controllers.student_controller as student_ctrl
import controllers.section_controller as section_ctrl
from utils.logger import log_info, log_warning


# ──────────────────────────────────────────────────────────────────────────────
# Dialog
# ──────────────────────────────────────────────────────────────────────────────

class StudentEditDialog(ctk.CTkToplevel):
    """
    Modal dialog for adding a new student or editing an existing one.

    Attributes:
        saved (bool): True if the user confirmed and changes were committed.
    """

    def __init__(
        self,
        parent: ctk.CTk,
        student_id: Optional[int] = None,
    ) -> None:
        super().__init__(parent)
        self._student_id = student_id
        self._is_edit: bool = student_id is not None

        self.title("Edit Student" if self._is_edit else "Add Student")
        self.resizable(False, False)
        self.grab_set()

        self.saved: bool = False

        # ── Load existing data ────────────────────────────────────────────────
        self._student_data: Optional[dict] = None
        self._enrolled_ids: set[int] = set()

        if self._is_edit and student_id is not None:
            students = student_ctrl.get_all_students_with_sections()
            for s in students:
                if s["id"] == student_id:
                    self._student_data = s
                    break
            # Load actual enrolled section ids via controller (MVC-compliant)
            self._enrolled_ids = student_ctrl.get_enrolled_section_ids(student_id)

        self._all_sections = section_ctrl.get_all_sections()
        self._section_vars: dict[int, ctk.BooleanVar] = {}
        self._capturing_rfid: bool = False

        self._build_ui()
        self._centre(parent)

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
        pad: dict = {"padx": 28, "pady": 6}

        # Title
        ctk.CTkLabel(
            self,
            text="Edit Student" if self._is_edit else "Add New Student",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color="#e0e0e0",
        ).pack(padx=28, pady=(22, 10))

        # ── First name ────────────────────────────────────────────────────────
        ctk.CTkLabel(
            self, text="First Name *",
            font=ctk.CTkFont(size=13), text_color="#c0c0d0", anchor="w",
        ).pack(fill="x", **pad)
        self._first_name = ctk.CTkEntry(
            self, width=330, height=40,
            font=ctk.CTkFont(size=14), placeholder_text="First name",
        )
        self._first_name.pack(**pad)
        if self._student_data:
            self._first_name.insert(0, self._student_data["first_name"])
        self._first_name.focus_set()

        # ── Last name ─────────────────────────────────────────────────────────
        ctk.CTkLabel(
            self, text="Last Name *",
            font=ctk.CTkFont(size=13), text_color="#c0c0d0", anchor="w",
        ).pack(fill="x", **pad)
        self._last_name = ctk.CTkEntry(
            self, width=330, height=40,
            font=ctk.CTkFont(size=14), placeholder_text="Last name",
        )
        self._last_name.pack(**pad)
        if self._student_data:
            self._last_name.insert(0, self._student_data["last_name"])

        # ── Sections (checkboxes) ─────────────────────────────────────────────
        ctk.CTkLabel(
            self, text="Sections",
            font=ctk.CTkFont(size=13), text_color="#c0c0d0", anchor="w",
        ).pack(fill="x", **pad)

        sec_height = min(160, max(50, len(self._all_sections) * 36))
        sec_frame = ctk.CTkScrollableFrame(
            self, width=330, height=sec_height,
            fg_color="#0f0f23", corner_radius=8,
        )
        sec_frame.pack(**pad)

        if self._all_sections:
            for sec in self._all_sections:
                var = ctk.BooleanVar(value=(sec["id"] in self._enrolled_ids))
                self._section_vars[sec["id"]] = var
                ctk.CTkCheckBox(
                    sec_frame,
                    text=sec["name"],
                    variable=var,
                    font=ctk.CTkFont(size=13),
                    text_color="#d0d0e0",
                    hover_color="#2563eb",
                    checkmark_color="#e0e0e0",
                ).pack(anchor="w", padx=10, pady=4)
        else:
            ctk.CTkLabel(
                sec_frame,
                text="No sections exist yet. Create one in the Sections tab.",
                font=ctk.CTkFont(size=12), text_color="#6b7280",
            ).pack(padx=10, pady=10)

        # ── RFID section (edit mode only) ─────────────────────────────────────
        if self._is_edit:
            self._build_rfid_section(pad)

        # ── Status label ──────────────────────────────────────────────────────
        self._status = ctk.CTkLabel(
            self, text="",
            font=ctk.CTkFont(size=12), text_color="#ff6b6b",
        )
        self._status.pack(padx=28, pady=(4, 6))

        # ── Action buttons ────────────────────────────────────────────────────
        btn_row = ctk.CTkFrame(self, fg_color="transparent")
        btn_row.pack(padx=28, pady=(0, 24))

        ctk.CTkButton(
            btn_row, text="Cancel", width=130, height=42,
            fg_color="#374151", hover_color="#4b5563",
            font=ctk.CTkFont(size=13),
            command=self._cancel,
        ).pack(side="left", padx=(0, 8))

        save_label = "Save Changes" if self._is_edit else "Add Student"
        ctk.CTkButton(
            btn_row, text=save_label, width=170, height=42,
            fg_color="#2563eb", hover_color="#1d4ed8",
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self._save,
        ).pack(side="left")

        self.protocol("WM_DELETE_WINDOW", self._cancel)
        self._last_name.bind("<Return>", lambda _e: self._save())

    def _build_rfid_section(self, pad: dict) -> None:
        """Build the RFID card row (edit mode only)."""
        rfid_outer = ctk.CTkFrame(self, fg_color="#0f0f23", corner_radius=8)
        rfid_outer.pack(fill="x", **pad)

        ctk.CTkLabel(
            rfid_outer, text="RFID Card",
            font=ctk.CTkFont(size=13, weight="bold"), text_color="#c0c0d0",
        ).pack(padx=12, pady=(10, 4), anchor="w")

        rfid_row = ctk.CTkFrame(rfid_outer, fg_color="transparent")
        rfid_row.pack(fill="x", padx=12, pady=(0, 10))

        current = (self._student_data or {}).get("card_id", "")
        display  = current if current else "Not assigned"
        colour   = "#d0d0e0" if current else "#6b7280"

        self._rfid_label = ctk.CTkLabel(
            rfid_row, text=display,
            font=ctk.CTkFont(size=13), text_color=colour,
        )
        self._rfid_label.pack(side="left", padx=(0, 12))

        # Entry for capturing a new card ID (hidden initially)
        self._rfid_entry = ctk.CTkEntry(
            rfid_row, width=190, height=34,
            font=ctk.CTkFont(size=13),
            placeholder_text="Tap card or type ID → Enter",
        )
        # Confirm button for the capture entry (hidden initially)
        self._rfid_confirm_btn = ctk.CTkButton(
            rfid_row, text="✓ Confirm", width=90, height=34,
            fg_color="#16a34a", hover_color="#15803d",
            font=ctk.CTkFont(size=12),
            command=self._confirm_rfid_capture,
        )

        # "Change RFID" button (always visible in edit mode)
        self._rfid_change_btn = ctk.CTkButton(
            rfid_row, text="Change RFID", width=120, height=34,
            fg_color="#374151", hover_color="#4b5563",
            font=ctk.CTkFont(size=12),
            command=self._start_rfid_capture,
        )
        self._rfid_change_btn.pack(side="right")

        if current:
            # Remove card button
            ctk.CTkButton(
                rfid_row, text="Remove", width=80, height=34,
                fg_color="#7f1d1d", hover_color="#991b1b",
                font=ctk.CTkFont(size=12),
                command=self._remove_rfid,
            ).pack(side="right", padx=(0, 6))

    # ──────────────────────────────────────────────────────────────────────────
    # RFID helpers
    # ──────────────────────────────────────────────────────────────────────────

    def _start_rfid_capture(self) -> None:
        """Switch to card-capture mode: show the entry widget."""
        if self._capturing_rfid:
            return
        self._capturing_rfid = True
        self._rfid_label.pack_forget()
        self._rfid_change_btn.pack_forget()
        self._rfid_entry.pack(side="left", padx=(0, 4))
        self._rfid_confirm_btn.pack(side="left", padx=(0, 4))
        cancel_btn = ctk.CTkButton(
            self._rfid_entry.master, text="✕", width=32, height=34,
            fg_color="#374151", hover_color="#4b5563",
            font=ctk.CTkFont(size=12),
            command=self._cancel_rfid_capture,
        )
        cancel_btn.pack(side="left")
        self._rfid_cancel_btn = cancel_btn
        self._rfid_entry.bind("<Return>", lambda _e: self._confirm_rfid_capture())
        self._rfid_entry.focus_set()

    def _cancel_rfid_capture(self) -> None:
        """Revert from card-capture mode."""
        self._capturing_rfid = False
        self._rfid_entry.delete(0, "end")
        self._rfid_entry.pack_forget()
        self._rfid_confirm_btn.pack_forget()
        if hasattr(self, "_rfid_cancel_btn"):
            self._rfid_cancel_btn.destroy()
        self._rfid_label.pack(side="left", padx=(0, 12))
        self._rfid_change_btn.pack(side="right")

    def _confirm_rfid_capture(self) -> None:
        """Validate and apply the new card ID immediately."""
        new_rfid = self._rfid_entry.get().strip()
        if not new_rfid:
            self._status.configure(
                text="Card ID cannot be empty.", text_color="#ff6b6b"
            )
            return

        if self._student_id is None:
            return

        result = student_ctrl.reassign_card(self._student_id, new_rfid)
        if result.success:
            self._rfid_label.configure(text=new_rfid, text_color="#d0d0e0")
            if self._student_data:
                self._student_data["card_id"] = new_rfid
            self._cancel_rfid_capture()
            self._status.configure(
                text="✓ Card updated successfully.", text_color="#4ade80"
            )
            self.after(3000, lambda: self._status.configure(text=""))
            log_info(
                f"StudentEditDialog: card updated for "
                f"student_id={self._student_id} → '{new_rfid}'"
            )
        else:
            self._status.configure(text=result.message, text_color="#ff6b6b")

    def _remove_rfid(self) -> None:
        """Unlink the current card from this student."""
        if self._student_id is None:
            return
        ok, msg = student_ctrl.remove_student_card(self._student_id)
        if ok:
            self._rfid_label.configure(
                text="Not assigned", text_color="#6b7280"
            )
            if self._student_data:
                self._student_data["card_id"] = ""
            self._status.configure(
                text="✓ Card removed.", text_color="#4ade80"
            )
            self.after(3000, lambda: self._status.configure(text=""))
        else:
            self._status.configure(text=msg, text_color="#ff6b6b")

    # ──────────────────────────────────────────────────────────────────────────
    # Save / Cancel
    # ──────────────────────────────────────────────────────────────────────────

    def _save(self) -> None:
        first = self._first_name.get().strip()
        last  = self._last_name.get().strip()

        if not first or not last:
            self._status.configure(
                text="First name and last name are required.",
                text_color="#ff6b6b",
            )
            return

        selected_ids = [
            sid for sid, var in self._section_vars.items() if var.get()
        ]

        if self._is_edit and self._student_id is not None:
            # Update name
            ok, msg = student_ctrl.update_student(self._student_id, first, last)
            if not ok:
                self._status.configure(text=msg, text_color="#ff6b6b")
                return
            # Update sections
            ok2, msg2 = student_ctrl.update_student_sections(
                self._student_id, selected_ids
            )
            if not ok2:
                self._status.configure(text=msg2, text_color="#ff6b6b")
                return
        else:
            # Add mode — create without RFID
            result = student_ctrl.create_student_manually(first, last, selected_ids)
            if not result.success:
                self._status.configure(
                    text=result.message, text_color="#ff6b6b"
                )
                return

        self.saved = True
        self.destroy()

    def _cancel(self) -> None:
        self.saved = False
        self.destroy()

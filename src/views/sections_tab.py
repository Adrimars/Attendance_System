"""
sections_tab.py — Sections management tab (Phase 1, Task 1.12 / exit criteria).

The Phase 1 exit criterion requires creating a section to start a session.
This tab provides full section CRUD so the Phase 1 loop works end-to-end.
"""

from __future__ import annotations

from typing import Any, Optional
import customtkinter as ctk
from tkinter import messagebox

import controllers.section_controller as section_ctrl
from utils.logger import log_info


_TYPES  = ["Technique", "Normal"]
_LEVELS = ["Beginner", "Intermediate", "Advanced"]
_DAYS   = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


class SectionFormDialog(ctk.CTkToplevel):
    """Shared create/edit dialog for sections."""

    def __init__(
        self,
        parent: ctk.CTk,
        title: str = "Section",
        initial: Optional[dict] = None,
    ) -> None:
        super().__init__(parent)
        self.title(title)
        self.resizable(False, False)
        self.grab_set()

        self.result: Optional[dict] = None   # set on confirm
        self._initial = initial or {}

        self._build_ui()
        self._centre(parent)

    def _centre(self, parent: ctk.CTk) -> None:
        self.update_idletasks()
        pw = parent.winfo_width()
        ph = parent.winfo_height()
        px = parent.winfo_x()
        py = parent.winfo_y()
        x = px + (pw - self.winfo_reqwidth()) // 2
        y = py + (ph - self.winfo_reqheight()) // 2
        self.geometry(f"+{x}+{y}")

    def _build_ui(self) -> None:
        self.configure(fg_color="#1a1a2e")
        pad = {"padx": 28, "pady": 6}
        init = self._initial

        ctk.CTkLabel(
            self, text=self.title(), font=ctk.CTkFont(size=18, weight="bold"),
            text_color="#e0e0e0",
        ).pack(padx=28, pady=(20, 10))

        # Name
        ctk.CTkLabel(self, text="Name *", font=ctk.CTkFont(size=13),
                     text_color="#c0c0d0").pack(fill="x", **pad)
        self._name = ctk.CTkEntry(self, width=300, height=40, font=ctk.CTkFont(size=14),
                                  placeholder_text="e.g. Ballet Beginners Monday")
        self._name.pack(**pad)
        if init.get("name"):
            self._name.insert(0, init["name"])
        self._name.focus_set()

        # Type
        ctk.CTkLabel(self, text="Type *", font=ctk.CTkFont(size=13),
                     text_color="#c0c0d0").pack(fill="x", **pad)
        self._type_var = ctk.StringVar(value=init.get("type", _TYPES[0]))
        ctk.CTkOptionMenu(self, values=_TYPES, variable=self._type_var,
                          width=300, height=38).pack(**pad)

        # Level
        ctk.CTkLabel(self, text="Level *", font=ctk.CTkFont(size=13),
                     text_color="#c0c0d0").pack(fill="x", **pad)
        self._level_var = ctk.StringVar(value=init.get("level", _LEVELS[0]))
        ctk.CTkOptionMenu(self, values=_LEVELS, variable=self._level_var,
                          width=300, height=38).pack(**pad)

        # Day
        ctk.CTkLabel(self, text="Day *", font=ctk.CTkFont(size=13),
                     text_color="#c0c0d0").pack(fill="x", **pad)
        self._day_var = ctk.StringVar(value=init.get("day", _DAYS[0]))
        ctk.CTkOptionMenu(self, values=_DAYS, variable=self._day_var,
                          width=300, height=38).pack(**pad)

        # Time
        ctk.CTkLabel(self, text="Time *  (HH:MM)", font=ctk.CTkFont(size=13),
                     text_color="#c0c0d0").pack(fill="x", **pad)
        self._time = ctk.CTkEntry(self, width=300, height=40, font=ctk.CTkFont(size=14),
                                  placeholder_text="e.g. 18:00")
        self._time.pack(**pad)
        if init.get("time"):
            self._time.insert(0, init["time"])

        # Status
        self._status = ctk.CTkLabel(self, text="", font=ctk.CTkFont(size=12),
                                    text_color="#ff6b6b")
        self._status.pack(padx=28, pady=(4, 6))

        # Buttons
        btn_row = ctk.CTkFrame(self, fg_color="transparent")
        btn_row.pack(padx=28, pady=(0, 20))

        ctk.CTkButton(btn_row, text="Cancel", width=130, height=40,
                      fg_color="#374151", hover_color="#4b5563",
                      command=self.destroy).pack(side="left", padx=(0, 8))

        ctk.CTkButton(btn_row, text="Save", width=160, height=40,
                      fg_color="#2563eb", hover_color="#1d4ed8",
                      font=ctk.CTkFont(size=14, weight="bold"),
                      command=self._save).pack(side="left")

        self._time.bind("<Return>", lambda _e: self._save())
        self.protocol("WM_DELETE_WINDOW", self.destroy)

    def _save(self) -> None:
        self.result = {
            "name":  self._name.get().strip(),
            "type":  self._type_var.get(),
            "level": self._level_var.get(),
            "day":   self._day_var.get(),
            "time":  self._time.get().strip(),
        }
        if not self.result["name"]:
            self._status.configure(text="Name is required.")
            self.result = None
            return
        if not self.result["time"]:
            self._status.configure(text="Time is required.")
            self.result = None
            return
        self.destroy()


class SectionsTab(ctk.CTkFrame):
    """Sections management tab — fully functional in Phase 1."""

    def __init__(self, parent: Any, root: Any) -> None:
        super().__init__(parent, fg_color="#1a1a2e", corner_radius=0)
        self._app = root
        self._sections: list = []
        self._build_ui()
        self._load()

    def _build_ui(self) -> None:
        # Header
        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.pack(fill="x", padx=24, pady=(18, 8))

        ctk.CTkLabel(
            hdr, text="Sections",
            font=ctk.CTkFont(size=26, weight="bold"), text_color="#e0e0e0",
        ).pack(side="left")

        ctk.CTkButton(
            hdr, text="+ Add Section", width=140, height=40,
            fg_color="#2563eb", hover_color="#1d4ed8",
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self._add_section,
        ).pack(side="right", padx=4)

        # Column headers
        col_hdr = ctk.CTkFrame(self, fg_color="#0f0f23", corner_radius=0)
        col_hdr.pack(fill="x", padx=24)
        for col, w in [("Name", 220), ("Type", 110), ("Level", 130),
                       ("Day", 110), ("Time", 80), ("", 240)]:
            ctk.CTkLabel(
                col_hdr, text=col, font=ctk.CTkFont(size=12, weight="bold"),
                text_color="#6b7280", width=w, anchor="w",
            ).pack(side="left", padx=8, pady=6)

        self._list_frame = ctk.CTkScrollableFrame(
            self, fg_color="#111125", corner_radius=0,
        )
        self._list_frame.pack(fill="both", expand=True, padx=24, pady=(0, 24))

    def _load(self) -> None:
        for w in self._list_frame.winfo_children():
            w.destroy()
        self._sections = section_ctrl.get_all_sections()
        for s in self._sections:
            self._render_row(s)

    def _render_row(self, s: dict) -> None:
        row = ctk.CTkFrame(self._list_frame, fg_color="#1e1e35", corner_radius=6)
        row.pack(fill="x", pady=2, padx=4)

        for val, w in [(s["name"], 220), (s["type"], 110), (s["level"], 130),
                       (s["day"], 110), (s["time"], 80)]:
            ctk.CTkLabel(
                row, text=str(val), font=ctk.CTkFont(size=13),
                text_color="#d0d0e0", width=w, anchor="w",
            ).pack(side="left", padx=8, pady=8)

        btn_frame = ctk.CTkFrame(row, fg_color="transparent", width=240)
        btn_frame.pack(side="left", padx=4)
        btn_frame.pack_propagate(False)

        ctk.CTkButton(
            btn_frame, text="Students", width=74, height=32,
            fg_color="#065f46", hover_color="#047857",
            font=ctk.CTkFont(size=12),
            command=lambda sid=s["id"], sname=s["name"]: self._show_section_students(sid, sname),
        ).pack(side="left", padx=(0, 4))

        ctk.CTkButton(
            btn_frame, text="Edit", width=70, height=32,
            fg_color="#374151", hover_color="#4b5563",
            font=ctk.CTkFont(size=12),
            command=lambda sid=s["id"]: self._edit_section(sid),
        ).pack(side="left", padx=(0, 4))

        ctk.CTkButton(
            btn_frame, text="Delete", width=70, height=32,
            fg_color="#7f1d1d", hover_color="#991b1b",
            font=ctk.CTkFont(size=12),
            command=lambda sid=s["id"], sname=s["name"]: self._delete_section(sid, sname),
        ).pack(side="left")

    def _add_section(self) -> None:
        dlg = SectionFormDialog(self._app, title="Add Section")
        self._app.wait_window(dlg)
        if dlg.result:
            ok, msg, _ = section_ctrl.create_section(
                dlg.result["name"], dlg.result["type"],
                dlg.result["level"], dlg.result["day"], dlg.result["time"],
            )
            if ok:
                self._load()
            else:
                messagebox.showerror("Error", msg, parent=self._app)

    def _edit_section(self, section_id: int) -> None:
        sec = section_ctrl.get_section_by_id(section_id)
        if sec is None:
            return
        init = {k: sec[k] for k in ("name", "type", "level", "day", "time")}
        dlg = SectionFormDialog(self._app, title="Edit Section", initial=init)
        self._app.wait_window(dlg)
        if dlg.result:
            ok, msg = section_ctrl.update_section(
                section_id, dlg.result["name"], dlg.result["type"],
                dlg.result["level"], dlg.result["day"], dlg.result["time"],
            )
            if ok:
                self._load()
            else:
                messagebox.showerror("Error", msg, parent=self._app)

    def _delete_section(self, section_id: int, name: str) -> None:
        if not messagebox.askyesno(
            "Delete Section",
            f"Delete section '{name}'?\n\nThis will also remove all student enrolments for this section.",
            parent=self._app,
        ):
            return
        ok, msg = section_ctrl.delete_section(section_id)
        if ok:
            self._load()
        else:
            messagebox.showerror("Error", msg, parent=self._app)

    def _show_section_students(self, section_id: int, section_name: str) -> None:
        """Open a popup listing students enrolled in the given section."""
        students = section_ctrl.get_enrolled_students(section_id)

        dlg = ctk.CTkToplevel(self._app)
        dlg.title(f"Students — {section_name}")
        dlg.geometry("420x480")
        dlg.transient(self._app)
        dlg.grab_set()
        dlg.resizable(False, True)

        ctk.CTkLabel(
            dlg, text=f"{section_name}  ({len(students)} students)",
            font=ctk.CTkFont(size=15, weight="bold"),
        ).pack(pady=(12, 6))

        scroll = ctk.CTkScrollableFrame(dlg, fg_color="#1e1e2e")
        scroll.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        if not students:
            ctk.CTkLabel(scroll, text="No students enrolled.", text_color="#9ca3af").pack(pady=20)
        else:
            for idx, st in enumerate(students):
                bg = "#2a2a3c" if idx % 2 == 0 else "#1e1e2e"
                row = ctk.CTkFrame(scroll, fg_color=bg, height=32)
                row.pack(fill="x", pady=1)
                name = f"{st['last_name']}, {st['first_name']}"
                card = st["card_id"] or "—"
                ctk.CTkLabel(row, text=name, width=240, anchor="w",
                             font=ctk.CTkFont(size=13)).pack(side="left", padx=8)
                ctk.CTkLabel(row, text=card, width=120, anchor="e",
                             text_color="#9ca3af", font=ctk.CTkFont(size=12)).pack(side="right", padx=8)

        ctk.CTkButton(dlg, text="Close", width=100, command=dlg.destroy).pack(pady=(4, 12))

    def on_tab_selected(self) -> None:
        self._load()

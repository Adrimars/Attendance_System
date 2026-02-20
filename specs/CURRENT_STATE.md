# Project Current State — RFID Dance Class Attendance System
**Last updated:** 2026-02-20  
**Status:** Phase 1 + Phase 2  complete. 0 Pylance errors. All imports verified.

---

## What the App Does (For a New Chat)

A full-screen Windows kiosk app (Python 3.10 + CustomTkinter + SQLite3) for a dance studio.

- Opens straight to the **attendance screen** — no startup PIN.
- A hidden RFID entry widget is always focused and captures card taps.
- On a tap the system looks up the card, finds all sections the student is enrolled in that are **scheduled for today's weekday**, auto-creates a daily session if needed, and marks the student **Present** in all those sections at once.
- Unknown card → registration dialog opens → student is created with name + section assignments → immediately marked present.
- **Ctrl+P** opens the admin panel (PIN-protected) with three tabs: Sections, Students, Settings.

---

## Folder Structure

```
src/
  main.py                          — entry point; DB init; global error handler
  controllers/
    attendance_controller.py       — process_rfid_passive(); old process_card_tap() kept
    session_controller.py          — start/end session logic (used internally)
    section_controller.py          — section CRUD orchestration
    student_controller.py          — register_student_with_sections(); CRUD helpers
    import_controller.py           — Google Sheets legacy import
  models/
    database.py                    — get_connection(); WAL; schema init
    attendance_model.py            — mark_present/absent; toggle; get_today_attendance_with_details()
    session_model.py               — create_session; get_or_create_session()
    section_model.py               — CRUD; delete_section() cascades correctly; get_sections_for_student_on_day()
    student_model.py               — CRUD; assign/remove section; reassign card
    settings_model.py              — key-value store (PIN hash, threshold, language, credentials path)
  utils/
    logger.py                      — file logger + structured event helpers
  views/
    app.py                         — App(CTk): title bar + AttendanceTab + Ctrl+P handler
    attendance_tab.py              — passive RFID listener; today's log; flash banner
    admin_panel.py                 — AdminPanel(CTkToplevel): Sections + Students + Settings tabs
    sections_tab.py                — section list + add/edit/delete dialogs
    students_tab.py                — student list + search + sort (no Add button here)
    settings_tab.py                — PIN change; threshold; language; credentials; backup; import
    components/
      student_list.py
    dialogs/
      pin_dialog.py                — PinDialog; MAX_ATTEMPTS=5 lockout; prompt_pin() helper
      registration_dialog.py       — unknown-card registration; multi-section checkboxes
      student_edit_dialog.py       — edit student name/sections/RFID card
      import_preview_dialog.py     — Google Sheets import wizard
      session_summary_dialog.py    — end-of-session absent summary (kept for legacy use)
specs/
  plan.md                          — full implementation plan (Phases 1-3 documented)
  agents.md                        — coding conventions and rules
  CURRENT_STATE.md                 — this file
  CHANGELOG.md                     — what changed in each phase (do not re-do these)
  prd/
    PRD-rfid-attendance-system.md
```

---

## Database Schema (6 tables)

```sql
students          (id, first_name, last_name, card_id UNIQUE, created_at)
sections          (id, name, type, level, day, time)
student_sections  (student_id → students, section_id → sections)   [junction]
sessions          (id, section_id → sections, date, start_time, end_time, status)
attendance        (id, session_id → sessions, student_id → students, status, method, timestamp)
settings          (key TEXT PK, value TEXT)
schema_version    (version INT PK)
```

WAL mode enabled on every connection. Foreign keys ON.

---

## Key Design Rules (from specs/agents.md — do NOT violate)

1. **Strict MVC**: views never import models. Controllers are the only bridge.  
   Exception allowed: `models.database.DB_PATH` used in `settings_tab._perform_backup()`.
2. **No new dependencies** — only `customtkinter`, `sqlite3`, `gspread`, `google-auth`.
3. **No raw tracebacks to the user** — all errors surface as `messagebox.showerror`.
4. **All DB writes via** `get_connection()` context manager (auto commit/rollback).
5. **PIN stored as** `hashlib.sha256(pin.encode()).hexdigest()` — never plaintext.
6. **Type hints on all public functions**. `Any` is acceptable for CTk parent/root params.

---

## Attendance Flow (Phase 3 — Current)

```
RFID tap
  │
  ├─ look up card_id in students table
  │     ├─ NOT FOUND → UNKNOWN_CARD → RegistrationDialog (checkboxes for sections)
  │     │                                └─ register_student_with_sections()
  │     │                                └─ re-tap card immediately after save
  │     │
  │     └─ FOUND → get today's weekday (e.g. 'Monday')
  │                  └─ get_sections_for_student_on_day(student_id, day)
  │                       └─ for each section:
  │                            get_or_create_session(section_id, today_date)
  │                            is_duplicate_tap? → DUPLICATE_TAP (yellow)
  │                                             : mark_present(RFID) → KNOWN_PRESENT (green)
```

---

## Admin Panel (Phase 3 — Current)

- **Ctrl+P** on the main window → `prompt_pin(parent)` → if granted → `AdminPanel(parent)`
- `AdminPanel` is a `CTkToplevel`, modal (`grab_set()`), 1100×720 resizable.
- Contains tabs: **Sections** (`SectionsTab`), **Students** (`StudentsTab`), **Settings** (`SettingsTab`).
- Closing the panel calls `attendance_tab.on_tab_selected()` to refresh the attendance view.

---

## PIN System

- Stored as SHA-256 hash in `settings` table under key `admin_pin`.
- Empty hash = first-run → `PinDialog` shows a "create PIN" setup screen.
- `MAX_ATTEMPTS = 5` — after 5 wrong attempts the dialog closes (app continues; PIN is only for admin panel now).
- `prompt_pin(parent) -> bool` — the helper function used by `app.py`.

---

## Settings Tab Sections

1. Change Admin PIN (requires current PIN)
2. Absence Threshold (for Google Sheets import filtering)
3. Language (placeholder — Phase 4)
4. Google Credentials Path (file picker for service-account JSON)
5. Database Backup (timestamped copy to `backups/`)
6. Legacy Google Sheets Import (opens `ImportPreviewDialog`)

---

## What Is NOT Implemented Yet

- Phase 4: Language switching (Turkish/English) — placeholder dropdown exists in Settings.
- Reporting / export to CSV or Google Sheets.
- Absence alerts / notifications.
- Multi-user concurrent access.

# Project Current State — RFID Dance Class Attendance System
**Last updated:** 2026-03-02 (Phase 5 complete; Phase 6+ planned)
**Status:** Phase 1-5 complete. Roadmap for Phase 6-8 in `specs/plan.md`.

---

## What the App Does (For a New Chat)

A windowed Windows desktop app (Python 3.10 + CustomTkinter + SQLite3) for a dance studio.

- Opens straight to the **attendance screen** — no startup PIN.
- A hidden RFID entry widget is always focused and captures card taps.
- On a tap the system looks up the card, finds all sections the student is enrolled in that are **scheduled for today's weekday**, auto-creates a daily session if needed, and marks the student **Present** in all those sections at once.
- Unknown card → registration dialog opens → student is created with name + section assignments → immediately marked present.
- Known student with zero sections → section assignment dialog opens.
- **Ctrl+P** opens the admin panel (PIN-protected) with three tabs: Sections, Students, Settings.
- Inactive students (consecutive absences ≥ threshold) are flagged automatically and shown with a purple flash.
- Auto-backup runs every 4 hours; manual backup and restore available in Settings.
- Localization support: English and Turkish, switchable live from Settings.
- Google Sheets integration: import student rosters and push attendance summaries.
- Daily attendance report dialog with per-section breakdown.

---

## Folder Structure

```
src/
  main.py                          — entry point; DB init; global error handler
  controllers/
    attendance_controller.py       — process_rfid_passive(); get_student_attendance_overview(); set_student_attendance(); push_summary_to_sheets(); get_daily_report(); refresh_inactive_status_all()
    session_controller.py          — start/end session logic (used internally)
    section_controller.py          — section CRUD orchestration
    student_controller.py          — register_student_with_sections(); CRUD helpers
    import_controller.py           — Google Sheets legacy import
  models/
    database.py                    — get_connection(); WAL; schema init; schema_version=2; is_inactive column
    attendance_model.py            — mark_present/absent; toggle; get_today_attendance_with_details()
    session_model.py               — create_session; get_or_create_session()
    section_model.py               — CRUD; delete_section() cascades correctly; get_sections_for_student_on_day()
    student_model.py               — CRUD; assign/remove section; reassign card; is_inactive flag
    settings_model.py              — key-value store (PIN hash, threshold, language, credentials path, section_mode, inactive_threshold, sheets_summary_url)
  utils/
    backup.py                      — create_backup(); MAX_BACKUPS=10; automatic pruning of old backups
    localization.py                — t() translator; set_language/get_language; English+Turkish string table
    logger.py                      — file logger + structured event helpers
    pin_utils.py                   — hash_pin() (PBKDF2-HMAC-SHA256 + salt); verify_pin() (backward-compatible with legacy SHA-256)
  views/
    app.py                         — App(CTk): 1280×800 windowed; title bar + AttendanceTab + Ctrl+P handler + auto-backup scheduler
    attendance_tab.py              — passive RFID listener; ● LISTENING indicator; 10-digit guard; sim panel; today's log; flash banner; locale-independent weekday
    admin_panel.py                 — AdminPanel(CTkToplevel): deferred _activate(); Sections + Students + Settings tabs
    sections_tab.py                — section list + add/edit/delete dialogs
    students_tab.py                — student list + search + sort + Attendance/Edit/Delete per row; PAGE_SIZE=20; inactive student filter
    settings_tab.py                — 10 sections: PIN, threshold, section mode, language, credentials, backup/restore, import, Sheets summary push, inactive threshold, daily report
    components/
      student_list.py
    dialogs/
      pin_dialog.py                — PinDialog; deferred _activate(); MAX_ATTEMPTS=5 lockout; prompt_pin() helper; uses pin_utils
      registration_dialog.py       — unknown-card registration; multi-section checkboxes
      student_edit_dialog.py       — edit student name/sections/RFID card
      manual_attendance_dialog.py  — admin manual Present/Absent editor for any student+date
      import_preview_dialog.py     — Google Sheets import wizard
      session_summary_dialog.py    — end-of-session absent summary (kept for legacy use)
      section_assign_dialog.py     — assign sections to a known student with zero enrolments
specs/
  plan.md                          — implementation plan (Phase 6-8 roadmap)
  agents.md                        — coding conventions and rules
  CURRENT_STATE.md                 — this file
  CHANGELOG.md                     — what changed in each phase (do not re-do these)
  prd/
    PRD-rfid-attendance-system.md
```

---

## Database Schema (6 tables + schema_version)

```sql
students          (id, first_name, last_name, card_id UNIQUE, created_at, is_inactive INTEGER DEFAULT 0)
sections          (id, name, type, level, day, time)
student_sections  (student_id → students, section_id → sections)   [junction]
sessions          (id, section_id → sections, date, start_time, end_time, status)
attendance        (id, session_id → sessions, student_id → students, status, method, timestamp)
settings          (key TEXT PK, value TEXT)
schema_version    (version INT PK)  — current version: 2
```

WAL mode enabled on every connection. Foreign keys ON.

### Settings Keys
- `admin_pin` — PBKDF2-HMAC-SHA256 salted hash (format: `salt_hex$hash_hex`)
- `absence_threshold` — import threshold for legacy Google Sheets
- `inactive_threshold` — consecutive absences before a student is marked inactive (default: 3)
- `language` — `en` or `tr`
- `google_credentials_path` — path to service-account JSON key
- `section_mode` — `0` or `1` (controls section filtering behavior in attendance)
- `sheets_summary_url` — Google Spreadsheet URL for attendance summary push

---

## Key Design Rules (from specs/agents.md — do NOT violate)

1. **Strict MVC**: views never import models. Controllers are the only bridge.  
   Exception allowed: `models.database.DB_PATH` used in `settings_tab._perform_backup()` and `app.py._schedule_auto_backup()`.
2. **No new dependencies** — only `customtkinter`, `sqlite3`, `gspread`, `google-auth`.
3. **No raw tracebacks to the user** — all errors surface as `messagebox.showerror`.
4. **All DB writes via** `get_connection()` context manager (auto commit/rollback).
5. **PIN stored as** PBKDF2-HMAC-SHA256 salted hash via `pin_utils.hash_pin()` — never plaintext. Legacy SHA-256 hashes are verified transparently.
6. **Type hints on all public functions**. `Any` is acceptable for CTk parent/root params.

---

## Attendance Flow (Current)

```
RFID tap
  │
  ├─ validate: exactly 10 decimal digits? → No → red flash "Invalid card"
  │
  ├─ look up card_id in students table
  │     ├─ NOT FOUND → UNKNOWN_CARD → RegistrationDialog (checkboxes for sections)
  │     │                                └─ register_student_with_sections()
  │     │                                └─ re-tap card immediately after save
  │     │
  │     └─ FOUND → check enrolled sections
  │                  ├─ ZERO SECTIONS → NO_SECTIONS → SectionAssignDialog
  │                  │                                 └─ assign sections, then process tap
  │                  │
  │                  └─ HAS SECTIONS → get today's weekday (locale-independent English)
  │                       └─ get_sections_for_student_on_day(student_id, day)
  │                            └─ for each section:
  │                                 get_or_create_session(section_id, today_date)
  │                                 is_duplicate_tap? → DUPLICATE_TAP (yellow)
  │                                                   : mark_present(RFID) → KNOWN_PRESENT (green)
  │                                                     is_inactive? → purple flash warning
```

---

## Admin Panel (Current)

- **Ctrl+P** on the main window → `prompt_pin(parent)` → if granted → `AdminPanel(parent)`
- `AdminPanel` is a `CTkToplevel`, modal (`grab_set()`), 1100×720 resizable. All window-management deferred via `after(50, _activate)` to avoid blank render on Windows.
- Contains tabs: **Sections** (`SectionsTab`), **Students** (`StudentsTab`), **Settings** (`SettingsTab`).
- **Students tab** has an **Attendance** button per row → opens `ManualAttendanceDialog`. Paginated at 20 rows per page.
- Closing the panel calls `attendance_tab.on_tab_selected()` to refresh the attendance view.

---

## Settings Tab Sections (10 sections)

1. **Change Admin PIN** — requires current PIN; uses PBKDF2-HMAC-SHA256
2. **Absence Threshold** — for Google Sheets import filtering
3. **Section Mode** — toggle to control section filtering behavior in attendance
4. **Language** — English / Turkish dropdown; live language switching via `localization.t()`
5. **Google Credentials Path** — file picker for service-account JSON; delete button to clear
6. **Database Backup** — manual backup + restore from backup file picker
7. **Legacy Google Sheets Import** — opens `ImportPreviewDialog`
8. **Google Sheets Summary** — push per-student attendance summary to a Google Spreadsheet
9. **Inactive Students** — configure consecutive absence threshold; refresh inactive status
10. **Daily Report** — generate today's attendance report dialog with per-section breakdown

---

## Simulation Panel

- A `💻 Sim` toggle button on the attendance screen sections bar shows/hides a development input panel.
- Typing a 10-digit ID and pressing Enter goes through the full `_process_card()` pipeline.
- All code is marked `#DELETABLE` for easy removal when hardware is available.

---

## PIN System

- Stored as PBKDF2-HMAC-SHA256 salted hash in `settings` table under key `admin_pin` (format: `salt_hex$hash_hex`).
- Legacy unsalted SHA-256 hashes are detected and verified transparently (no `$` separator).
- Empty hash = first-run → `PinDialog` shows a "create PIN" setup screen.
- `MAX_ATTEMPTS = 5` — after 5 wrong attempts the dialog closes.
- `prompt_pin(parent) -> bool` — the helper function used by `app.py`.
- All hashing logic centralised in `utils/pin_utils.py`.

---

## Auto-Backup System

- `utils/backup.py` provides `create_backup(db_path)` — timestamped copy to `backups/`.
- Maximum 10 backups retained; oldest pruned automatically.
- `App._schedule_auto_backup()` runs on startup and every 4 hours thereafter.
- Manual "Backup Now" and "Restore" buttons available in Settings tab.

---

## Localization System

- `utils/localization.py` provides `t(key)` for translated strings, `set_language()`, `get_language()`.
- Two languages: English (`en`) and Turkish (`tr`).
- String table covers attendance tab labels, settings labels, and shared status strings.
- Language preference saved to `settings` table and loaded on startup via `load_from_settings()`.
- Changing language in Settings applies live to the attendance tab via `_apply_language()`.

---

## Inactive Student System

- Students are automatically flagged `is_inactive = 1` after N consecutive absences (configurable, default 3).
- Inactive students scan normally but display a purple flash as a visual alert.
- Students tab shows inactive students with a red-tinted row; filterable via "Hide inactive students" checkbox.
- `refresh_inactive_status_all()` recomputes inactive flags for all students.
- Daily report excludes inactive students from totals.

---

## What Is NOT Implemented Yet

- Reporting / export to CSV.
- Absence alerts / notifications (beyond inactive flagging).
- Multi-user concurrent access.
- Audio feedback on card tap.
- Dark mode / light mode toggle.
- Daily/weekly attendance calendar view.

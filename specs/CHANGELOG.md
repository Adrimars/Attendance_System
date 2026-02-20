# Changelog — Do NOT Re-Do These Changes

This file documents every design decision and code change that has already been
made. Before writing any new code, read this file top-to-bottom to avoid undoing
or duplicating completed work.

---

## Phase 1 — MVP Core (completed)

All of the following are **done and working**. Do not recreate them.

| File | What was built |
|------|----------------|
| `models/database.py` | `get_connection()` context manager; WAL mode; FK enforcement; full 6-table schema init; `schema_version` migration support. |
| `models/student_model.py` | Full CRUD: create, get_by_id, get_by_card_id, get_all, update, delete, assign_section, remove_section, remove_card, reassign. |
| `models/section_model.py` | Full CRUD. `delete_section()` cascades in FK order (attendance → sessions → student_sections → section). |
| `models/session_model.py` | create_session, get_active_session, get_existing_session_for_date, close_session, `get_or_create_session()`. |
| `models/attendance_model.py` | mark_present, mark_absent, toggle_status, get_attendance_by_session, is_duplicate_tap, get_attendance_record, `get_today_attendance_with_details()`. |
| `models/settings_model.py` | get_setting, set_setting, get_all_settings. |
| `controllers/attendance_controller.py` | `process_card_tap()` (legacy, kept). `process_rfid_passive()` (Phase 3 main flow). `mark_present_manual()`. `toggle_attendance()`. `record_attendance_after_registration()`. |
| `controllers/session_controller.py` | start_session (validates/deduplicates), end_session (generates SessionSummary), get_live_attendance. |
| `controllers/section_controller.py` | create_section, update_section, delete_section (with validation), get_all_sections, get_section_by_id, get_enrolled_students. |
| `controllers/student_controller.py` | register_new_student, `register_student_with_sections()`, reassign_card, delete_student, update_student, get_all_students, get_all_students_with_sections, `get_enrolled_section_ids()`, update_student_sections, remove_student_card, search_students, sort_students. |
| `utils/logger.py` | Daily rotating log to `logs/attendance_YYYY-MM-DD.log`. Structured helpers: log_startup, log_shutdown, log_card_tap, log_session_start, log_session_end, log_import_event, log_export_event. |

---

## Phase 2 — MVP Completion (completed)

| What was built | Where |
|----------------|-------|
| Full student CRUD tab with search + sort | `views/students_tab.py` |
| Student edit dialog (name, sections, RFID change/remove) | `views/dialogs/student_edit_dialog.py` |
| Sections tab with full add/edit/delete dialogs | `views/sections_tab.py` |
| Settings tab with 6 sections (PIN, threshold, language, credentials, backup, import) | `views/settings_tab.py` |
| Google Sheets import controller (preview + commit, threshold filtering) | `controllers/import_controller.py` |
| Google Sheets import wizard dialog | `views/dialogs/import_preview_dialog.py` |
| DB backup (timestamped copy to `backups/`) | `views/settings_tab.py` → `_perform_backup()` |
| Global exception handler (`sys.excepthook`) | `src/main.py` |
| All handlers wrapped in try/except → `messagebox.showerror` | all view files |

---

## Phase 3 — UX & Security Redesign (completed 2026-02-20)

### What changed and why — read before touching these files

---

### 3-A: No startup PIN

**Before:** `App.__init__` called `self.after(200, self._check_pin)` which showed `PinDialog` on launch.  
**After:** Startup PIN removed entirely. App opens directly to the attendance screen.  
**Files changed:** `views/app.py` — removed `_check_pin()` method and `from views.dialogs.pin_dialog import prompt_pin` top-level import.  
**Do NOT re-add a startup PIN.**

---

### 3-B: Ctrl+P Admin Panel

**Before:** Sections, Students, Settings were tabs on the main window's `CTkTabview`.  
**After:**  
- Main window has **no tab bar** — only `AttendanceTab` fills it.  
- Pressing **Ctrl+P** calls `prompt_pin(self)` and, on success, opens `AdminPanel(self)`.  
- `AdminPanel` is a new `CTkToplevel` in `views/admin_panel.py` with its own 3-tab layout.  
**Files created:** `views/admin_panel.py`  
**Files changed:** `views/app.py` — stripped to a single-view window with Ctrl+P binding.  
**Do NOT restore the top-level tab bar. Do NOT add tabs back to `App`.**

---

### 3-C: Passive attendance — no session buttons

**Before:** Attendance tab had a Section dropdown + Start Session + End Session buttons. Taps were rejected if no session was active.  
**After:**  
- Section dropdown and session buttons **removed**.  
- RFID hidden entry is always active (no pre-conditions).  
- On tap: `process_rfid_passive(card_id)` is called.  
  - Finds all sections the student is enrolled in whose `day` field matches today's weekday.  
  - Calls `get_or_create_session(section_id, today_date)` for each section.  
  - Marks Present in every un-marked section.  
  - Returns `DUPLICATE_TAP` if already fully marked today.  
- Attendance screen shows a **"Today's Log"** list (all taps for the current calendar date).  
- An info bar shows which sections are scheduled for today.  
**Files changed:** `views/attendance_tab.py` (complete rewrite).  
**Files changed:** `controllers/attendance_controller.py` (added `process_rfid_passive`, `PassiveTapResult`).  
**Files changed:** `models/session_model.py` (added `get_or_create_session`).  
**Files changed:** `models/section_model.py` (added `get_sections_for_student_on_day`).  
**Files changed:** `models/attendance_model.py` (added `get_today_attendance_with_details`).  
**Do NOT re-add Start/End Session buttons to the attendance screen.**  
**Do NOT check for an active session before recording attendance.**

---

### 3-D: Registration dialog — multi-section checkboxes

**Before:** Registration dialog had a single `CTkOptionMenu` for one optional section.  
**After:** Registration dialog shows a scrollable list of `CTkCheckBox` widgets (one per section with day+time label). Calls `register_student_with_sections(first, last, card_id, [sec_ids])`.  
After dialog closes, `process_rfid_passive(card_id)` is called again to immediately mark the new student present.  
**Files changed:** `views/dialogs/registration_dialog.py` (complete rewrite, old class removed).  
**Do NOT restore the single-section dropdown. Do NOT call `register_new_student()` from the registration dialog.**

---

### 3-E: No manual "Add Student" button

**Before:** `StudentsTab` had a `+ Add Student` button that opened `StudentEditDialog` in add mode.  
**After:** The only way to add a student is to tap an unknown RFID card.  
**Note:** `StudentsTab` (in the admin panel) still has the `+ Add Student` button for the add flow — this is intentional for admin manual data entry. Do not remove it from the admin panel's Students tab. The attendance screen has no add button.

---

### 3-F: Section delete FK error fix

**Before:** `section_model.delete_section()` only deleted `student_sections` and then `sections`, leaving attendance + session rows orphaned — causing `FOREIGN KEY constraint failed`.  
**After:** Correct cascade order: `attendance → sessions → student_sections → section` in a single `get_connection()` transaction.  
**Files changed:** `models/section_model.py` → `delete_section()`.  
**Do NOT revert this to the old 2-step delete.**

---

### 3-G: Type annotation widening

All tab `__init__` signatures changed from `parent: ctk.CTkFrame, root: ctk.CTk` to `parent: Any, root: Any` to allow `CTkToplevel` (AdminPanel) and `App` (CTk subclass) to pass Pylance validation without errors.  
**Files changed:** `attendance_tab.py`, `sections_tab.py`, `students_tab.py`, `settings_tab.py`.  
**Do NOT narrow these back to specific CTk types.**

---

## Invariants — Things That Must Never Change

- `get_connection()` must be the only way to open DB connections.
- PIN always stored as `hashlib.sha256(pin.encode()).hexdigest()` in settings key `admin_pin`.
- Views must never import from `models.*` directly (only from `controllers.*`).  
  Only exception: `settings_tab._perform_backup()` reads `models.database.DB_PATH`.
- `student_edit_dialog.py` uses `student_ctrl.get_enrolled_section_ids()` — NOT `models.student_model.get_sections_for_student()` directly.
- Log files go to `logs/attendance_YYYY-MM-DD.log` — path determined by `utils/logger.py`.
- Backups go to `backups/attendance_YYYY-MM-DD_HHMMSS.db`.

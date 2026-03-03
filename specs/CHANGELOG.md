# Changelog — Do NOT Re-Do These Changes

This file documents every design decision and code change that has already been
made. Before writing any new code, read this file top-to-bottom to avoid undoing
or duplicating completed work.

---

## Documentation Refresh (2026-03-02)

| What was updated | Where |
|------------------|-------|
| PRD refreshed to v1.2 with current scope and roadmap snapshot | `specs/prd/PRD-rfid-attendance-system.md` |
| Agent guidelines aligned to current architecture and constraints | `specs/agents.md` |
| Implementation plan updated with Phase 6-8 roadmap | `specs/plan.md` |
| Current state and changelog aligned to latest docs | `specs/CURRENT_STATE.md`, `specs/CHANGELOG.md` |

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
- PIN stored as PBKDF2-HMAC-SHA256 salted hash via `utils/pin_utils.py` under settings key `admin_pin` (format: `salt_hex$hash_hex`). Legacy SHA-256 hashes are verified transparently.
- Views must never import from `models.*` directly (only from `controllers.*`).  
  Only exception: `settings_tab._perform_backup()` reads `models.database.DB_PATH`.
- `student_edit_dialog.py` uses `student_ctrl.get_enrolled_section_ids()` — NOT `models.student_model.get_sections_for_student()` directly.
- Log files go to `logs/attendance_YYYY-MM-DD.log` — path determined by `utils/logger.py`.
- Backups go to `backups/attendance_YYYY-MM-DD_HHMMSS.db`.

---

## Phase 4 — Stability, UX Polish & Manual Attendance (completed 2026-02-20)

---

### 4-A: Windowed mode

**Before:** App launched fullscreen (`self.attributes("-fullscreen", True)`).
**After:** App opens as a normal resizable window at `1280×800` (minimum `900×600`).
**Files changed:** `views/app.py` — removed `-fullscreen` attribute and the `_exit_fullscreen` method (Escape handler removed too).
**Do NOT re-add fullscreen as the default.** If the operator wants fullscreen they can maximise the OS window.

---

### 4-B: CTkToplevel deferred activation

**Problem:** On Windows, `CTkToplevel` widgets opened from a fullscreen parent (or any parent) render blank/tiny when `grab_set()`, `geometry()`, and `lift()` are called synchronously in `__init__`. The OS maps the window shell before child widgets are drawn.
**Fix:** Both `PinDialog` and `AdminPanel` now defer all window-management calls to `self.after(50, self._activate)`. The `_activate()` method runs after the first render tick and calls `_centre()`, `grab_set()`, `lift()`, `focus_force()`, and a brief `-topmost True` flash.
**Files changed:** `views/dialogs/pin_dialog.py`, `views/admin_panel.py`.
**Do NOT move window sizing/grab calls back into `__init__` synchronously.**

---

### 4-C: PinDialog `pady` duplicate keyword crash fix

**Problem:** `_build_ui()` defined `pad = {"padx": 30, "pady": 10}` and then called `.pack(**pad, pady=(24,4))` — passing `pady` twice → `TypeError`.
**Fix:** Removed the shared `pad` dict; each `.pack()` call now specifies `padx` and `pady` independently.
**Files changed:** `views/dialogs/pin_dialog.py`.

---

### 4-D: LISTENING/IDLE indicator

**Added:** A `● LISTENING` / `◌ IDLE` label in the right side of the sections info bar in the attendance tab.
- Shows green `● LISTENING` when the hidden RFID entry has keyboard focus (ready to receive hardware input).
- Shows grey `◌ IDLE` when focus is elsewhere (e.g. admin panel open).
**Files changed:** `views/attendance_tab.py`.

---

### 4-E: 10-digit RFID guard

**Added:** Before any DB lookup, `_on_rfid_enter()` validates `card_id.isdigit() and len(card_id) == 10`. Anything else triggers a red flash showing the rejected value and returns without processing.
**Files changed:** `views/attendance_tab.py`.
**Do NOT remove or relax this guard.** RFID readers used in this project produce exactly 10 decimal digits.

---

### 4-F: RFID simulation panel

**Added:** A `💻 Sim` toggle button in the sections bar. Clicking it shows/hides a clearly-marked amber simulation panel where any 10-digit ID can be typed and submitted, going through the exact same `_process_card()` pipeline as a real hardware tap.
**Purpose:** Hardware RFID reader not always available during development.
**All simulation code is marked `#DELETABLE`.** To remove: delete `_build_sim_panel()` call in `_build_ui()`, the `_sim_toggle_btn` lines, and the three methods `_build_sim_panel`, `_toggle_sim_panel`, `_sim_submit`.
**Files changed:** `views/attendance_tab.py`.

---

### 4-G: Focus management refactor (loop & freeze fixes)

**Problems fixed:**
1. Clicking the Sim button caused an infinite LISTENING↔IDLE loop — the `FocusOut` handler unconditionally rescheduled `_rfid_entry.focus_set()` every 100 ms, fighting the sim entry.
2. Second and subsequent sim taps misbehaved — `_sim_submit` injected text into `_rfid_entry` and called `_on_rfid_enter`, which ended with `_rfid_entry.focus_set()`, stealing focus from `_sim_entry`.
3. Opening/closing the admin panel caused event-loop thrashing — the refocus timer fought `grab_set()` repeatedly.

**Fixes:**
- `<FocusOut>` now calls `_on_rfid_focus_out()` which only schedules `_try_refocus()` when `_sim_visible is False`.
- `_try_refocus()` checks `grab_current()` — backs off with a 500 ms retry if a modal is open.
- Card logic extracted to `_process_card(card_id)` — called by both `_on_rfid_enter` and `_sim_submit` directly, with no focus side-effects.
- `_open_registration()` returns focus to `_sim_entry` if sim panel is visible, otherwise to `_rfid_entry`.
**Files changed:** `views/attendance_tab.py`.

---

### 4-H: Manual attendance editor

**Added:** Admin can manually set any student's attendance for any date from the Students tab in the admin panel.

**New controller functions** (`controllers/attendance_controller.py`):
- `get_student_attendance_overview(student_id, date_str)` — returns per-section status for a student on any date.
- `set_student_attendance(student_id, section_id, date_str, target_status)` — explicitly sets Present/Absent, auto-creating a session if needed.

**New dialog** (`views/dialogs/manual_attendance_dialog.py`):
- Date picker (default today); any `YYYY-MM-DD` accepted.
- One row per enrolled section showing: section name, schedule (day+time), coloured status badge, **✓ Present** and **✗ Absent** buttons.
- Currently-active status button is highlighted. Changes save immediately on click.

**Students tab change** (`views/students_tab.py`):
- Each student row now has a green **Attendance** button alongside Edit and Delete.
- Button opens `ManualAttendanceDialog` for that student.
- Action column width widened from 196 to 296 px to accommodate the third button.

**Do NOT route manual attendance changes through `process_rfid_passive()`.** Use `set_student_attendance()` directly.

---

## Phase 5 — Feature Expansion & Hardening (2026-02-22 → 2026-03-01)

Phase 5 adds localization, inactive student tracking, auto-backup, secure PIN upgrade, Google Sheets export, daily reports, section assignment for zero-section students, and numerous bug fixes.

---

### 5-A: Localization system (English + Turkish)

**Added:** `utils/localization.py` — a lightweight i18n helper with a string table covering attendance tab and settings labels.
- `t(key)` returns translated text based on the active language.
- `set_language(code)`, `get_language()`, `load_from_settings()`.
- Language preference persisted in the `settings` table and loaded on startup.
- Changing language in Settings applies **live** to the attendance tab via `_apply_language()` — no restart required for the main screen.
**Files created:** `utils/localization.py`.
**Files changed:** `views/attendance_tab.py`, `views/settings_tab.py`, `main.py`.

---

### 5-B: Locale-independent weekday and month handling

**Problem:** `datetime.strftime("%A")` returns OS-locale weekday names (e.g. Turkish "Pazartesi" instead of "Monday"), breaking section day matching since DB stores English day names.
**Fix:** Added `_ENGLISH_DAYS` and `_ENGLISH_MONTHS` lookup arrays and `_english_weekday(dt)` / `_english_month(dt)` helpers in `attendance_controller.py`. All weekday/month formatting now uses these instead of `strftime`.
**Files changed:** `controllers/attendance_controller.py`, `views/attendance_tab.py`.
**Do NOT use strftime("%A") or strftime("%B") for any logic that touches the DB.**

---

### 5-C: Inactive student tracking

**Added:** Students are automatically flagged `is_inactive = 1` in the DB after exceeding a configurable consecutive-absence threshold.
- Schema migration: `schema_version` bumped to 2; `is_inactive INTEGER DEFAULT 0` column added to `students` table.
- `refresh_inactive_status_all()` in `attendance_controller.py` recomputes inactive flags for all students.
- Inactive students display with a **purple** flash on RFID tap and a red-tinted row in the Students tab.
- "Hide inactive students" checkbox added to Students tab filter bar.
- Settings tab section 9: **Inactive Students** — configurable threshold + manual refresh button.
**Files changed:** `models/database.py`, `models/student_model.py`, `controllers/attendance_controller.py`, `views/students_tab.py`, `views/settings_tab.py`, `views/attendance_tab.py`.

---

### 5-D: Auto-backup utility

**Added:** `utils/backup.py` — `create_backup(db_path)` creates timestamped copies to `backups/`, maximum 10 retained (oldest pruned).
- `App._schedule_auto_backup()` runs on startup and every 4 hours via `self.after()`.
- Settings tab backup section also supports **restore from backup** — file picker, safety backup of current DB, then overwrite and close.
**Files created:** `utils/backup.py`.
**Files changed:** `views/app.py`, `views/settings_tab.py`.

---

### 5-E: Secure PIN hashing upgrade (PBKDF2)

**Added:** `utils/pin_utils.py` — centralised `hash_pin()` and `verify_pin()` using PBKDF2-HMAC-SHA256 with 260,000 iterations + 16-byte random salt.
- New format: `salt_hex$hash_hex`.
- `verify_pin()` detects legacy unsalted SHA-256 hashes (no `$` separator) and handles them transparently — zero migration friction.
- `PinDialog` and `SettingsTab` now import from `pin_utils` instead of defining their own hash functions.
**Files created:** `utils/pin_utils.py`.
**Files changed:** `views/dialogs/pin_dialog.py`, `views/settings_tab.py`.
**Do NOT define _hash_pin() in any other module. Always use pin_utils.**

---

### 5-F: Section assignment dialog (NO_SECTIONS flow)

**Added:** `views/dialogs/section_assign_dialog.py` — modal dialog for assigning sections to a known student who has zero sections enrolled.
- Triggered when `process_rfid_passive()` returns `TapResultType.NO_SECTIONS`.
- Shows student name + scrollable section checkboxes. On confirm, enrolls the student and re-processes the tap.
**Files created:** `views/dialogs/section_assign_dialog.py`.
**Files changed:** `controllers/attendance_controller.py` (added `NO_SECTIONS` result type), `views/attendance_tab.py`.

---

### 5-G: Section mode toggle

**Added:** Settings section "Section Mode" — a checkbox that toggles `section_mode` in the settings table.
- Controls whether the attendance view shows all sections or only today's scheduled sections in the info bar.
**Files changed:** `views/settings_tab.py`.

---

### 5-H: Google Sheets attendance summary push

**Added:** Settings section "Google Sheets Summary" — push a per-student attendance summary (attended/total per section) to a dedicated "Attendance Summary" worksheet in a given Google Spreadsheet.
- `push_summary_to_sheets(spreadsheet_url)` in `attendance_controller.py` — authenticates via service-account credentials, builds summary data, writes to sheet.
- Spreadsheet URL persisted in `sheets_summary_url` setting.
- Push runs in a background thread to avoid UI freeze; status label shows progress.
**Files changed:** `controllers/attendance_controller.py`, `views/settings_tab.py`.

---

### 5-I: Daily attendance report

**Added:** Settings section "Daily Report" — generates a today's-attendance report popup.
- `get_daily_report(date_str)` in `attendance_controller.py` — returns total active students, present/absent counts, and per-section breakdown.
- Report dialog shows summary cards (Active, Present, Absent, Rate) and a scrollable per-section table.
- Inactive students excluded from all totals.
**Files changed:** `controllers/attendance_controller.py`, `views/settings_tab.py`.

---

### 5-J: Students tab pagination reduced

**Changed:** `StudentsTab._PAGE_SIZE` reduced from 50 to 20 rows per page for improved rendering performance.
**Files changed:** `views/students_tab.py`.

---

### 5-K: Bug fixes (2026-03-01)

| Fix | Description | Files |
|-----|-------------|-------|
| CTkEntry cursor param | Removed unsupported `cursor` parameter from CTkEntry constructor | `views/attendance_tab.py` |
| RFID input handling | Fixed RFID entry processing edge cases | `views/attendance_tab.py` |
| Sheets push | Fixed Google Sheets push to handle missing credentials and empty data gracefully | `controllers/attendance_controller.py`, `views/settings_tab.py` |
| Enrollment attendance | Fixed: only mark present for today's scheduled sections during registration (not all enrolled sections) | `controllers/attendance_controller.py` |
| Section mode display | Section info bar now respects section_mode setting for showing all vs. today's sections | `views/attendance_tab.py` |

---

### 5-L: Infrastructure additions

- `requirements.txt` and `requirements-dev.txt` created with pinned dependencies.
- `attendance.spec` PyInstaller build config added.
- `LICENSE` (MIT) added.
- `README.md` created with full setup/usage/build instructions.
- `.gitignore` expanded for Python/IDE/build artifacts.

---

### Phase 5 Exit Criteria

- [x] Language switching works live from Settings (English ↔ Turkish)
- [x] Weekday matching is locale-independent — works on Turkish Windows
- [x] Inactive students auto-flagged after N consecutive absences
- [x] Auto-backup runs every 4 hours; manual backup + restore available
- [x] PIN hashing upgraded to PBKDF2 with backward compatibility
- [x] Students with zero sections get a section assignment dialog on tap
- [x] Google Sheets summary push works end-to-end
- [x] Daily report shows per-section breakdown
- [x] Students tab loads 20 rows per page

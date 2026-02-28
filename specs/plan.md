# Implementation Plan — RFID Dance Class Attendance System

**Project:** RFID Dance Class Attendance System v1.1  
**Developer:** Orkun Arslanturk  
**PRD:** `specs/prd/PRD-rfid-attendance-system.md`  
**Status:** Active  
**Last Updated:** 2026-03-01

---

## 1. Goal & Approach

### What We're Building
A Windows desktop kiosk application that lets a dance studio administrator tap RFID cards to record attendance, manage students and sections, start/end class sessions with live absent lists, and import legacy data from Google Sheets. Phase 1 (MVP) delivers the complete offline attendance workflow. Phase 2 adds reporting, Google Sheets export, absence alerts, and i18n.

**"Done" for Phase 1 means:** An administrator can launch the app full-screen, enter an admin PIN, create sections, start a session, tap RFID cards to record attendance (with auto-registration for unknown cards), manually toggle attendance, reassign cards, end the session with an absent summary popup, import legacy data from Google Sheets, and view/search/sort the student database — all stored in a local SQLite database.

### Strategy
**Bottom-up, layer by layer, then vertical integration:**
1. Infrastructure first — project skeleton, database schema, config.
2. Model layer — all data access methods for every entity.
3. Controller layer — all business logic (RFID processing, session management, import).
4. View layer — CustomTkinter UI screens wired to controllers.
5. Integration — end-to-end testing of each use case.

This order minimizes rework: models are stable before controllers consume them, and controllers are stable before views wire to them.

### Out of Scope for This Plan
- Cloud/web deployment
- Mobile companion app
- Payment/billing integration
- Biometric or facial recognition
- Multi-user concurrent access

---

## 2. Environment Setup Checklist

> Complete before writing any application code.

- [ ] Python 3.10+ installed and verified (`python --version`)
- [ ] Virtual environment created (`python -m venv venv`) and activated
- [ ] `requirements.txt` created with: `customtkinter`, `gspread`, `google-auth`
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] Project folder structure created (see Section 5)
- [ ] USB HID RFID reader connected and tested (type into Notepad to verify card ID output format)
- [ ] Empty `attendance.db` SQLite file created with WAL mode enabled
- [ ] `.gitignore` configured (exclude `venv/`, `attendance.db`, `*.pyc`, Google credentials JSON)

---

## 3. Phase Breakdown

### Phase 1 — MVP Core (Day 1)
**Goal:** Database layer, core business logic, and the main attendance screen are fully functional. A user can start a session and tap cards to record attendance.

#### Tasks

| # | Task | Layer | PRD Ref | Done |
|---|------|-------|---------|------|
| 1.1 | Create project skeleton: folder structure, `main.py` entry point, `requirements.txt`, `.gitignore` | Infra | §9.2, §9.3 | [x] |
| 1.2 | Implement `database.py` — connection manager with WAL mode, schema initialization (all 6 tables from agents.md §3), migration support | Model | FR-1.4 | [x] |
| 1.3 | Implement `student_model.py` — CRUD operations: create, get_by_id, get_by_card_id, get_all, update, delete, assign/remove section, reassign card | Model | FR-1.3, FR-1.6, FR-1.7, FR-1.12 | [x] |
| 1.4 | Implement `section_model.py` — CRUD operations: create, get_by_id, get_all, update, delete, get_enrolled_students | Model | FR-1.5 | [x] |
| 1.5 | Implement `session_model.py` — create session, get active session, close session, check for existing session (same section + date) | Model | FR-1.10, FR-1.11 | [x] |
| 1.6 | Implement `attendance_model.py` — mark present (RFID/Manual), mark absent, toggle status, get attendance by session, check duplicate tap | Model | FR-1.2, FR-1.9 | [x] |
| 1.7 | Implement `settings_model.py` — get/set key-value pairs (admin PIN, absence threshold, language, credentials path) | Model | §5.2 | [x] |
| 1.8 | Implement `attendance_controller.py` — process card tap (lookup → known/unknown/duplicate), return result type + student info for UI feedback | Controller | FR-1.1, FR-1.2, FR-1.3, FR-1.13 | [x] |
| 1.9 | Implement `session_controller.py` — start session (validate section, check existing, create), end session (generate absent summary, close), get live attendance state | Controller | FR-1.10, FR-1.11, FR-1.14 | [x] |
| 1.10 | Implement `student_controller.py` — register new student from unknown card, reassign RFID card (validate uniqueness, unlink old), search/sort students | Controller | FR-1.3, FR-1.12, FR-1.15 | [x] |
| 1.11 | Implement `section_controller.py` — section CRUD orchestration with validation | Controller | FR-1.5 | [x] |
| 1.12 | Set up `app.py` — main CustomTkinter window, full-screen launch, force-focus, tab-based navigation skeleton (Attendance, Students, Sections, Settings tabs) | View | §5.4 | [x] |
| 1.13 | Implement Attendance tab — section selector dropdown, Start/End Session buttons, hidden RFID input entry widget (focused, captures keyboard stream, fires on Enter), live student list (name + status), color-flash background (Green/Red/Yellow for 2–3s) | View | FR-1.8, FR-1.10, FR-1.11, FR-1.13, FR-1.14 | [x] |
| 1.14 | Implement registration dialog — popup triggered by unknown card tap, fields: first name, last name, confirm/cancel buttons, optional section assignment | View | FR-1.3 | [x] |
| 1.15 | Implement manual attendance toggle — clickable Present/Absent status in the live student list, sets `method = 'Manual'` | View | FR-1.9 | [x] |
| 1.16 | Implement End Session popup — summary showing total enrolled, present count, absent count, named absent list, last-minute manual toggle, Confirm & Close button | View | FR-1.11 | [x] |

#### Phase 1 (Day 1) Exit Criteria
- [x] App launches full-screen on Windows with tab navigation
- [x] Can create a section, start a session for it, tap an RFID card, and see the student marked present with a green flash
- [x] Unknown card tap opens registration dialog; completing it creates the student and records attendance
- [x] Duplicate tap shows yellow flash and "Already marked" message
- [x] Can manually toggle a student's attendance (flagged as Manual in DB)
- [x] End Session shows absent summary popup with correct counts
- [x] All data persists in `attendance.db` with WAL mode

---

### Phase 2 — MVP Completion (Day 2)
**Goal:** Student/section management screens, RFID card reassignment, legacy import, admin panel, and polish. MVP is fully usable.

#### Tasks

##### 2A — Student & Section Management

| # | Task | Layer | PRD Ref | Done |
|---|------|-------|---------|------|
| 2.1 | Implement Students tab — full student list view with columns (Name, RFID, Sections), sort by name/RFID/section, real-time search box, add/edit/delete buttons | View | FR-1.6, FR-1.15 | [ ] |
| 2.2 | Implement student edit dialog — edit first name, last name, section assignments, "Change RFID Card" button (tap new card or type manually), RFID uniqueness validation | View | FR-1.6, FR-1.12 | [ ] |
| 2.3 | Implement Sections tab — section list with columns (Name, Type, Level, Day, Time), add/edit/delete section dialogs | View | FR-1.5 | [ ] |
| 2.4 | Reader disconnection detection — show error banner "RFID reader not detected" when no input received, allow manual name entry as fallback | View | UC-1 alt | [ ] |

##### 2B — Admin Panel

> The Admin Panel is implemented as the **Settings tab** in the main window. It is the single place for all privileged/configuration actions. It is protected by the admin PIN — the PIN dialog appears on app launch before the main window is accessible.

**Admin Panel screens and features:**

| Screen / Feature | Description | PRD Ref |
|-----------------|-------------|---------|
| PIN Entry Dialog | Shown on app launch; hashed PIN compared against settings table; lockout after 5 failed attempts | §5.2 |
| PIN Change | Field to enter current PIN + new PIN + confirm; updates hashed value in settings table | §5.2 |
| Absence Threshold | Numeric input to set the global absence alert threshold (default: 3); stored in settings table | FR-2.4 |
| Language Selector | Dropdown placeholder for Turkish / English (active in Phase 3); stored in settings table | FR-3.1 |
| Google Credentials Path | File picker to set path to service account JSON key; path stored in settings table (never the file itself) | §5.2 |
| Backup Database | Button that copies `attendance.db` to `backups/attendance_YYYY-MM-DD_HHMMSS.db` | §5.3 |
| Legacy Import | Google Sheet URL input + minimum attendance threshold input → preview table (total students, with/without RFID, attendance counts) → confirm/cancel | FR-2.7, FR-2.8 |

**Admin Panel tasks:**

| # | Task | Layer | PRD Ref | Done |
|---|------|-------|---------|------|
| 2.5 | Implement `pin_dialog.py` — PIN entry on app launch, hash comparison against settings table, lockout counter (block UI after 5 failed attempts) | Controller/View | §5.2 | [ ] |
| 2.6 | Implement `settings_tab.py` — PIN change form, absence threshold input, language dropdown (placeholder), Google credentials file picker, Backup Database button; all changes persist to settings table | View | §5.2, §5.3 | [ ] |
| 2.7 | Implement `import_controller.py` — read legacy Google Sheet (`name`, `rfid`, `D_YYYY_MM_DD` columns), apply minimum attendance threshold, exclude below-threshold students without RFID, return preview data and commit on confirm | Controller | FR-2.7, FR-2.8 | [ ] |
| 2.8 | Implement `import_preview_dialog.py` — Google Sheet URL input, threshold spinner, preview table (total/with RFID/without RFID/session counts), confirm/cancel buttons wired to import controller | View | FR-2.7, FR-2.8 | [ ] |
| 2.9 | Implement database backup — on "Backup Now" click, copy `attendance.db` to `backups/attendance_YYYY-MM-DD_HHMMSS.db`; show success/failure dialog | Controller | §5.3 | [ ] |

##### 2C — Infrastructure & Polish

| # | Task | Layer | PRD Ref | Done |
|---|------|-------|---------|------|
| 2.10 | Implement `logger.py` — local file logging with timestamps for: app startup/shutdown, card taps, session start/end, errors, imports, exports | Infra | §5.5 | [ ] |
| 2.11 | Implement error handling pass — wrap all DB writes in transactions, add try/except in every controller method, show user-friendly error dialogs for all failure modes (reader disconnected, DB error, import failure, etc.) | Controller/View | §5.3 | [ ] |

#### Phase 2 (Day 2) Exit Criteria
- [ ] Can CRUD students with RFID assignment, search, and sort
- [ ] Can reassign an RFID card to a different student (old card unlinked, new card validated for uniqueness)
- [ ] Can CRUD sections with type, level, and schedule
- [ ] Admin PIN dialog appears on app launch; wrong PIN rejected; 5 failures locks the UI
- [ ] Settings tab shows: PIN change, absence threshold, language dropdown, credentials path, Backup button, Legacy Import button
- [ ] Legacy Google Sheets import works with attendance threshold filtering and preview before commit
- [ ] Database backup creates a timestamped copy in `backups/` on button click
- [ ] All events are logged to a local log file with timestamps
- [ ] All errors show user-friendly dialogs — no raw tracebacks anywhere
- [ ] **MVP is fully usable end-to-end for the studio**

---

### Phase 3 — Post-MVP Enhancements (1–2 Weeks)
**Goal:** Reporting, Google Sheets export, absence alerts, language switching, and polish.

#### Tasks

| # | Task | Layer | PRD Ref | Done |
|---|------|-------|---------|------|
| 3.1 | Implement Reports tab — attendance reports filterable by section, date range, student, and status | View/Controller | FR-2.1 | [ ] |
| 3.2 | Implement attendance statistics — total present, total absent, attendance percentage per section and per student | Controller | FR-2.5 | [ ] |
| 3.3 | Implement Google Sheets export — authenticate with service account, push filtered attendance data, show success with link | Controller | FR-2.2 | [ ] |
| 3.4 | Implement CSV export fallback — export filtered reports as CSV when Google API is unavailable | Controller | FR-2.6 | [ ] |
| 3.5 | Implement Google Sheets student import — read student data (Name, Surname, Section) from a Google Sheet, preview with validation, create records without RFID (assigned on first tap) | Controller | FR-2.3 | [ ] |
| 3.6 | Implement absence alerts — highlight students exceeding configurable absence threshold in attendance view, click to see detailed history | View/Controller | FR-2.4 | [ ] |
| 3.7 | Implement Turkish/English language switching — language switcher in settings, all UI labels/buttons/messages update, selection persists between sessions | View | FR-3.1 | [ ] |
| 3.8 | Implement audio feedback — beep sound on card tap in addition to color-flash visual feedback | View | FR-3.2 | [ ] |
| 3.9 | Implement daily/weekly attendance calendar view | View | FR-3.3 | [ ] |
| 3.10 | Implement dark mode / light mode theming toggle | View | FR-3.4 | [ ] |

#### Phase 3 Exit Criteria
- [ ] Reports screen shows filterable attendance data with summary statistics
- [ ] Google Sheets export pushes attendance data successfully; CSV fallback works
- [ ] Students with excessive absences are visually highlighted
- [ ] UI language switches between Turkish and English; persists across sessions
- [ ] Audio feedback plays on card tap

---

## 4. Architecture Decisions

| Decision | Choice | Reason |
|----------|--------|--------|
| DB access pattern | Raw `sqlite3` module, no ORM | Minimal dependencies; project scope is simple enough; built-in Python module |
| GUI framework | CustomTkinter | PRD requirement; modern look over raw tkinter; single-window kiosk design |
| UI navigation | Tab-based single window | PRD §5.4 specifies single-window with tab/panel navigation |
| RFID input method | Hidden Entry widget + Enter key event | USB HID reader emulates keyboard; Enter key delimits card IDs |
| RFID card ID parsing | Configurable — trim prefix/suffix via settings | Different reader models output different formats (Risk 1 in PRD) |
| Session deduplication | Query before create; prompt to resume | PRD FR-1.10 alt flow: "Session already exists for this section and date" |
| Manual attendance flag | `method` column: 'RFID' or 'Manual' | PRD FR-1.9: manual overrides must be flagged for audit |
| Color-flash duration | 2–3 seconds, then revert | PRD FR-1.13 specification |
| DB journaling | WAL mode on every connection | PRD Risk 3: protects against corruption on power loss |
| Credential storage | File path in settings table; never committed to source | PRD §5.2: credentials must not be in plain text config |
| Legacy import filtering | Attendance threshold + RFID presence | PRD FR-2.7: exclude below-threshold students without RFID |
| PIN storage | Hashed in settings table | Security best practice; PRD §5.2 requires password/PIN protection |
| Logging | Local file with timestamps | PRD §5.5: log startup, card taps, errors, exports |

---

## 5. Project Structure

```text
Attendance_System/
├── specs/
│   ├── prd/
│   │   └── PRD-rfid-attendance-system.md
│   ├── templates/
│   │   ├── agents-template.md
│   │   ├── epic-template.md
│   │   ├── prd-template.md
│   │   ├── plan-template.md
│   │   └── story-template.md
│   ├── agents.md
│   └── plan.md                          # This file
├── src/
│   ├── models/
│   │   ├── __init__.py
│   │   ├── database.py                  # Connection manager, schema init, WAL mode
│   │   ├── student_model.py             # Student CRUD + card + section assignment
│   │   ├── section_model.py             # Section CRUD + enrolled students
│   │   ├── session_model.py             # Session lifecycle (create, close, query)
│   │   ├── attendance_model.py          # Attendance records (mark, toggle, query)
│   │   └── settings_model.py            # Key-value settings store
│   ├── controllers/
│   │   ├── __init__.py
│   │   ├── attendance_controller.py     # RFID tap processing, result routing
│   │   ├── session_controller.py        # Start/end session, live state, absent summary
│   │   ├── student_controller.py        # Registration, card reassignment, search/sort
│   │   ├── section_controller.py        # Section CRUD orchestration
│   │   └── import_controller.py         # Legacy Google Sheets import with threshold
│   ├── views/
│   │   ├── __init__.py
│   │   ├── app.py                       # Main window, full-screen, tab navigation
│   │   ├── attendance_tab.py            # Main attendance screen, RFID input, color flash
│   │   ├── students_tab.py              # Student list, search, sort, CRUD dialogs
│   │   ├── sections_tab.py              # Section list and CRUD dialogs
│   │   ├── settings_tab.py              # Settings, backup, import
│   │   ├── dialogs/
│   │   │   ├── __init__.py
│   │   │   ├── registration_dialog.py   # New student registration popup
│   │   │   ├── session_summary_dialog.py # End-session absent summary popup
│   │   │   ├── pin_dialog.py            # Admin PIN entry on launch
│   │   │   └── import_preview_dialog.py # Legacy import preview + confirm
│   │   └── components/
│   │       ├── __init__.py
│   │       └── student_list.py          # Reusable sortable/searchable student list
│   ├── utils/
│   │   ├── __init__.py
│   │   └── logger.py                    # File logging with timestamps
│   └── main.py                          # Entry point: init DB, show PIN dialog, launch app
├── logs/                                # Auto-created log files
├── backups/                             # Auto-created DB backups
├── attendance.db                        # SQLite database (WAL mode)
├── requirements.txt                     # customtkinter, gspread, google-auth
└── .gitignore                           # venv/, *.db, *.pyc, credentials JSON, logs/
```

---

## 6. Risks & Mitigations (Active)

| Risk | Severity | Mitigation |
|------|----------|-----------|
| USB HID reader format varies by model | High | Configurable card ID parser; "Test Reader" flow in settings; trim prefix/suffix |
| Rapid sequential scans merge input | Medium | Enter-key delimiter parsing; debounce timer; reject malformed IDs by expected length |
| SQLite corruption on power loss | High | WAL mode enabled; periodic auto-backups; manual "Backup Now" button |
| Google Sheets API auth failure | Low | Clear error messages; CSV fallback always available; validate creds on startup |
| 2-day MVP timeline is aggressive | High | Strict Phase 1 scope; defer reports/export/i18n/alerts to Phase 3; focus Day 1 on data + attendance, Day 2 on CRUD + admin |
| CustomTkinter rendering inconsistencies | Low | Test on Windows 10 and 11; stick to documented widget set; avoid raw tkinter mixing |

---

## 7. Testing Approach

- **Scope:** Manual end-to-end testing for MVP. Unit tests for model layer if time allows.
- **RFID simulation:** Without a physical reader, type a card ID string directly into the hidden Entry widget and press Enter — the app treats keyboard input identically to reader input.
- **DB verification:** Use DB Browser for SQLite or `sqlite3` CLI to inspect `attendance.db` after operations.
- **Key scenarios to verify manually:**
  - [ ] Start session → tap known card → green flash → student marked present in DB
  - [ ] Tap unknown card → red flash → registration dialog → complete → student created + attendance recorded
  - [ ] Tap same card twice in one session → yellow flash → "Already marked present"
  - [ ] Manual toggle Absent → Present → method is 'Manual' in DB
  - [ ] End session → popup shows correct present/absent counts → absent names listed → Confirm & Close finalizes
  - [ ] Create/edit/delete section → section persists in DB
  - [ ] Create/edit/delete student → student persists in DB → RFID column sortable
  - [ ] Reassign RFID card → old card unlinked → new card saved → duplicate card rejected
  - [ ] Legacy import → preview shows counts → threshold applied → import committed → students in DB
  - [ ] Admin PIN required on launch → wrong PIN rejected → correct PIN grants access
  - [ ] Run app for 1+ hour continuously → no crashes or memory leaks
  - [ ] Rapid card taps (< 500ms apart) → both recorded correctly, no merged IDs

---

## 8. Definition of Done

A feature is **done** when:
1. Code is written and follows the conventions in `specs/agents.md` (MVC separation, type hints, snake_case, etc.).
2. The feature works end-to-end on Windows 10/11.
3. All acceptance criteria from the corresponding PRD user story are met.
4. Error states show user-friendly dialogs (no raw tracebacks).
5. Relevant events are logged to the local log file with timestamps.
6. Data persists correctly in `attendance.db` (verified via DB inspection).
7. Manual testing of the scenario passes.

---

*Primary specification: `specs/prd/PRD-rfid-attendance-system.md`*  
*Agent guidelines: `specs/agents.md`*

---

## 9. Phase 3 — UX & Security Redesign (2026-02-20)

### Summary of Changes

Phase 3 reworks the main window, attendance flow, and access-control model based on
real-world studio usage feedback.

---

### 3.1 — Admin Panel (Ctrl+P)

| # | Change | Files |
|---|--------|-------|
| 3.1.1 | New `AdminPanel` CTkToplevel window opened by **Ctrl+P** | `views/admin_panel.py` *(new)* |
| 3.1.2 | PIN prompt (existing PinDialog) gates every admin panel open | `views/app.py`, `views/dialogs/pin_dialog.py` |
| 3.1.3 | Admin panel contains **Sections**, **Students**, **Settings** tabs | `views/admin_panel.py` |
| 3.1.4 | Main window **no longer shows Sections / Students / Settings tabs** — only the attendance view | `views/app.py` |
| 3.1.5 | **No PIN on app startup** — the app opens directly to the attendance screen | `views/app.py` (removed `_check_pin`) |

---

### 3.2 — Passive Attendance (Always-On RFID)

| # | Change | Files |
|---|--------|-------|
| 3.2.1 | Remove **Start Session / End Session** buttons and section selector dropdown from the attendance screen | `views/attendance_tab.py` |
| 3.2.2 | RFID entry widget is always active — no session state required to record a tap | `views/attendance_tab.py` |
| 3.2.3 | On tap → look up card → mark student **Present in every section scheduled for today** (section.day == today's weekday) | `controllers/attendance_controller.py` → `process_rfid_passive()` |
| 3.2.4 | Sessions are **auto-created** per section per day on first tap; subsequent taps reuse the same session | `models/session_model.py` → `get_or_create_session()` |
| 3.2.5 | Duplicate tap (student already fully marked today) → yellow flash with names of already-marked sections | `controllers/attendance_controller.py` |
| 3.2.6 | Attendance screen shows **"Today's Log"**: all taps for the current calendar day, newest first, with student name, section, status, method, timestamp | `views/attendance_tab.py`, `models/attendance_model.py` → `get_today_attendance_with_details()` |
| 3.2.7 | Info bar shows which sections are **scheduled for today** based on section day field | `views/attendance_tab.py` |

---

### 3.3 — Student Registration via Unknown Card

| # | Change | Files |
|---|--------|-------|
| 3.3.1 | Unknown card tap → **RegistrationDialog** opens (same as before, but redesigned) | `views/attendance_tab.py` |
| 3.3.2 | RegistrationDialog now shows **multiple section checkboxes** instead of a single dropdown | `views/dialogs/registration_dialog.py` |
| 3.3.3 | On save, calls `register_student_with_sections(first, last, card_id, [sec_ids])` | `controllers/student_controller.py` → `register_student_with_sections()` |
| 3.3.4 | After registration, card is immediately re-processed via `process_rfid_passive()` to mark the new student present in today's sections | `views/attendance_tab.py` |
| 3.3.5 | There is **no manual "Add Student" button** — all student creation is triggered by an unknown RFID scan | `views/attendance_tab.py`, `views/dialogs/registration_dialog.py` |

---

### 3.4 — Fix: Section Delete FK Constraint

| # | Change | Files |
|---|--------|-------|
| 3.4.1 | `delete_section()` now cascades: deletes **attendance → sessions → student_sections → section** in correct FK order | `models/section_model.py` |
| 3.4.2 | Added `get_sections_for_student_on_day(student_id, day)` helper for passive tap processing | `models/section_model.py` |

---

### 3.5 — Phase 3 Exit Criteria

- [ ] App opens directly to attendance screen (no startup PIN)
- [ ] Pressing Ctrl+P prompts for PIN; correct PIN opens admin panel; wrong PIN closes the dialog
- [ ] Admin panel has Sections, Students, Settings tabs fully functional
- [ ] Section delete no longer fails with FK error
- [ ] Tapping an RFID card marks the student present in all sections scheduled for today — without pressing any session buttons
- [ ] Duplicate tap shows yellow flash with "already marked" message
- [ ] Unknown card tap opens RegistrationDialog with multi-section checkboxes; saving registers the student and marks them present
- [ ] "Today's Log" list reflects all taps for the current calendar day
- [ ] Sections info bar shows all sections scheduled for today's weekday


---

## Phase 4 — Stability, UX Polish & Manual Attendance (completed 2026-02-20)

### Summary of Changes

Phase 4 addresses rendering bugs on Windows, adds UX quality-of-life features (simulation, listening indicator), hardens RFID input validation, and adds a full manual attendance editor accessible from the admin panel.

---

### 4.1 — Window & Rendering Fixes

| # | Change | Files |
|---|--------|-------|
| 4.1.1 | App changed from **fullscreen** to **windowed** (1280×800, resizable, min 900×600) | `views/app.py` |
| 4.1.2 | `AdminPanel` and `PinDialog` now defer all window-management (`grab_set`, `geometry`, `lift`, `focus_force`) to `after(50, _activate)` — fixes blank/tiny render on Windows | `views/admin_panel.py`, `views/dialogs/pin_dialog.py` |
| 4.1.3 | Removed shared `pad` dict from `PinDialog._build_ui()` — it caused `TypeError: got multiple values for keyword argument 'pady'` | `views/dialogs/pin_dialog.py` |

---

### 4.2 — Attendance Tab UX

| # | Change | Files |
|---|--------|-------|
| 4.2.1 | `● LISTENING` / `◌ IDLE` indicator added to sections bar — shows RFID entry focus state in real time | `views/attendance_tab.py` |
| 4.2.2 | 10-digit numeric guard added to `_on_rfid_enter()` — rejects anything that is not exactly 10 decimal digits | `views/attendance_tab.py` |
| 4.2.3 | **Simulation panel** (marked `#DELETABLE`) added — amber toggle button shows a dev input row where a card ID can be typed and submitted through the real processing pipeline | `views/attendance_tab.py` |
| 4.2.4 | Card processing logic extracted to `_process_card(card_id)` — called by both `_on_rfid_enter` and `_sim_submit` to avoid duplication and focus conflicts | `views/attendance_tab.py` |
| 4.2.5 | `<FocusOut>` refactored: `_on_rfid_focus_out()` skips refocus when sim panel is visible; `_try_refocus()` backs off when a modal `grab` is active — eliminates LISTENING↔IDLE loop and admin-panel freeze | `views/attendance_tab.py` |

---

### 4.3 — Manual Attendance Editor

| # | Change | Files |
|---|--------|-------|
| 4.3.1 | `get_student_attendance_overview(student_id, date_str)` — returns per-section attendance status for any date | `controllers/attendance_controller.py` |
| 4.3.2 | `set_student_attendance(student_id, section_id, date_str, target_status)` — sets Present/Absent directly, auto-creating session if needed | `controllers/attendance_controller.py` |
| 4.3.3 | New `ManualAttendanceDialog` — date picker + per-section Present/Absent buttons; changes saved immediately | `views/dialogs/manual_attendance_dialog.py` *(new)* |
| 4.3.4 | **Attendance** button added to each student row in `StudentsTab` (admin panel) — opens `ManualAttendanceDialog` | `views/students_tab.py` |

---

### 4.4 — Phase 4 Exit Criteria

- [x] App opens in a normal window (not fullscreen)
- [x] Admin panel and PIN dialog render fully and come to front on Windows
- [x] `● LISTENING` indicator accurately reflects RFID entry focus
- [x] Card IDs that are not exactly 10 digits are rejected with a red flash
- [x] Sim panel allows typing a card ID to simulate a hardware tap
- [x] No focus loop between RFID entry and sim panel
- [x] Admin panel opens/closes without event-loop thrashing
- [x] Clicking **Attendance** on a student row opens the manual editor
- [x] Manual editor shows per-section status for any date
- [x] Clicking Present/Absent saves immediately to the DB

---

## Phase 5 — Feature Expansion & Hardening (2026-02-22 → 2026-03-01)

### Summary of Changes

Phase 5 adds localization, inactive student tracking, auto-backup, secure PIN upgrade, Google Sheets export, daily reports, a section assignment dialog for zero-section students, and numerous bug fixes.

---

### 5.1 — Localization & Locale Independence

| # | Change | Files |
|---|--------|-------|
| 5.1.1 | Lightweight i18n system (`utils/localization.py`) with English + Turkish string table | `utils/localization.py` *(new)* |
| 5.1.2 | `t(key)` translator, `set_language()`, `get_language()`, `load_from_settings()` | `utils/localization.py` |
| 5.1.3 | Live language switching from Settings tab — applies to attendance tab without restart | `views/settings_tab.py`, `views/attendance_tab.py` |
| 5.1.4 | Locale-independent weekday/month helpers (`_english_weekday`, `_english_month`) to avoid OS locale issues | `controllers/attendance_controller.py`, `views/attendance_tab.py` |

---

### 5.2 — Inactive Student System

| # | Change | Files |
|---|--------|-------|
| 5.2.1 | `is_inactive` column added to `students` table; schema version bumped to 2 | `models/database.py` |
| 5.2.2 | `refresh_inactive_status_all()` recomputes inactive flags for all students | `controllers/attendance_controller.py` |
| 5.2.3 | Inactive students show purple flash on RFID tap and red-tinted row in Students tab | `views/attendance_tab.py`, `views/students_tab.py` |
| 5.2.4 | "Hide inactive students" checkbox in Students tab filter bar | `views/students_tab.py` |
| 5.2.5 | Settings section 9: Inactive threshold config + manual refresh button | `views/settings_tab.py` |

---

### 5.3 — Auto-Backup & Restore

| # | Change | Files |
|---|--------|-------|
| 5.3.1 | `utils/backup.py` — `create_backup()` with timestamped copies; MAX_BACKUPS=10 pruning | `utils/backup.py` *(new)* |
| 5.3.2 | Auto-backup every 4 hours via `App._schedule_auto_backup()` | `views/app.py` |
| 5.3.3 | Restore from backup — file picker + safety backup + overwrite + app close | `views/settings_tab.py` |

---

### 5.4 — Secure PIN Hashing Upgrade

| # | Change | Files |
|---|--------|-------|
| 5.4.1 | `utils/pin_utils.py` — PBKDF2-HMAC-SHA256 with 260K iterations + 16-byte salt | `utils/pin_utils.py` *(new)* |
| 5.4.2 | Backward-compatible `verify_pin()` detects legacy SHA-256 hashes | `utils/pin_utils.py` |
| 5.4.3 | All PIN hashing calls centralised — PinDialog and SettingsTab import from `pin_utils` | `views/dialogs/pin_dialog.py`, `views/settings_tab.py` |

---

### 5.5 — Section Assignment Dialog

| # | Change | Files |
|---|--------|-------|
| 5.5.1 | `SectionAssignDialog` for known students with zero sections | `views/dialogs/section_assign_dialog.py` *(new)* |
| 5.5.2 | `NO_SECTIONS` result type added to `TapResultType` enum | `controllers/attendance_controller.py` |
| 5.5.3 | Attendance tab handles `NO_SECTIONS` by opening assign dialog + re-processing tap | `views/attendance_tab.py` |

---

### 5.6 — Google Sheets Summary Push & Daily Report

| # | Change | Files |
|---|--------|-------|
| 5.6.1 | `push_summary_to_sheets(url)` — push per-student attendance summary to Google Spreadsheet | `controllers/attendance_controller.py` |
| 5.6.2 | Settings section 8: Google Sheets Summary — URL input + push button + background thread | `views/settings_tab.py` |
| 5.6.3 | `get_daily_report(date_str)` — per-section attendance breakdown excluding inactive students | `controllers/attendance_controller.py` |
| 5.6.4 | Settings section 10: Daily Report popup with summary cards and section table | `views/settings_tab.py` |

---

### 5.7 — Additional Changes

| # | Change | Files |
|---|--------|-------|
| 5.7.1 | Section mode toggle setting (controls section filtering in attendance view) | `views/settings_tab.py` |
| 5.7.2 | Students tab page size reduced from 50 to 20 rows | `views/students_tab.py` |
| 5.7.3 | PyInstaller build config (`attendance.spec`) added | `attendance.spec` |
| 5.7.4 | `requirements.txt`, `requirements-dev.txt`, `LICENSE`, `README.md` added | project root |
| 5.7.5 | Bug fixes: CTkEntry cursor param, RFID input handling, Sheets push, enrollment attendance | multiple |

---

### 5.8 — Phase 5 Exit Criteria

- [x] Language switching works live from Settings (English ↔ Turkish)
- [x] Weekday matching is locale-independent — works on Turkish Windows
- [x] Inactive students auto-flagged after N consecutive absences
- [x] Auto-backup runs every 4 hours; manual backup + restore available
- [x] PIN hashing upgraded to PBKDF2 with backward compatibility
- [x] Students with zero sections get a section assignment dialog on tap
- [x] Google Sheets summary push works end-to-end
- [x] Daily report shows per-section breakdown
- [x] Students tab loads 20 rows per page
- [x] README, LICENSE, and build config present
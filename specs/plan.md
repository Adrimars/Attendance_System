# Implementation Plan — RFID Dance Class Attendance System

**Project:** RFID Dance Class Attendance System v1.1  
**Developer:** Orkun Arslanturk  
**PRD:** `specs/prd/PRD-rfid-attendance-system.md`  
**Status:** Draft  
**Last Updated:** 2026-02-20

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
| 1.1 | Create project skeleton: folder structure, `main.py` entry point, `requirements.txt`, `.gitignore` | Infra | §9.2, §9.3 | [ ] |
| 1.2 | Implement `database.py` — connection manager with WAL mode, schema initialization (all 6 tables from agents.md §3), migration support | Model | FR-1.4 | [ ] |
| 1.3 | Implement `student_model.py` — CRUD operations: create, get_by_id, get_by_card_id, get_all, update, delete, assign/remove section, reassign card | Model | FR-1.3, FR-1.6, FR-1.7, FR-1.12 | [ ] |
| 1.4 | Implement `section_model.py` — CRUD operations: create, get_by_id, get_all, update, delete, get_enrolled_students | Model | FR-1.5 | [ ] |
| 1.5 | Implement `session_model.py` — create session, get active session, close session, check for existing session (same section + date) | Model | FR-1.10, FR-1.11 | [ ] |
| 1.6 | Implement `attendance_model.py` — mark present (RFID/Manual), mark absent, toggle status, get attendance by session, check duplicate tap | Model | FR-1.2, FR-1.9 | [ ] |
| 1.7 | Implement `settings_model.py` — get/set key-value pairs (admin PIN, absence threshold, language, credentials path) | Model | §5.2 | [ ] |
| 1.8 | Implement `attendance_controller.py` — process card tap (lookup → known/unknown/duplicate), return result type + student info for UI feedback | Controller | FR-1.1, FR-1.2, FR-1.3, FR-1.13 | [ ] |
| 1.9 | Implement `session_controller.py` — start session (validate section, check existing, create), end session (generate absent summary, close), get live attendance state | Controller | FR-1.10, FR-1.11, FR-1.14 | [ ] |
| 1.10 | Implement `student_controller.py` — register new student from unknown card, reassign RFID card (validate uniqueness, unlink old), search/sort students | Controller | FR-1.3, FR-1.12, FR-1.15 | [ ] |
| 1.11 | Implement `section_controller.py` — section CRUD orchestration with validation | Controller | FR-1.5 | [ ] |
| 1.12 | Set up `app.py` — main CustomTkinter window, full-screen launch, force-focus, tab-based navigation skeleton (Attendance, Students, Sections, Settings tabs) | View | §5.4 | [ ] |
| 1.13 | Implement Attendance tab — section selector dropdown, Start/End Session buttons, hidden RFID input entry widget (focused, captures keyboard stream, fires on Enter), live student list (name + status), color-flash background (Green/Red/Yellow for 2–3s) | View | FR-1.8, FR-1.10, FR-1.11, FR-1.13, FR-1.14 | [ ] |
| 1.14 | Implement registration dialog — popup triggered by unknown card tap, fields: first name, last name, confirm/cancel buttons, optional section assignment | View | FR-1.3 | [ ] |
| 1.15 | Implement manual attendance toggle — clickable Present/Absent status in the live student list, sets `method = 'Manual'` | View | FR-1.9 | [ ] |
| 1.16 | Implement End Session popup — summary showing total enrolled, present count, absent count, named absent list, last-minute manual toggle, Confirm & Close button | View | FR-1.11 | [ ] |

#### Phase 1 (Day 1) Exit Criteria
- [ ] App launches full-screen on Windows with tab navigation
- [ ] Can create a section, start a session for it, tap an RFID card, and see the student marked present with a green flash
- [ ] Unknown card tap opens registration dialog; completing it creates the student and records attendance
- [ ] Duplicate tap shows yellow flash and "Already marked" message
- [ ] Can manually toggle a student's attendance (flagged as Manual in DB)
- [ ] End Session shows absent summary popup with correct counts
- [ ] All data persists in `attendance.db` with WAL mode

---

### Phase 2 — MVP Completion (Day 2)
**Goal:** Student/section management screens, RFID card reassignment, legacy import, admin PIN protection, and polish. MVP is fully usable.

#### Tasks

| # | Task | Layer | PRD Ref | Done |
|---|------|-------|---------|------|
| 2.1 | Implement Students tab — full student list view with columns (Name, RFID, Sections), sort by name/RFID/section, real-time search box, add/edit/delete buttons | View | FR-1.6, FR-1.15 | [ ] |
| 2.2 | Implement student edit dialog — edit first name, last name, section assignments, "Change RFID Card" button (tap new card or type manually), RFID uniqueness validation | View | FR-1.6, FR-1.12 | [ ] |
| 2.3 | Implement Sections tab — section list with columns (Name, Type, Level, Day, Time), add/edit/delete section dialogs | View | FR-1.5 | [ ] |
| 2.4 | Implement Settings tab — admin PIN change, absence threshold config, language selector placeholder, Google credentials path, Backup Database button | View | §5.2, §5.3 | [ ] |
| 2.5 | Implement admin PIN protection — PIN entry dialog on app launch, PIN stored hashed in settings table, lockout after 5 failed attempts | Controller/View | §5.2 | [ ] |
| 2.6 | Implement `import_controller.py` — legacy Google Sheets import: read sheet with `name`, `rfid`, `D_YYYY_MM_DD` columns, apply minimum attendance threshold, exclude below-threshold students without RFID, preview before commit | Controller | FR-2.7, FR-2.8 | [ ] |
| 2.7 | Implement legacy import UI — import button in Settings or admin panel, Google Sheet URL input, preview table (total students, with/without RFID, attendance counts), threshold input, confirm/cancel | View | FR-2.7, FR-2.8 | [ ] |
| 2.8 | Implement database backup — copy `attendance.db` to timestamped backup file on button click | Controller | §5.3 | [ ] |
| 2.9 | Implement `logger.py` — local file logging with timestamps for: app startup/shutdown, card taps, session start/end, errors, imports, exports | Infra | §5.5 | [ ] |
| 2.10 | Implement error handling pass — wrap all DB writes in transactions, add try/catch in every controller method, show user-friendly error dialogs for all failure modes (reader disconnected, DB error, etc.) | Controller/View | §5.3 | [ ] |
| 2.11 | Reader disconnection detection — show error banner "RFID reader not detected" when no input received, allow manual name entry as fallback | View | UC-1 alt | [ ] |

#### Phase 2 (Day 2) Exit Criteria
- [ ] Can CRUD students with RFID assignment, search, and sort
- [ ] Can reassign an RFID card to a different student (old card unlinked, new card validated for uniqueness)
- [ ] Can CRUD sections with type, level, and schedule
- [ ] Admin PIN is required on app launch; incorrect PIN shows error
- [ ] Legacy Google Sheets import works with attendance threshold filtering and preview
- [ ] Database backup creates a timestamped copy on button click
- [ ] All events are logged to a local log file
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

# Agent Guidelines — RFID Dance Class Attendance System

> Project-specific rules and role definitions for AI agents working on the RFID Dance Class Attendance System project.

**Project:** RFID Dance Class Attendance System v1.1  
**Stack:** Python 3.10+, CustomTkinter, SQLite3, gspread  
**Last Updated:** 2026-02-20

---

## 1. Project Context

### What This Project Is
A Windows desktop kiosk application that automates attendance tracking for a dance studio (~200 students, ~5 sections) using USB HID RFID card scanning. Students tap a card to mark themselves present; unknown cards trigger instant registration. Administrators manage sections, sessions, students, and export reports to Google Sheets or CSV.

### Key Constraints
- **Desktop only:** Windows 10/11 exclusively. No web, mobile, or cloud deployment.
- **Offline-first:** Core attendance must work with zero internet. Google Sheets features only require internet during export/import.
- **Single-instance:** Only one running instance per machine at a time.
- **Single operator:** No multi-user concurrent access or role-based auth (single admin role).
- **USB HID RFID only:** Reader emulates a keyboard — card ID arrives as keystrokes followed by Enter. No driver installation allowed.

### Tech Stack (Non-Negotiable)
| Layer | Technology | Notes |
|-------|-----------|-------|
| Language | Python 3.10+ | Type hints required throughout |
| GUI Framework | CustomTkinter | Modern tkinter wrapper; single-window, tab-based navigation |
| Database | SQLite3 (built-in) | WAL mode enabled; single `attendance.db` file |
| Google Integration | gspread + google-auth | Phase 2 only; service account JSON key |
| Packaging | PyInstaller (future) | Not required for MVP |

**Do NOT introduce:** web frameworks (Flask, FastAPI, Django), ORMs (SQLAlchemy), cloud databases, React/JS tooling, any GUI framework other than CustomTkinter, or any dependency that requires a separate installer.

---

## 2. Code Conventions

### Python Rules
- Python 3.10+ features and type hints on all function signatures.
- No bare `except` clauses — always catch specific exception types.
- All errors shown to user via dialog boxes — never raw stack traces in the UI.
- Logging to a local log file with timestamps for: startup, card taps, errors, exports.
- Use SQLite WAL mode (`PRAGMA journal_mode=WAL`) on every database connection.

### Architecture Rules (MVC)
- **Model layer** (`models/`): SQLite access only. No UI imports. No business logic.
- **View layer** (`views/`): CustomTkinter widgets only. No direct database access.
- **Controller layer** (`controllers/`): Business logic, attendance processing, card registration, report generation, Google Sheets sync. Bridges models and views.
- Never mix layers — views call controllers, controllers call models.

### Custom Architecture / Patterns
| Pattern | Purpose |
|---------|---------|
| Hidden text entry widget | Captures USB HID keyboard stream from RFID reader; fires on Enter key event |
| Manual flag on attendance records | Distinguishes RFID taps from administrator overrides for audit purposes |
| Color-flash feedback | Main screen background flashes Green/Red/Yellow for 2–3s then reverts |
| WAL + periodic backup | Protects against SQLite corruption on power loss |

### Naming Conventions
| Item | Convention | Example |
|------|-----------|---------|
| Classes | PascalCase | `AttendanceController`, `StudentModel` |
| Functions/Methods | snake_case | `get_student_by_rfid()` |
| Files/Modules | snake_case | `attendance_controller.py` |
| Constants | UPPER_SNAKE_CASE | `ABSENCE_THRESHOLD`, `DB_PATH` |
| Database columns | snake_case | `card_id`, `session_id` |

### Styling Guidelines
- CustomTkinter themed widgets only; no raw tkinter styling.
- Minimum button/touch target size: 44×44 pixels (kiosk-style usability).
- Large fonts and high-contrast colors — readable at a distance.
- Application launches in full-screen mode and forces window focus on startup.
- Color-coded feedback: **Green** = present, **Red** = unknown card, **Yellow** = duplicate tap.

---

## 3. Data Model

All agents must adhere to these SQLite schemas:

```sql
-- Students
CREATE TABLE students (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    first_name  TEXT NOT NULL,
    last_name   TEXT NOT NULL,
    card_id     TEXT UNIQUE,           -- NULL until RFID card is assigned
    created_at  TEXT NOT NULL          -- ISO-8601 timestamp
);

-- Sections
CREATE TABLE sections (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT NOT NULL,
    type        TEXT NOT NULL,         -- 'Technique' | 'Normal'
    level       TEXT NOT NULL,         -- 'Beginner' | 'Intermediate' | 'Advanced'
    day         TEXT NOT NULL,         -- e.g., 'Monday'
    time        TEXT NOT NULL          -- e.g., '18:00'
);

-- Student ↔ Section assignments (many-to-many)
CREATE TABLE student_sections (
    student_id  INTEGER NOT NULL REFERENCES students(id),
    section_id  INTEGER NOT NULL REFERENCES sections(id),
    PRIMARY KEY (student_id, section_id)
);

-- Sessions
CREATE TABLE sessions (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    section_id  INTEGER NOT NULL REFERENCES sections(id),
    date        TEXT NOT NULL,         -- ISO-8601 date (YYYY-MM-DD)
    start_time  TEXT NOT NULL,         -- ISO-8601 timestamp
    end_time    TEXT,                  -- NULL while active
    status      TEXT NOT NULL DEFAULT 'active'  -- 'active' | 'closed'
);

-- Attendance records
CREATE TABLE attendance (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id  INTEGER NOT NULL REFERENCES sessions(id),
    student_id  INTEGER NOT NULL REFERENCES students(id),
    status      TEXT NOT NULL,         -- 'Present' | 'Absent'
    method      TEXT NOT NULL,         -- 'RFID' | 'Manual'
    timestamp   TEXT NOT NULL,         -- ISO-8601 timestamp
    UNIQUE (session_id, student_id)
);

-- Settings (key-value)
CREATE TABLE settings (
    key         TEXT PRIMARY KEY,
    value       TEXT NOT NULL
);
-- Expected keys: 'absence_threshold', 'admin_pin', 'language', 'google_credentials_path'
```

### Validation Rules
- `card_id` must be unique across all students (one card per student).
- A session for the same `section_id` + `date` must not be duplicated (prompt to resume instead).
- When reassigning a card, the old `card_id` must be set to NULL before the new one is saved.
- Students below the configured absence threshold AND without a `card_id` are excluded from legacy imports.
- All timestamps stored as ISO-8601 strings in UTC.

---

## 4. Performance Requirements

| Metric | Target | How to Verify |
|--------|--------|---------------|
| Attendance logged after tap | < 500ms | Manual timing during testing |
| UI feedback (name display) | < 300ms | Manual timing during testing |
| Rapid sequential scans | No data loss at < 500ms between taps | Simulate rapid taps in QA |
| DB query (attendance records) | < 1s for up to 100,000 rows | Run query with large dataset |
| Continuous uptime | 8+ hours, 0 crashes | Extended pilot run |
| Scalability | 1,000+ students, 50+ sections | Seed DB and verify query speed |

---

## 5. Agent Role Definitions

### PM Agent
**Context:** You are the product manager for the RFID Dance Class Attendance System.  
**Your responsibilities:**
- Write and refine PRD sections, epics, and user stories.
- Decompose features into acceptance criteria using Given/When/Then format.
- Prioritize Phase 1 (MVP) vs Phase 2 scope strictly as defined in the PRD.

**Rules:**
- Always reference the PRD at `specs/prd/PRD-rfid-attendance-system.md`.
- Phase 1 (MVP) features must be complete before Phase 2 work begins.
- Acceptance criteria must be verifiable and testable.
- Never add scope that contradicts the "Out of Scope" section (no web, no mobile, no billing).

**Key files:** `specs/prd/PRD-rfid-attendance-system.md`, `specs/templates/`

---

### Developer Agent
**Context:** You are a Python desktop developer building the RFID Dance Class Attendance System.  
**Your responsibilities:**
- Implement user stories following the MVC architecture.
- Write application code with full type hints and docstrings.
- Handle all errors gracefully — display user-friendly dialogs, never raw tracebacks.

**Rules:**
- Follow the tech stack exactly (Section 1) — CustomTkinter, SQLite3, Python 3.10+.
- Follow MVC separation strictly (Section 2) — no layer crossover.
- RFID input is captured via a hidden/focused text entry widget listening for the Enter key.
- All attendance writes must use database transactions to prevent partial saves.
- Manual attendance overrides must set `method = 'Manual'` in the attendance table.
- Color-flash feedback (Green/Red/Yellow) must revert after exactly 2–3 seconds.
- Enable SQLite WAL mode on every database connection open.
- Log all card taps, errors, session start/end, and exports to a timestamped local log file.

**Key files:** `specs/prd/PRD-rfid-attendance-system.md`, `specs/agents.md`

---

### QA Agent
**Context:** You are a QA engineer testing the RFID Dance Class Attendance System on Windows 10/11.  
**Your responsibilities:**
- Verify all acceptance criteria from user stories.
- Test RFID edge cases: rapid sequential taps, duplicate taps, unknown cards, disconnected reader.
- Verify data integrity in the SQLite database after each operation.

**Rules:**
- Test on Windows 10 or 11 only — no other OS.
- Verify performance targets from Section 4 (response times, uptime).
- Confirm manual attendance overrides are flagged with `method = 'Manual'` in the DB.
- Confirm unknown card tap opens registration dialog and auto-records attendance on completion.
- Confirm color flash (Green/Red/Yellow) appears and reverts within 2–3 seconds.
- Confirm "End Session" popup shows correct present/absent counts and named absent list.
- Confirm legacy Google Sheets import correctly excludes students below the attendance threshold who have no RFID.
- Verify CSV export works when Google Sheets API is unavailable.
- All error states (reader disconnected, DB failure, API error) must show a user-friendly dialog — never a raw traceback.

**Key files:** `specs/prd/PRD-rfid-attendance-system.md`, `specs/agents.md`

---

## 6. Project Structure Reference

```text
Attendance_System/
├── specs/
│   ├── prd/
│   │   └── PRD-rfid-attendance-system.md   # Primary specification
│   ├── templates/                           # PRD, epic, story, agent templates
│   └── agents.md                           # This file
├── src/
│   ├── models/                             # SQLite data access (Student, Section, Session, Attendance, Settings)
│   ├── views/                              # CustomTkinter UI (Attendance, Students, Sections, Reports, Settings tabs)
│   ├── controllers/                        # Business logic (attendance processing, RFID handling, exports)
│   └── main.py                             # Application entry point; launches full-screen window
├── logs/                                   # Timestamped application log files
├── attendance.db                           # SQLite database (WAL mode)
└── requirements.txt                        # customtkinter, gspread, google-auth
```

---

## 7. Common Mistakes to Avoid

| Mistake | Why It's Wrong | Do This Instead |
|---------|---------------|-----------------|
| Accessing the DB directly from a view | Violates MVC; makes views untestable and tightly coupled | Views call controller methods; controllers call model methods |
| Using bare `except:` | Swallows unexpected errors silently; hides bugs | Catch specific exceptions (`sqlite3.Error`, `gspread.exceptions.APIError`, etc.) |
| Showing raw stack traces in the UI | Breaks usability for non-technical admins (Elif) | Show a localized, user-friendly error dialog and log the full trace to file |
| Creating a new session without checking for an existing one | Creates duplicate sessions for the same section + date | Query for existing session first; prompt to resume or create new |
| Writing attendance without a transaction | Partial writes on crash corrupt data | Wrap all multi-step DB writes in `BEGIN / COMMIT / ROLLBACK` transactions |
| Hardcoding the RFID card ID length/format | Different reader models output different formats | Use a configurable parser; trim prefix/suffix via settings |
| Importing all students from legacy sheet without threshold filter | Floods DB with inactive students who will never tap in | Apply the admin-configured minimum attendance threshold before committing import |
| Storing Google API credentials in plain text config | Security risk — credentials exposed in version control | Store credential path in settings; never commit the JSON key file |

---

*This file is the single source of truth for agent behavior on this project. When in doubt, check the primary specification at `specs/prd/PRD-rfid-attendance-system.md`.*

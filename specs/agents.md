# Agent Guidelines — RFID Dance Class Attendance System

> Project-specific behavior and quality rules for AI agents working in this repository.

**Project:** RFID Dance Class Attendance System v1.2  
**Stack:** Python 3.10+, CustomTkinter, SQLite3, gspread  
**Last Updated:** 2026-03-02

---

## 1. Project Context

### What This Project Is
A Windows desktop kiosk application for dance class attendance. Students tap RFID cards; admins manage students, sections, sessions, settings, imports, and daily reporting.

### Non-Negotiable Constraints
- Windows desktop only (10/11).
- Offline-first attendance; internet required only for Google Sheets operations.
- Single local SQLite database, no cloud DB.
- CustomTkinter UI only; keep existing visual style.
- Strict MVC separation (`views -> controllers -> models`).

### Forbidden Introductions
- No web frameworks, no ORMs, no new architecture layers.
- No new dependencies unless explicitly approved.
- No direct model access inside views.

---

## 2. Code Conventions

### Python Rules
- Use Python 3.10+ syntax and type hints for public methods.
- Catch specific exceptions; avoid bare `except`.
- Show user-friendly error dialogs; log technical details.
- Keep changes minimal and scoped to the requested task.

### Database Rules
- Use `models.database.get_connection()` for all DB writes.
- Preserve WAL mode and foreign key behavior.
- Never break existing schema compatibility without migration.
- Keep `settings` keys stable unless coordinated changes are made.

### UI Rules
- Keep RFID input workflow uninterrupted and focused.
- Preserve fast feedback states (green/red/yellow/purple flows).
- Reuse existing dialogs/tabs/components before creating new ones.

---

## 3. Architecture Rules

### Layer Responsibilities
- **Models:** data access only.
- **Controllers:** business logic and orchestration.
- **Views:** user interaction and rendering only.
- **Utils:** shared infrastructure (backup, localization, logging, PIN hashing).

### Current Critical Files
- Entry: `src/main.py`
- Attendance flow: `src/controllers/attendance_controller.py`, `src/views/attendance_tab.py`
- Session logic: `src/controllers/session_controller.py`
- Admin UI: `src/views/admin_panel.py`, `src/views/settings_tab.py`
- Data schema/init: `src/models/database.py`
- PIN security: `src/utils/pin_utils.py`

---

## 4. Role Definitions

### PM Agent
Responsibilities:
- Keep PRD and implementation plan aligned with actual repo state.
- Define clear scope boundaries and acceptance criteria.
- Prioritize operational stability over feature expansion.

Deliverables:
- Updated PRD, plan, changelog entries, and scoped story breakdowns.

### Developer Agent
Responsibilities:
- Implement requested features/fixes with strict MVC discipline.
- Preserve compatibility with existing attendance workflows.
- Add defensive error handling and maintain localization patterns.

Definition of quality:
- No regressions in RFID flow, admin PIN flow, and DB persistence.

### QA Agent
Responsibilities:
- Validate attendance scenarios (known/unknown/duplicate/no-section cards).
- Validate admin actions (CRUD, settings, import, backup/restore).
- Verify all user-visible failures are clear and non-technical.

Test focus:
- Windows runtime behavior, data integrity, and resilience under repetitive use.

---

## 5. Common Mistakes to Avoid

| Mistake | Why It Breaks Things | Correct Action |
|---|---|---|
| View directly calling model | Breaks MVC and makes testing hard | Route through controller |
| Raw traceback in UI | Poor UX for operators | Show message dialog + log details |
| Unscoped refactor during small task | Causes regressions | Apply minimal targeted edits |
| Direct SQL outside model layer | Spreads data logic and risk | Keep SQL in model modules |
| Changing settings key names casually | Breaks existing flows | Preserve or migrate keys explicitly |

---

## 6. Source of Truth

- Product requirements: `specs/prd/PRD-rfid-attendance-system.md`
- Current implementation status: `specs/CURRENT_STATE.md`
- Project roadmap: `specs/plan.md`
- Completed work history: `specs/CHANGELOG.md`

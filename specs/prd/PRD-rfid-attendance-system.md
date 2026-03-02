# Product Requirements Document (PRD)

**Project Name:** RFID Dance Class Attendance System  
**Version:** 1.2  
**Status:** Active  
**Date:** 2026-03-02  
**Author:** Orkun Arslanturk  
**Last Updated:** 2026-03-02

---

## 1. Overview

### 1.1 Purpose
Build and maintain a Windows desktop attendance kiosk for dance classes using USB HID RFID cards, with fast daily operation for non-technical staff and reliable local data storage.

### 1.2 Problem Statement
Manual attendance tracking is slow, error-prone, and difficult to report. The studio needs a single-screen desktop workflow that records attendance in seconds and keeps data searchable and exportable.

### 1.3 Product Goals
- **Goal 1:** Mark attendance within 1 tap and under 500ms response time.
- **Goal 2:** Maintain accurate local records with robust offline operation.
- **Goal 3:** Reduce admin workload via section automation, import, backup, and reporting utilities.

### 1.4 Current Product State
As of 2026-03-02, core attendance flow, admin panel, localization, backup/restore, inactive-student logic, and Google Sheets import/summary features are implemented and operational in the current codebase.

---

## 2. Users

### Persona 1: Studio Administrator (Primary)
- Runs daily attendance operations during classes.
- Needs clear, large UI controls and minimal setup.
- Uses registration/manual override workflows when students forget cards.

### Persona 2: Technical Assistant (Secondary)
- Configures PIN, thresholds, credentials, backups, and imports.
- Troubleshoots RFID/device/configuration issues.

---

## 3. Scope

### 3.1 In Scope (Implemented)
- RFID attendance via USB HID keyboard-emulation input.
- Unknown-card registration and section assignment.
- Auto-session behavior for today’s scheduled sections.
- Manual attendance overrides.
- Admin panel with PIN protection (`Ctrl+P`).
- Student and section CRUD.
- Legacy Google Sheets import preview + commit.
- Google Sheets attendance summary push.
- English/Turkish localization.
- Backup now, restore, and scheduled auto-backup.
- Inactive student status calculation and visibility.
- Daily report generation dialog.

### 3.2 In Scope (Next)
- CSV export fallback for reporting.
- Broader report filters (date range, section, student, status).
- Additional quality and resilience hardening for edge cases.

### 3.3 Out of Scope
- Web/mobile versions.
- Multi-user concurrent roles and permissions.
- Billing/payments.
- Biometric attendance.

---

## 4. Functional Requirements

### 4.1 Attendance Core
- **FR-1.1:** System accepts RFID from USB HID input stream and parses card IDs.
- **FR-1.2:** Known cards mark student present for relevant active/today session(s).
- **FR-1.3:** Unknown cards trigger registration and immediate attendance flow.
- **FR-1.4:** Duplicate taps are handled safely with clear UI feedback.
- **FR-1.5:** Manual present/absent changes are supported and flagged by method.

### 4.2 Administration
- **FR-2.1:** PIN-protected admin panel allows secure configuration changes.
- **FR-2.2:** Student CRUD includes RFID reassignment and section assignment.
- **FR-2.3:** Section CRUD includes name/type/level/day/time.
- **FR-2.4:** Settings persist language, thresholds, credentials path, and section mode.
- **FR-2.5:** Backup/restore workflows are available from settings.

### 4.3 Data Exchange & Reporting
- **FR-3.1:** Legacy Google Sheets import supports preview and threshold filtering.
- **FR-3.2:** Attendance summary push to Google Sheets is supported.
- **FR-3.3:** Daily attendance report dialog is available.
- **FR-3.4:** CSV export fallback remains planned and not yet complete.

---

## 5. Non-Functional Requirements

### 5.1 Platform
- Windows 10/11 desktop only.
- Python 3.10+, CustomTkinter, sqlite3.

### 5.2 Performance
- RFID response under 500ms target.
- UI feedback appears near-instantly after scan.

### 5.3 Reliability
- SQLite with WAL mode.
- Local logging for startup, taps, errors, and operations.
- Backup strategy: manual + automatic periodic backups.

### 5.4 Security
- Admin access by PIN only.
- Stored PIN uses salted PBKDF2 hash.
- Credentials referenced by path; key file is not stored in DB.

### 5.5 Maintainability
- Strict MVC layering.
- Type hints expected for public functions.
- User-friendly dialogs instead of raw tracebacks.

---

## 6. Success Metrics

- Attendance operation time per student reduced to seconds.
- Stable multi-hour class-day runtime without crashes.
- Accurate session, student, and attendance persistence in SQLite.
- Smooth admin operations for import, backup, and settings.

---

## 7. Roadmap Snapshot

### Phase A (Complete)
Core attendance, registration, session handling, manual overrides, CRUD, admin panel, localization, backup/restore.

### Phase B (Complete)
Legacy import flow, inactive-student handling, settings expansion, reporting baseline (daily report), Google summary push.

### Phase C (Next)
Report filtering + CSV export fallback + final polish/hardening.

---

## 8. Risks & Mitigation

- **RFID format variability:** keep parser/validation configurable and testable.
- **Operator mistakes during class:** preserve fast manual override and clear feedback states.
- **Data integrity issues:** enforce transaction-safe writes and backups.
- **Google API instability:** keep local-first model and fallback export path.

---

## 9. References

- `specs/CURRENT_STATE.md`
- `specs/CHANGELOG.md`
- `specs/agents.md`
- `specs/plan.md`

# Product Requirements Document (PRD)

**Project Name:** RFID Dance Class Attendance System  
**Version:** 1.1  
**Status:** Draft  
**Date:** 2026-02-20  
**Author:** Orkun Arslanturk  
**Last Updated:** 2026-02-20

---

## 1. Overview

### 1.1 Purpose
Build a desktop application that automates attendance tracking for a dance studio using RFID card scanning. The system replaces manual paper-based or verbal roll-call processes with a fast, tap-to-attend workflow — reducing administrative overhead to near-zero and providing accurate, exportable attendance records.

### 1.2 Problem Statement
Dance studio administrators currently spend approximately 10–15 minutes per class manually tracking attendance across ~5 sections and ~200 students. This manual process leads to:
- **Data entry errors** — misspelled names, missed entries, duplicate records.
- **Lost records** — paper sheets get misplaced; no centralized history.
- **No real-time visibility** — absence patterns go unnoticed until it's too late.
- **Reporting burden** — compiling weekly/monthly reports takes 2+ hours of manual work.

With ~5 sections running multiple classes per week, this amounts to **5+ hours/week** of wasted administrative time and unreliable data.

### 1.3 Goals
- **Goal 1:** Reduce per-class attendance logging time from 10–15 minutes to under 10 seconds (RFID tap).
- **Goal 2:** Achieve 100% accurate attendance records with zero manual data entry errors.
- **Goal 3:** Enable one-click export of attendance data to Google Sheets, eliminating 2+ hours/week of manual reporting.

### 1.4 Vision
A simple, reliable, single-screen desktop kiosk application that any dance studio staff member can operate — tap a card, see instant feedback, and never worry about attendance paperwork again. The system should be extendable to support growing sections and student counts without re-architecture.

---

## 2. User Personas

### Persona 1: Elif, the Studio Administrator
- **Role/Title:** Dance Studio Administrator / Owner
- **Background:** Manages day-to-day operations of a dance studio with ~200 students across 5 sections. Non-technical but comfortable using basic desktop applications. Has been tracking attendance on paper and Excel spreadsheets.
- **Goals:**
  - Log attendance quickly before/during class without disrupting the session.
  - View and export attendance reports for parents, instructors, or management.
  - Register new students instantly when they first arrive with an RFID card.
  - Get alerts when a student accumulates excessive absences.
- **Pain Points:**
  - Wastes 5+ hours/week on manual attendance tracking and report compilation.
  - Frequently encounters errors in paper-based records.
  - Cannot easily identify students with chronic absence patterns.
  - No centralized, searchable history of attendance data.
- **Technical Proficiency:** Beginner — comfortable with desktop apps, Google Sheets, and USB devices.
- **Key Behaviors:** Prefers single-screen workflows with large, clear buttons. Avoids complex configuration menus. Wants Turkish UI with English fallback.

### Persona 2: Ahmet, the IT-Savvy Assistant
- **Role/Title:** Part-time Technical Assistant
- **Background:** Helps set up hardware (RFID reader, computer) and troubleshoots technical issues. Comfortable with Python and basic database operations.
- **Goals:**
  - Set up and configure the system (RFID reader, database, Google Sheets API).
  - Import/export student lists and attendance data.
  - Manage sections, schedules, and system settings via an admin panel.
- **Pain Points:**
  - Needs the system to "just work" after initial setup — minimal ongoing maintenance.
  - Wants clear error messages when things go wrong (reader disconnected, duplicate card, etc.).
- **Technical Proficiency:** Intermediate — can run Python scripts, manage config files, and interact with APIs.
- **Key Behaviors:** Uses the admin panel for bulk operations. Prefers English UI. Exports data periodically for backup.

---

## 3. Use Cases

### Use Case 1: Record Attendance via RFID Tap (Known Student)
- **Actor:** Elif (Administrator)
- **Preconditions:** The application is running, an active class session is selected, and the USB HID RFID reader is connected.
- **Main Flow:**
  1. Student taps their RFID card on the reader.
  2. The reader sends the card ID to the application (keyboard emulation).
  3. The system looks up the card ID in the SQLite database.
  4. The student's name appear on screen with a "Welcome" message.
  5. Attendance record is saved with timestamp, student ID, section, and class date.
- **Alternative Flows:**
  - **Duplicate tap:** If the student already has attendance for this session, the system shows "Already marked present" and optionally allows toggling to "Absent."
  - **Reader disconnected:** The system shows an error banner "RFID reader not detected" and allows manual name entry as fallback.
- **Postconditions:** Attendance record is stored in SQLite. The attendance list on screen updates in real-time.

### Use Case 2: Register New Student via RFID Tap (Unknown Card)
- **Actor:** Elif (Administrator)
- **Preconditions:** The application is running and a card is tapped that does not exist in the database.
- **Main Flow:**
  1. Student taps their RFID card on the reader.
  2. The system detects the card ID is not registered.
  3. A registration dialog appears prompting for: **First Name**, **Last Name**.
  4. Elif enters the student's name and surname and clicks "Register."
  5. The system saves the new student record linked to this RFID card ID.
  6. Attendance is automatically marked for the current session.
- **Alternative Flows:**
  - **Cancelled registration:** If Elif cancels the dialog, no record is created and the card tap is ignored.
  - **Section assignment:** After registration, a prompt asks which section(s) to assign the student to.
- **Postconditions:** New student record exists in the database with the RFID card ID. Student is assigned to at least one section. Attendance is recorded for the current session.

### Use Case 3: Export Attendance to Google Sheets
- **Actor:** Elif or Ahmet
- **Preconditions:** Google Sheets API credentials are configured. Attendance data exists in the database.
- **Main Flow:**
  1. User navigates to the "Reports" or "Export" section of the admin panel.
  2. User selects date range, section(s), and export format.
  3. User clicks "Export to Google Sheets."
  4. The system authenticates with Google Sheets API and pushes the data.
  5. A success message appears with a link to the Google Sheet.
- **Alternative Flows:**
  - **API credentials missing:** System prompts user to configure Google credentials in settings.
  - **Network error:** System saves the export locally as CSV and notifies user to retry.
- **Postconditions:** Attendance data is available in the configured Google Sheet. Local data remains unchanged.

### Use Case 4: Import Student List from Google Sheets
- **Actor:** Ahmet (Technical Assistant)
- **Preconditions:** A Google Sheet with student data (Name, Surname, Section) exists. API credentials are configured.
- **Main Flow:**
  1. User navigates to "Import" in the admin panel.
  2. User provides the Google Sheet URL or selects from configured sheets.
  3. System reads student data and shows a preview with validation results.
  4. User confirms the import.
  5. System creates new student records (without RFID card IDs — cards will be assigned on first tap).
- **Alternative Flows:**
  - **Duplicate students detected:** System highlights duplicates and asks user to skip, overwrite, or merge.
- **Postconditions:** Student records are created/updated in the database. Students without RFID cards will be auto-registered on first card tap.

### Use Case 5: View Absence Alerts
- **Actor:** Elif (Administrator)
- **Preconditions:** Attendance history exists. Absence threshold is configured in settings.
- **Main Flow:**
  1. User opens the dashboard or attendance view.
  2. The system highlights students who have exceeded the configured absence threshold (e.g., 3+ absences in the current month).
  3. User clicks on a student name to see detailed attendance history.
- **Postconditions:** Administrator is aware of students with excessive absences and can take action.

### Use Case 6: Start a Class Session
- **Actor:** Elif (Administrator)
- **Preconditions:** At least one section exists in the database.
- **Main Flow:**
  1. Admin selects a section from the section dropdown/list on the main screen.
  2. Admin clicks the "Start Session" button.
  3. The system creates a session record for today's date and the selected section.
  4. The attendance screen activates: the student list for that section is loaded, all students default to "Absent", and the RFID input field gains focus.
  5. The system is now ready to accept RFID card taps.
- **Alternative Flows:**
  - **Session already exists:** If a session for this section and today's date already exists, the system asks whether to resume the existing session or start a new one.
- **Postconditions:** An active session is running. RFID taps are processed against this session. All enrolled students are shown as "Absent" until they tap in.

### Use Case 7: Manual Attendance Change (Forgotten Card)
- **Actor:** Elif (Administrator)
- **Preconditions:** A session is active. The student is enrolled in the system but forgot their RFID card.
- **Main Flow:**
  1. Admin opens the student list for the current session.
  2. Admin finds the student by name (search or scroll).
  3. Admin clicks the student's attendance status toggle (Absent → Present or Present → Absent).
  4. The system updates the attendance record with a "manual" flag indicating it was not an RFID tap.
- **Alternative Flows:**
  - **Student not enrolled:** Admin can search all students and add them to the session manually.
- **Postconditions:** Student's attendance status is updated. The record is flagged as a manual override for audit purposes.

### Use Case 8: Reassign RFID Card to a Different Student
- **Actor:** Elif or Ahmet
- **Preconditions:** The student exists in the database. A new RFID card is available.
- **Main Flow:**
  1. Admin navigates to the student management screen.
  2. Admin selects the student whose RFID card needs to be changed.
  3. Admin clicks "Change RFID Card" button.
  4. A prompt appears: "Tap the new RFID card on the reader."
  5. Admin taps the new card. The system captures the card ID.
  6. The system validates the new card ID is not already assigned to another student.
  7. The old card ID is unlinked and the new card ID is saved to the student's record.
- **Alternative Flows:**
  - **Card already assigned:** System shows an error: "This card is already assigned to [Student Name]. Unassign it first."
  - **Manual entry:** Admin can also type the RFID number manually instead of tapping.
- **Postconditions:** Student's RFID card ID is updated. The old card ID is no longer linked to any student.

### Use Case 9: Import Legacy Data from Google Sheets
- **Actor:** Ahmet (Technical Assistant)
- **Preconditions:** An existing Google Sheet with the legacy format exists (columns: `name`, `rfid`, `D_YYYY_MM_DD`, ...). API credentials are configured.
- **Main Flow:**
  1. Admin navigates to "Import" in the admin panel and selects "Import Legacy Database."
  2. Admin provides the Google Sheet URL or ID.
  3. The system reads the sheet and displays a preview: total students found, students with RFID, students without RFID, and total attendance sessions.
  4. Admin sets a **minimum attendance threshold** (e.g., "only import students who attended at least 3 sessions").
  5. The system filters: students below the threshold AND without an RFID number are excluded (can be deleted/ignored).
  6. Admin confirms the import.
  7. The system creates student records (name + RFID) and optionally assigns them to the selected section.
- **Alternative Flows:**
  - **Duplicate students detected:** System highlights matches by name or RFID and asks to skip, overwrite, or merge.
  - **No RFID assigned:** Students without RFID are imported but flagged as "pending card assignment" — their card will be linked on first tap.
- **Postconditions:** Student records are created in SQLite from the legacy Google Sheet. Students below the attendance threshold without RFID are excluded. Section assignment is applied.

### Use Case 10: Post-Lesson Absent Summary
- **Actor:** Elif (Administrator)
- **Preconditions:** A session is active and the class has ended.
- **Main Flow:**
  1. During the session, the attendance screen shows a **live list** of students who haven't tapped in yet (marked red/absent) alongside those who have (marked green/present).
  2. When the admin clicks "End Session," a summary popup appears showing:
     - Total students enrolled in the section.
     - Number present and number absent.
     - A list of absent student names.
  3. Admin can review the absent list and optionally mark any student as "Present" (manual override) before finalizing.
  4. Admin clicks "Confirm & Close" to finalize the session.
- **Postconditions:** Session is closed. Attendance records are finalized. Absent students are recorded.

---

## 4. Functional Requirements

### Musts: Core Attendance
- **FR-1.1:** System must accept RFID card input from a USB HID reader (keyboard emulation mode) and capture the full card ID string.
- **FR-1.2:** When a known card is tapped, system must log an attendance record with: student ID, section ID, class date, timestamp, and status (Present).
- **FR-1.3:** When an unknown card is tapped, system must display a registration form capturing first name and last name, and link the new student to the card ID.
- **FR-1.4:** System must store all data in a local SQLite database.
- **FR-1.5:** System must allow creating, editing, and deleting **sections** with attributes: name, type (e.g., Technique, Normal), level (e.g., Beginner, Intermediate, Advanced), and schedule (day/time).
- **FR-1.6:** System must allow creating, editing, and deleting **student records** with attributes: first name, last name, RFID card ID, assigned section(s).
- **FR-1.7:** System must support assigning a student to one or more sections.
- **FR-1.8:** System must provide a main attendance screen showing: current section, list of students with attendance status, and a real-time RFID input field.
- **FR-1.9:** System must allow toggling a student's attendance status (Present ↔ Absent) manually via the UI as a fallback for students who forgot their RFID card. Manual overrides must be flagged in the database.
- **FR-1.10:** System must provide a "Start Session" button that requires selecting a section, then creates a session for today's date, loads the section's enrolled students (all defaulting to Absent), and activates the RFID input listener.
- **FR-1.11:** System must provide an "End Session" button that displays a post-lesson summary popup showing: total enrolled, total present, total absent, and a named list of absent students. Admin can make last-minute manual attendance changes before finalizing.
- **FR-1.12:** System must allow re-assigning an RFID card number to a student — either by tapping a new card or by manually typing the RFID number. The old card ID is unlinked upon reassignment.
- **FR-1.13:** System must change the main attendance screen background color based on RFID scan result: **Green** = known student marked present, **Red** = unknown card (triggers registration), **Yellow** = student already marked present (duplicate tap). Color flash should persist for 2–3 seconds before reverting.
- **FR-1.14:** System must display a real-time absent list during an active session — students who have not tapped in are shown with "Absent" status and visually distinguished (e.g., red text or background).
- **FR-1.15:** The student database view must support sorting by RFID card number, student name, and section. Students must be searchable by name or RFID number for quick lookup.

### Shoulds: Reporting & Export
- **FR-2.1:** System should generate attendance reports filterable by: section, date range, student, and attendance status.
- **FR-2.2:** System should support manual export of attendance data to Google Sheets via Google Sheets API.
- **FR-2.3:** System should support optional import of student data from Google Sheets.
- **FR-2.4:** System should display absence alerts for students exceeding a configurable absence threshold.
- **FR-2.5:** System should show attendance summary statistics: total present, total absent, attendance percentage per section and per student.
- **FR-2.6:** System should allow exporting reports as CSV as a fallback when Google Sheets is unavailable.
- **FR-2.7:** System should support importing legacy data from the existing Google Sheet format (columns: `name`, `rfid`, `D_YYYY_MM_DD`...). During import, admin sets a minimum total attendance threshold — students below the threshold who have no RFID assigned are excluded from import.
- **FR-2.8:** During legacy import, the system should show a preview (total students, with/without RFID, attendance counts) and allow the admin to confirm before committing.

### Coulds: Enhanced Experience
- **FR-3.1:** System could support switching the UI language between Turkish and English.
- **FR-3.2:** System could provide audio feedback (e.g., beep sound) in addition to the color-coded visual feedback on card tap.
- **FR-3.3:** System could display a daily/weekly attendance calendar view.
- **FR-3.4:** System could support dark mode / light mode theming.

---

## 5. Non-Functional Requirements

### 5.1 Performance
- **Response Time:** Attendance must be logged within < 500ms of RFID card tap. UI feedback (student name display) must appear within < 300ms.
- **Throughput:** System must handle rapid sequential scans (2+ students tapping within 1 second) without losing any reads.
- **Scalability:** Database schema must support 1,000+ students and 50+ sections without performance degradation. Queries on attendance records must return within < 1 second for up to 100,000 records.

### 5.2 Security
- **Authentication:** Admin panel access should be protected by a local password/PIN.
- **Authorization:** Single-role system (administrator). No multi-user access control needed for MVP.
- **Data Encryption:** Google Sheets API credentials must be stored securely (not in plain text config files). SQLite database should be stored in a protected directory.
- **Compliance:** No specific regulatory compliance required. Student data (name + RFID ID) is minimal PII.

### 5.3 Reliability
- **Uptime:** Application must run stably for 8+ hours continuously without crashes or memory leaks.
- **Backup & Recovery:** SQLite database file must be easily copyable for manual backups. System should support a "Backup Database" button in the admin panel.
- **Error Handling:** All errors (reader disconnected, database write failure, Google API error) must show user-friendly error messages in a dialog — never raw stack traces.

### 5.4 Usability
- **Accessibility:** Large fonts and high-contrast colors for readability at a distance (kiosk-style usage). Minimum touch target / button size of 44x44 pixels.
- **User Interface:** Built with CustomTkinter for a modern look. Single-window design with tab/panel navigation. The application launches directly in full-screen mode and automatically forces window focus (brought to the front) upon startup.
- **Learning Curve:** A new user should be able to mark attendance (tap cards) within 1 minute of seeing the app. Admin features should be learnable within 15 minutes.

### 5.5 Maintainability
- **Code Quality:** Python 3.10+ with type hints. Modular architecture separating UI, business logic, and data access layers.
- **Logging & Monitoring:** Application should log events (startup, card taps, errors, exports) to a local log file with timestamps.
- **Technology Stack:** Python 3.10+, CustomTkinter, SQLite3, Google Sheets API (gspread or google-api-python-client).

---

## 6. User Stories

### Story 1
**As a** studio administrator, **I want** to tap a student's RFID card and have their attendance automatically recorded, **so that** I don't waste class time doing manual roll calls.

Acceptance Criteria:
- [ ] Tapping a registered card logs attendance within 500ms
- [ ] Student's name appears on screen confirming the record
- [ ] Duplicate taps within the same session show "Already marked" message

### Story 2
**As a** studio administrator, **I want** unknown RFID cards to trigger a registration prompt, **so that** new students can be enrolled instantly without a separate workflow.

Acceptance Criteria:
- [ ] Unknown card tap opens a name/surname input dialog
- [ ] After entering details, the student is created and linked to the card
- [ ] Attendance for the current session is automatically recorded

### Story 3
**As a** studio administrator, **I want** to create and manage dance class sections with type, level, and schedule, **so that** I can organize students and track attendance per section.

Acceptance Criteria:
- [ ] Can create sections with name, type, level, and day/time
- [ ] Can edit and delete existing sections
- [ ] Students can be assigned to one or more sections

### Story 4
**As a** studio administrator, **I want** to export attendance records to Google Sheets, **so that** I can share reports with instructors and parents without manual data entry.

Acceptance Criteria:
- [ ] "Export to Google Sheets" button is accessible from the reports panel
- [ ] User can select date range and section(s) before exporting
- [ ] Success/failure feedback is shown after the export attempt
- [ ] CSV fallback export works when Google API is unavailable

### Story 5
**As a** studio administrator, **I want** to see absence alerts for students with excessive absences, **so that** I can follow up before students drop out.

Acceptance Criteria:
- [ ] Configurable absence threshold (default: 3 per month)
- [ ] Students exceeding threshold are visually highlighted in the attendance view
- [ ] Clicking a highlighted student shows their detailed attendance history

### Story 6
**As a** studio administrator, **I want** to switch the application language between Turkish and English, **so that** I and my colleagues can use the app in our preferred language.

Acceptance Criteria:
- [ ] Language switcher available in settings
- [ ] All UI labels, buttons, and messages update on language change
- [ ] Selected language persists between sessions

### Story 7
**As a** studio administrator, **I want** to start a class session by selecting a section and clicking "Start Session", **so that** the system is prepared to record attendance for today's class.

Acceptance Criteria:
- [ ] Section dropdown lists all created sections
- [ ] Clicking "Start Session" creates a session for today's date
- [ ] All enrolled students appear in the list as "Absent" until they tap in
- [ ] RFID input is active and focused after session starts

### Story 8
**As a** studio administrator, **I want** to manually mark a student present or absent, **so that** students who forgot their RFID card are not penalized.

Acceptance Criteria:
- [ ] Can search/scroll to find the student by name
- [ ] One-click toggle between Present and Absent
- [ ] Manual changes are flagged as "manual" in the database

### Story 9
**As a** studio administrator, **I want** to change the RFID card assigned to a student, **so that** lost or broken cards can be replaced without creating a new student record.

Acceptance Criteria:
- [ ] "Change RFID" button available on the student detail/edit screen
- [ ] Admin can tap a new card or type the RFID number manually
- [ ] System rejects RFID numbers already assigned to another student
- [ ] Old card ID is unlinked immediately

### Story 10
**As a** studio administrator, **I want** the screen to flash green, red, or yellow based on the RFID scan result, **so that** I can see the outcome from a distance without reading text.

Acceptance Criteria:
- [ ] Green flash = known student marked present
- [ ] Red flash = unknown card (registration triggered)
- [ ] Yellow flash = duplicate tap (already present)
- [ ] Color persists for 2–3 seconds then reverts

### Story 11
**As a** studio administrator, **I want** to see a summary of absent students after ending a session, **so that** I know exactly who missed the class.

Acceptance Criteria:
- [ ] "End Session" button shows a popup with present/absent counts and absent student names
- [ ] Admin can make last-minute manual changes in the popup
- [ ] "Confirm & Close" finalizes the session

### Story 12
**As a** technical assistant, **I want** to import students from the existing Google Sheet format (name, rfid, date columns), **so that** the legacy database is migrated without re-entering data.

Acceptance Criteria:
- [ ] Supports the legacy format with `name`, `rfid`, and `D_YYYY_MM_DD` columns
- [ ] Admin sets a minimum attendance threshold to filter inactive students
- [ ] Students below threshold with no RFID are excluded
- [ ] Preview is shown before committing the import

### Story 13
**As a** studio administrator, **I want** to sort and search the student database by RFID number or name, **so that** I can quickly find any student's record.

Acceptance Criteria:
- [ ] Student list supports sorting by RFID number, name, and section
- [ ] Search box filters students in real-time as admin types
- [ ] RFID column is visible and sortable in the student management view

---

## 7. Success Metrics

### Key Performance Indicators (KPIs)
- **Metric 1:** Attendance Logging Speed — Average time from card tap to recorded attendance < 500ms (measured from first use)
- **Metric 2:** Data Accuracy — 0 manual data entry errors in attendance records over a 1-month trial period
- **Metric 3:** Admin Time Saved — Reduce weekly attendance administration time from 5+ hours to < 30 minutes
- **Metric 4:** System Reliability — Application runs 8+ hours continuously with 0 crashes during a 2-week pilot

### Success Criteria
- [ ] *To be specified by stakeholder*

---

## 8. Scope

### 8.1 In Scope
- RFID card tap-based attendance recording via USB HID reader
- Auto-registration of new students on first card tap
- **Start Session / End Session workflow** with section selection and post-lesson absent summary
- **Manual attendance override** for students who forgot their RFID card (flagged as manual)
- **RFID card reassignment** — change a student's card by tapping a new card or entering the number manually
- **Color-coded screen feedback** — Green (present), Red (unknown card), Yellow (duplicate tap)
- **Real-time absent list** during active sessions showing who hasn't tapped in
- Section management (create, edit, delete with type/level/schedule)
- Student management (CRUD, multi-section assignment, **sortable/searchable by RFID number and name**)
- Attendance reports with filtering by section, date range, and student
- Manual export to Google Sheets and CSV
- **Legacy Google Sheets import** — supports existing format (`name`, `rfid`, `D_YYYY_MM_DD` columns) with configurable minimum attendance threshold to exclude inactive students without RFID
- Optional import of student data from Google Sheets
- Absence alert highlighting based on configurable threshold
- Turkish/English bilingual UI
- Local SQLite database storage
- Admin panel with password/PIN protection

### 8.2 Out of Scope
- **Cloud/web-based deployment** — This is a local desktop application only. Web version is a future consideration.
- **Multi-user concurrent access** — Single operator per installation. Network-shared access is not supported.
- **Payment/billing integration** — No tuition tracking, invoicing, or payment processing.
- **Biometric or facial recognition** — Only RFID card-based identification is supported.
- **Mobile application** — No iOS/Android companion app in this version.

### 8.3 Phases
**Phase 1 (MVP — 2 Days):**
- Start Session / End Session workflow with section selection
- RFID tap-in attendance with auto-registration
- Color-coded screen feedback (Green/Red/Yellow)
- Manual attendance toggle for forgotten cards
- RFID card reassignment to students
- Real-time absent list during session
- Post-lesson absent summary popup on session end
- Section and student management (CRUD, sortable by RFID/name)
- Legacy Google Sheets database import with attendance threshold filter
- SQLite database storage
- Google Sheets export (manual)
- Admin panel with PIN protection

**Phase 2 (Post-MVP — 1–2 weeks):**
- Attendance reports with filtering and statistics
- Absence alerts
- Turkish/English language switching
- CSV export fallback
- Audio feedback on card tap

---

## 9. Technical Constraints & Architecture

### 9.1 Technical Constraints
- **Platform:** Windows desktop only (must run on Windows 10/11).
- **RFID Reader:** USB HID keyboard-emulation readers only. The reader sends the card ID as keystrokes followed by Enter. No driver installation required.
- **Offline-first:** System must function fully without internet. Google Sheets features require internet only during export/import operations.
- **Single-instance:** Only one instance of the application should run at a time per machine.

### 9.2 Architecture Considerations
- **Pattern:** Model-View-Controller (MVC) or similar layered architecture.
  - **Model layer:** SQLite database access via Python `sqlite3` module. Data models for Student, Section, Session, Attendance, Settings.
    - **Session model:** Tracks active/closed sessions with fields: session ID, section ID, date, start time, end time, status (active/closed).
    - **Attendance model:** Links session ID + student ID with status (Present/Absent), method (RFID/Manual), and timestamp.
  - **View layer:** CustomTkinter UI with tab-based navigation (Attendance, Students, Sections, Reports, Settings).
  - **Controller layer:** Business logic for attendance processing, card registration, report generation, and Google Sheets sync.
- **RFID Input Handling:** A hidden/focused text entry widget captures keyboard input from the USB HID reader. On Enter key event, the captured string is processed as a card ID.
- **Database:** Single SQLite file (e.g., `attendance.db`) in the application directory.

### 9.3 Technology Stack
- **Language:** Python 3.10+
- **GUI Framework:** CustomTkinter (modern-looking tkinter wrapper)
- **Database:** SQLite3 (built-in Python module)
- **Google Integration:** `gspread` + `oauth2client` or `google-auth` for Google Sheets API
- **Packaging:** PyInstaller or cx_Freeze for creating a standalone `.exe` (future)
- **Infrastructure:** Runs locally on a single Windows PC. No server infrastructure required.

---

## 10. Dependencies

### 10.1 Internal Dependencies
- RFID card set — physical cards must be procured for students.
- A dedicated Windows PC or laptop at the studio for running the application.
- USB port availability for the RFID reader.

### 10.2 External Dependencies
- **Google Sheets API** — Requires a Google Cloud project with Sheets API enabled and a service account JSON key file.
- **CustomTkinter** — Open-source Python package (`pip install customtkinter`).
- **gspread** — Open-source Python package for Google Sheets interaction (`pip install gspread`).
- **USB HID RFID Reader** — Off-the-shelf hardware (e.g., 125kHz or 13.56MHz USB reader).

### 10.3 Assumptions
- The RFID reader outputs a consistent-length numeric or alphanumeric card ID string followed by a newline/Enter character.
- Each physical RFID card has a unique, factory-assigned ID that does not change.
- The studio has a stable internet connection when Google Sheets export/import is needed (not required for core attendance).
- A single admin operator is sufficient for managing the system.

---

## 11. Risks & Mitigation

### Risk 1: USB HID Reader Compatibility Issues
- **Severity:** High
- **Probability:** Low
- **Description:** Different USB HID RFID reader models may output card IDs in varying formats (length, encoding, prefix/suffix characters). This could cause the app to fail to recognize card taps.
- **Mitigation Strategy:** Implement a configurable card ID parser with a "Test Reader" setup wizard that detects the reader's output format. Support trimming prefix/suffix characters via settings.

### Risk 2: Rapid Sequential Scans Lost
- **Severity:** Medium
- **Probability:** Medium
- **Description:** If two students tap their cards in quick succession (< 500ms apart), the keyboard buffer may merge inputs, resulting in a corrupted card ID.
- **Mitigation Strategy:** Use a delimiter-based parser (Enter key as separator). Implement a debounce timer and input validation (expected card ID length/format). Reject malformed IDs with an error beep.

### Risk 3: SQLite Database Corruption
- **Severity:** High
- **Probability:** Low
- **Description:** Power loss or unexpected application termination during a database write could corrupt the SQLite file.
- **Mitigation Strategy:** Enable SQLite WAL (Write-Ahead Logging) mode. Implement periodic automatic backups (every 30 minutes or configurable). Provide a "Backup Now" button in the admin panel.

### Risk 4: Google Sheets API Authentication Failure
- **Severity:** Low
- **Probability:** Medium
- **Description:** Service account credentials may expire, be revoked, or become misconfigured, blocking export/import functionality.
- **Mitigation Strategy:** Provide clear error messages with setup instructions. Always offer CSV export as a fallback. Validate credentials on app startup with a non-blocking warning.

### Risk 5: Aggressive MVP Timeline (2 Days)
- **Severity:** High
- **Probability:** High
- **Description:** Building a full-featured attendance system in 2 days risks incomplete features, untested edge cases, and poor code quality.
- **Mitigation Strategy:** Strictly prioritize Phase 1 (MVP) features only. Defer Google Sheets, i18n, reports, and absence alerts to Phase 2. Focus Day 1 on core architecture + RFID attendance. Focus Day 2 on student/section management + admin panel.



## 12. Resources & Team

### 12.1 Team Structure
- **Developer / Product Owner:** Arslan — sole developer handling design, development, testing, and deployment.

### 12.2 Required Resources
- **Hardware:** 1x USB HID RFID Reader (125kHz or 13.56MHz), 1x Windows PC/Laptop, RFID cards for students.
- **Software:** Python 3.10+, CustomTkinter, SQLite3, gspread (Phase 2), PyInstaller (packaging, future).
- **Accounts:** Google Cloud project with Sheets API enabled (Phase 2).

---

## 13. Marketing & Go-to-Market

### 13.1 Target Market
Single dance studio with ~200 students across ~5 sections. Internal tool — not a commercial product at this stage.

### 13.2 Competitive Advantage
- **Zero cost** — built with free, open-source tools.
- **Instant setup** — plug in a USB reader and run the app.
- **No internet required** — fully offline-capable for core attendance.
- **Auto-registration** — no pre-enrollment needed; students register on first card tap.

### 13.3 Launch Strategy
- Deploy directly to the studio's attendance PC.
- Train Elif (administrator) in a 15-minute walkthrough session.
- Run a 1-week pilot alongside the existing manual process to validate accuracy.

---

## 14. Appendices & References

### 14.1 Glossary
- **RFID:** Radio-Frequency Identification — technology using electromagnetic fields to identify tags/cards.
- **USB HID:** USB Human Interface Device — a protocol that allows RFID readers to emulate a keyboard, sending card IDs as keystrokes.
- **Section:** A dance class group defined by name, type (Technique/Normal), level, and schedule.
- **Card ID:** The unique alphanumeric identifier transmitted by an RFID card when scanned.
- **CustomTkinter:** A modern Python UI library built on top of tkinter with themed widgets.
- **SQLite:** A lightweight, file-based relational database engine built into Python.
- **WAL:** Write-Ahead Logging — an SQLite journaling mode that improves reliability and concurrent read performance.
- **MoSCoW:** A prioritization framework — Must have, Should have, Could have, Won't have.

### 15.2 Supporting Documents
- PRD Template: `specs/templates/prd-template.md`
- Epic Template: `specs/templates/epic-template.md`
- Story Template: `specs/templates/story-template.md`

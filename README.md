# RFID Attendance System

> A full-screen Windows kiosk application for tracking student attendance in a dance studio using RFID card readers. Built with Python, CustomTkinter, and SQLite3.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)](https://www.python.org/)
[![Platform: Windows](https://img.shields.io/badge/Platform-Windows-blue?logo=windows)](https://github.com/Adrimars/Attendance_System/releases)

---

## Table of Contents

- [Features](#features)
- [Screenshots](#screenshots)
- [Requirements](#requirements)
- [Developer Setup](#developer-setup)
- [Running the App](#running-the-app)
- [Building the Executable](#building-the-executable)
- [For End-Users (Download & Run .exe)](#for-end-users-download--run-exe)
- [Project Structure](#project-structure)
- [Configuration & Secrets](#configuration--secrets)
- [Contributing](#contributing)
- [License](#license)

---

## Features

- **Passive RFID listening** ΓÇö always-focused entry widget captures card taps instantly
- **Auto-session creation** ΓÇö daily attendance sessions are created per section automatically
- **Multi-section enrollment** ΓÇö one tap marks a student present in all their sections scheduled for that weekday
- **Unknown card registration** ΓÇö a registration dialog opens on first tap; student is enrolled and immediately marked present
- **Admin panel** (Ctrl+P, PIN-protected) with three tabs:
  - **Sections** ΓÇö add/edit/delete class sections with day and time
  - **Students** ΓÇö search, sort, view attendance history, edit details, and reassign RFID cards
  - **Settings** ΓÇö change PIN, language, attendance threshold, Google Sheets credentials, backup, and Google Sheets import
- **Google Sheets integration** ΓÇö export attendance summaries and import student rosters from a live spreadsheet
- **Auto-backup** ΓÇö database is backed up every 4 hours automatically
- **Localization support** ΓÇö language is configurable via the settings panel

---

## Requirements

- Windows 10 or 11 (64-bit)
- Python **3.10+**
- An RFID USB card reader (keyboard-emulation / HID mode)

---

## Developer Setup

### 1. Clone the repository

```bash
git clone https://github.com/Adrimars/Attendance_System.git
cd Attendance_System
```

### 2. Create and activate a virtual environment

```bash
python -m venv .venv
.venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Google Sheets credentials (optional)

If you want Google Sheets export/import functionality:

1. Create a **Google Cloud project** and enable the **Google Sheets API** and **Google Drive API**.
2. Create a **Service Account**, download the JSON key file.
3. **Do not commit this file** ΓÇö it is already excluded by `.gitignore`.
4. In the app's Settings tab, browse to your credentials `.json` file.

---

## Running the App

From the project root:

```bash
python src/main.py
```

- The app launches full-screen.
- Press **Ctrl+P** to open the admin panel (default PIN: `1234` on first run ΓÇö change it immediately in Settings).

---

## Building the Executable

A pre-configured `attendance.spec` is included. Run from the project root with the virtual environment active:

```bash
pyinstaller attendance.spec
```

Output: `dist\AttendanceSystem\AttendanceSystem.exe`

### Alternative ΓÇö one-file build (slower startup, no external files)

```bash
pyinstaller --onefile --noconsole --name AttendanceSystem src/main.py
```

> **Note:** The `build/` and `dist/` folders are git-ignored. The executable is distributed separately via [Attendance_System_App](https://github.com/Adrimars/Attendance_System_App).

---

## For End-Users (Download & Run .exe)

> You do **not** need Python installed.

1. Go to the **[Attendance_System_App](https://github.com/Adrimars/Attendance_System_App)** repository.
2. Download the latest `AttendanceSystem.exe` from the releases or the `app/` folder.
3. Double-click `AttendanceSystem.exe` ΓÇö no installation required.
4. On first launch, open the Settings panel (Ctrl+P ΓåÆ enter PIN `1234`) and configure your preferences.

---

## Project Structure

```
Attendance_System/
Γö£ΓöÇΓöÇ src/
Γöé   Γö£ΓöÇΓöÇ main.py                    # Entry point
Γöé   Γö£ΓöÇΓöÇ controllers/               # Business logic layer
Γöé   Γöé   Γö£ΓöÇΓöÇ attendance_controller.py
Γöé   Γöé   Γö£ΓöÇΓöÇ import_controller.py
Γöé   Γöé   Γö£ΓöÇΓöÇ section_controller.py
Γöé   Γöé   Γö£ΓöÇΓöÇ session_controller.py
Γöé   Γöé   ΓööΓöÇΓöÇ student_controller.py
Γöé   Γö£ΓöÇΓöÇ models/                    # Database access layer (SQLite3)
Γöé   Γöé   Γö£ΓöÇΓöÇ database.py
Γöé   Γöé   Γö£ΓöÇΓöÇ attendance_model.py
Γöé   Γöé   Γö£ΓöÇΓöÇ section_model.py
Γöé   Γöé   Γö£ΓöÇΓöÇ session_model.py
Γöé   Γöé   Γö£ΓöÇΓöÇ settings_model.py
Γöé   Γöé   ΓööΓöÇΓöÇ student_model.py
Γöé   Γö£ΓöÇΓöÇ utils/                     # Shared utilities
Γöé   Γöé   Γö£ΓöÇΓöÇ backup.py
Γöé   Γöé   Γö£ΓöÇΓöÇ localization.py
Γöé   Γöé   Γö£ΓöÇΓöÇ logger.py
Γöé   Γöé   ΓööΓöÇΓöÇ pin_utils.py
Γöé   ΓööΓöÇΓöÇ views/                     # UI layer (CustomTkinter)
Γöé       Γö£ΓöÇΓöÇ app.py
Γöé       Γö£ΓöÇΓöÇ attendance_tab.py
Γöé       Γö£ΓöÇΓöÇ admin_panel.py
Γöé       Γö£ΓöÇΓöÇ sections_tab.py
Γöé       Γö£ΓöÇΓöÇ students_tab.py
Γöé       Γö£ΓöÇΓöÇ settings_tab.py
Γöé       Γö£ΓöÇΓöÇ components/
Γöé       ΓööΓöÇΓöÇ dialogs/
Γö£ΓöÇΓöÇ specs/                         # Project specification documents
Γö£ΓöÇΓöÇ attendance.spec                # PyInstaller build config
Γö£ΓöÇΓöÇ requirements.txt
Γö£ΓöÇΓöÇ LICENSE
ΓööΓöÇΓöÇ README.md
```

---

## Configuration & Secrets

| Setting | Storage | Committed to Git? |
|---|---|---|
| Admin PIN (hashed) | `attendance.db` (SQLite) | Γ¥î No ΓÇö DB is gitignored |
| Google Sheets URL | `attendance.db` (SQLite) | Γ¥î No ΓÇö DB is gitignored |
| Google credentials path | `attendance.db` (SQLite) | Γ¥î No ΓÇö DB is gitignored |
| Service account `.json` | User-selected local file | Γ¥î No ΓÇö pattern excluded in `.gitignore` |

**No secrets are ever stored in source code.** All sensitive settings are stored in the local SQLite database file (`attendance.db`) which is excluded from version control by `.gitignore`.

---

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature-name`
3. Commit your changes: `git commit -m "feat: add your feature"`
4. Push to the branch: `git push origin feature/your-feature-name`
5. Open a Pull Request

---

## License

This project is licensed under the [MIT License](LICENSE) ΓÇö ┬⌐ 2026 Adrimars.

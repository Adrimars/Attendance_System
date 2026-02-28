# RFID Attendance System

> Specifically created for IZTECH World Dance Society. A Windows desktop application for tracking student attendance in dance classes using USB HID RFID card readers. Built with Python, CustomTkinter, and SQLite3.

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

- **Passive RFID listening** — always-focused entry widget captures card taps instantly
- **Auto-session creation** — daily attendance sessions are created per section automatically
- **Multi-section enrollment** — one tap marks a student present in all their sections scheduled for that weekday
- **Unknown card registration** — a registration dialog opens on first tap; student is enrolled and immediately marked present
- **Zero-section handling** — known students with no sections get a section assignment dialog on tap
- **Inactive student tracking** — students exceeding consecutive absence threshold are auto-flagged with visual alerts
- **Admin panel** (Ctrl+P, PIN-protected) with three tabs:
  - **Sections** — add/edit/delete class sections with day and time
  - **Students** — search, sort, view attendance history, edit details, and reassign RFID cards
  - **Settings** — change PIN, language, attendance threshold, inactive threshold, section mode, Google Sheets credentials, backup/restore, import, summary push, and daily reports
- **Google Sheets integration** — import student rosters and push per-student attendance summaries
- **Auto-backup** — database is backed up every 4 hours automatically; manual backup and restore available
- **Localization support** — English and Turkish, switchable live from Settings
- **Daily attendance report** — per-section breakdown with summary statistics
- **Secure PIN** — PBKDF2-HMAC-SHA256 with salt; backward-compatible with legacy hashes
- **RFID simulation panel** — development tool for testing without hardware (marked #DELETABLE)

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
3. **Do not commit this file** — it is already excluded by `.gitignore`.
4. In the app's Settings tab, browse to your credentials `.json` file.

---

## Running the App

From the project root:

```bash
python src/main.py
```

- The app launches in a 1280×800 windowed mode (resizable, minimum 900×600).
- Press **Ctrl+P** to open the admin panel (default PIN: `1234` on first run — change it immediately in Settings).

---

## Building the Executable

A pre-configured `attendance.spec` is included. Run from the project root with the virtual environment active:

```bash
pyinstaller attendance.spec
```

Output: `dist\AttendanceSystem\AttendanceSystem.exe`

### Alternative — one-file build (slower startup, no external files)

```bash
pyinstaller --onefile --noconsole --name AttendanceSystem src/main.py
```

> **Note:** The `build/` and `dist/` folders are git-ignored. The executable is distributed separately via [Attendance_System_App](https://github.com/Adrimars/Attendance_System_App).

---

## For End-Users (Download & Run .exe)

> You do **not** need Python installed.

1. Go to the **[Attendance_System_App](https://github.com/Adrimars/Attendance_System_App)** repository.
2. Download the latest `AttendanceSystem.exe` from the releases or the `app/` folder.
3. Double-click `AttendanceSystem.exe` — no installation required.
4. On first launch, open the Settings panel (Ctrl+P → enter PIN `1234`) and configure your preferences.

---

## Project Structure

```
Attendance_System/
├── src/
│   ├── main.py                    # Entry point
│   ├── controllers/               # Business logic layer
│   │   ├── attendance_controller.py
│   │   ├── import_controller.py
│   │   ├── section_controller.py
│   │   ├── session_controller.py
│   │   └── student_controller.py
│   ├── models/                    # Database access layer (SQLite3)
│   │   ├── database.py
│   │   ├── attendance_model.py
│   │   ├── section_model.py
│   │   ├── session_model.py
│   │   ├── settings_model.py
│   │   └── student_model.py
│   ├── utils/                     # Shared utilities
│   │   ├── backup.py              # Auto-backup & restore
│   │   ├── localization.py        # English/Turkish i18n
│   │   ├── logger.py              # File logging
│   │   └── pin_utils.py           # PBKDF2 PIN hashing
│   └── views/                     # UI layer (CustomTkinter)
│       ├── app.py
│       ├── attendance_tab.py
│       ├── admin_panel.py
│       ├── sections_tab.py
│       ├── students_tab.py
│       ├── settings_tab.py
│       ├── components/
│       └── dialogs/
├── specs/                         # Project specification documents
├── attendance.spec                # PyInstaller build config
├── requirements.txt
├── requirements-dev.txt
├── LICENSE
└── README.md
```


## License

This project is licensed under the [MIT License](LICENSE) — © 2026 Adrimars.

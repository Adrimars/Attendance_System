# Push Prompt — Build & Release Workflow

Standard procedure for building and pushing a new release of the Attendance System.

---

## Pre-Push Checklist

- [ ] All code changes are tested and working
- [ ] No lint/compile errors in modified files
- [ ] Application launches and runs correctly (`python src/main.py`)

---

## 1. Commit & Push Source Code (main branch)

```powershell
# Stage all changes
git add -A

# Commit with a descriptive message
git commit -m "feat: <short description of changes>

- <bullet point 1>
- <bullet point 2>
- <bullet point 3>"

# Push to main
git push origin main
```

---

## 2. Build the Executable

```powershell
# Build using the project's .venv and spec file
& ".venv\Scripts\python.exe" -m PyInstaller attendance.spec --noconfirm

# Verify the output
Test-Path "dist\attendance.exe"
(Get-Item "dist\attendance.exe").Length / 1MB
```

---

## 3. Push to Release Branch

```powershell
# Switch to release branch
git checkout release

# Copy the new exe over the old one
Copy-Item "dist\attendance.exe" -Destination "attendance.exe" -Force

# Commit and push
git add attendance.exe
git commit -m "Update attendance.exe - <short description>"
git push origin release

# Switch back to main
git checkout main
```

---

## 4. Verify

- [ ] Check https://github.com/Adrimars/Attendance_System/tree/main — source committed
- [ ] Check https://github.com/Adrimars/Attendance_System/tree/release — exe updated
- [ ] Download exe from release branch and test launch

---

## Push History

| Date       | Commit (main)  | Description |
|------------|----------------|-------------|
| 2026-03-01 | `e8ffb07`      | feat: name-surname display order, Turkish character support in PDFs and search |

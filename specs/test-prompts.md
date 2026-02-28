# Test Prompts — RFID Dance Class Attendance System

These prompts are designed to manually test every major feature of the application.
Run the app (`AttendanceSystem.exe` or `python src/main.py`) and follow each section in order.

---

## 0. Prerequisites

- Ensure `attendance.db` does **not** exist (fresh start), or delete it before testing.
- Have the Simulation Panel visible (click `💻 Sim` toggle on the attendance screen).
- Note down test card IDs to use: `1234567890`, `9876543210`, `1111111111`, `2222222222`, `3333333333`.

---

## 1. Application Startup

| # | Prompt | Expected Result |
|---|--------|-----------------|
| 1.1 | Launch the application. | Window opens at 1280×800, title bar visible. Attendance screen loads directly — **no PIN prompt**. |
| 1.2 | Verify the attendance screen shows a `● LISTENING` indicator. | Green dot with "LISTENING" text is visible, confirming RFID input is active. |
| 1.3 | Verify the `💻 Sim` toggle button is visible. | A button labeled `💻 Sim` appears on the sections bar area. |

---

## 2. Sections Setup (Admin Panel)

| # | Prompt | Expected Result |
|---|--------|-----------------|
| 2.1 | Press **Ctrl+P**. | A PIN dialog appears. On first run it should show "Create PIN" setup screen. |
| 2.2 | Set a new admin PIN (e.g., `1234`). Confirm it. | PIN is saved. Admin Panel opens with three tabs: **Sections**, **Students**, **Settings**. |
| 2.3 | Go to the **Sections** tab. Click **Add Section**. Create: Name=`Hip Hop Beginner`, Type=`Normal`, Level=`Beginner`, Day=`Monday`, Time=`10:00`. | Section is created and appears in the list. |
| 2.4 | Create a second section: Name=`Ballet Advanced`, Type=`Technique`, Level=`Advanced`, Day=`Tuesday`, Time=`14:00`. | Section appears in the list. |
| 2.5 | Create a third section: Name=`Contemporary`, Type=`Normal`, Level=`Intermediate`, Day=today's weekday (e.g., `Sunday`), Time=`16:00`. | Section appears. **This section matches today's day — important for attendance tests.** |
| 2.6 | Edit the `Hip Hop Beginner` section — change time to `11:00`. | Section updates. Time shows `11:00`. |
| 2.7 | Delete the `Ballet Advanced` section. Confirm the deletion dialog. | Section is removed from the list. |
| 2.8 | Re-create `Ballet Advanced` with Day=today's weekday, Time=`15:00`. | Section appears. **Two sections now match today's day.** |
| 2.9 | Close the Admin Panel. | Panel closes. Attendance screen regains focus. |

---

## 3. New Student Registration (Unknown Card)

| # | Prompt | Expected Result |
|---|--------|-----------------|
| 3.1 | Open the Sim panel. Type `1234567890` and press Enter. | **Red flash** — unknown card detected. Registration dialog opens asking for First Name, Last Name, with section checkboxes. |
| 3.2 | Enter First Name=`Ali`, Last Name=`Yılmaz`. Check **Contemporary** and **Ballet Advanced** (today's sections). Click Register. | Student is created. Attendance is immediately marked for today's sessions. **Green flash** with welcome message showing `Ali Yılmaz`. |
| 3.3 | Type `9876543210` and press Enter. Register as `Elif Kaya`, assign to **Contemporary** only. | Red flash → registration dialog → green flash after registration. |
| 3.4 | Type `1111111111` and press Enter. Register as `Ahmet Demir`, assign to **Hip Hop Beginner** only (NOT today's weekday). | Red flash → registration → student created. Since Hip Hop Beginner is on Monday (not today), **no attendance is marked for today**. Verify no error occurs. |
| 3.5 | Type `2222222222` and press Enter. Register as `Zeynep Çelik`, assign to **no sections** (uncheck all). | Registration completes. On next tap, a section assignment dialog should appear. |

---

## 4. Known Student Attendance (RFID Tap)

| # | Prompt | Expected Result |
|---|--------|-----------------|
| 4.1 | Type `1234567890` (Ali Yılmaz) in Sim panel and press Enter. | **Yellow flash** — duplicate tap. Message says "Already marked present" (Ali was marked present during registration). |
| 4.2 | Type `9876543210` (Elif Kaya) in Sim panel. | **Yellow flash** — duplicate tap (marked present during registration). |
| 4.3 | Type `1111111111` (Ahmet Demir) in Sim panel. | Ahmet is only in Hip Hop Beginner (Monday). If today is NOT Monday: no matching section for today → appropriate handling (may show "no sections scheduled today" or similar message). |
| 4.4 | Type `2222222222` (Zeynep Çelik — no sections) in Sim panel. | **Section Assignment Dialog** opens because student has zero enrolled sections. |
| 4.5 | In the Section Assignment Dialog, assign Zeynep to `Contemporary`. Confirm. | Dialog closes. Attendance is processed — Zeynep is marked present in Contemporary. Green flash. |
| 4.6 | Type `2222222222` again. | **Yellow flash** — duplicate tap. |

---

## 5. Invalid Card Input

| # | Prompt | Expected Result |
|---|--------|-----------------|
| 5.1 | Type `12345` (only 5 digits) in Sim panel and press Enter. | **Red flash** — "Invalid card" message. Input is rejected (not 10 digits). |
| 5.2 | Type `ABCDEFGHIJ` (10 letters) in Sim panel. | **Red flash** — "Invalid card". Only decimal digits are accepted. |
| 5.3 | Type `12345678901` (11 digits) in Sim panel. | **Red flash** — "Invalid card". Too many digits. |
| 5.4 | Type nothing and press Enter. | No action or a graceful rejection. No crash. |

---

## 6. Today's Attendance Log

| # | Prompt | Expected Result |
|---|--------|-----------------|
| 6.1 | After the taps in sections 3–4, verify the attendance log on the main screen. | A list/table shows today's attendance entries: Ali Yılmaz (Present), Elif Kaya (Present), Zeynep Çelik (Present), with section names and timestamps. |
| 6.2 | Verify each entry shows the correct section and method (`RFID`). | Section names match enrolled sections. Method = RFID. |

---

## 7. Admin Panel — Students Tab

| # | Prompt | Expected Result |
|---|--------|-----------------|
| 7.1 | Press **Ctrl+P**, enter PIN `1234`. Go to the **Students** tab. | Student list shows all registered students: Ali Yılmaz, Elif Kaya, Ahmet Demir, Zeynep Çelik. |
| 7.2 | Use the **search** box — type `Ali`. | List filters to show only `Ali Yılmaz`. |
| 7.3 | Clear search. Sort students by **name**. | Students are sorted alphabetically. |
| 7.4 | Click **Edit** on Ahmet Demir. Change his name to `Ahmet Demirci`. | Name updates in the list. |
| 7.5 | Click **Edit** on Ahmet Demirci. In the RFID field, change card to `3333333333`. | Card ID updates. Old card `1111111111` is unlinked. |
| 7.6 | Click **Edit** on Ahmet Demirci. Try to set card to `1234567890` (Ali's card). | Error message: card is already assigned to another student. |
| 7.7 | Click **Attendance** button on Ali Yılmaz. | `ManualAttendanceDialog` opens showing Ali's attendance history. |
| 7.8 | In the manual attendance dialog, toggle Ali's status from Present to Absent for one of today's sessions. | Status changes. Method is flagged as `manual`. |
| 7.9 | Close manual attendance dialog. Close Admin Panel. | Panels close cleanly. |

---

## 8. Admin Panel — Settings Tab

### 8.1 PIN Management

| # | Prompt | Expected Result |
|---|--------|-----------------|
| 8.1.1 | Open Admin Panel → Settings tab → **Change Admin PIN** section. | Shows current PIN required + new PIN + confirm new PIN fields. |
| 8.1.2 | Enter wrong current PIN, then a new PIN. Click Change. | Error: wrong current PIN. |
| 8.1.3 | Enter correct current PIN (`1234`), new PIN `5678`, confirm `5678`. Click Change. | Success message. PIN is updated. |
| 8.1.4 | Close Admin Panel. Press Ctrl+P. Try old PIN `1234`. | Access denied. |
| 8.1.5 | Try new PIN `5678`. | Admin Panel opens. |

### 8.2 Language Switching

| # | Prompt | Expected Result |
|---|--------|-----------------|
| 8.2.1 | In Settings → **Language** section, switch from English to **Turkish**. | All UI labels, buttons, and messages switch to Turkish immediately. |
| 8.2.2 | Close Admin Panel. Verify attendance screen labels are in Turkish. | Labels are in Turkish (e.g., `DİNLENİYOR` or equivalent). |
| 8.2.3 | Re-open Admin Panel (Ctrl+P, PIN). Switch back to English. | UI reverts to English. |

### 8.3 Section Mode

| # | Prompt | Expected Result |
|---|--------|-----------------|
| 8.3.1 | In Settings → **Section Mode** section, toggle the mode. | Mode changes between 0 and 1. Observe any behavioral difference in attendance filtering. |

### 8.4 Backup & Restore

| # | Prompt | Expected Result |
|---|--------|-----------------|
| 8.4.1 | In Settings → **Database Backup** section, click **Backup Now**. | Success message. A timestamped `.db` file appears in the `backups/` folder. |
| 8.4.2 | Click **Backup Now** again. | A second backup file is created with a different timestamp. |
| 8.4.3 | Delete a student (e.g., Zeynep Çelik) from the Students tab. | Student is removed. |
| 8.4.4 | Go to Settings → Backup → Click **Restore**. Select the backup file from before the deletion. | Database is restored. Zeynep Çelik reappears in the Students list. |

### 8.5 Inactive Students

| # | Prompt | Expected Result |
|---|--------|-----------------|
| 8.5.1 | In Settings → **Inactive Students** section, set the consecutive absence threshold to `2`. | Threshold is saved. |
| 8.5.2 | Click **Refresh Inactive Status**. | Status is recomputed for all students. |
| 8.5.3 | Create a student who has been absent for 2+ consecutive sessions (or simulate via manual attendance). | After refreshing inactive status, the student should be flagged as inactive. |
| 8.5.4 | Tap the inactive student's card on the attendance screen. | Attendance is processed normally, but a **purple flash** appears as a visual warning. |
| 8.5.5 | In the Students tab, verify the inactive student has a **red-tinted row**. | Row is visually distinct. |
| 8.5.6 | Toggle "Hide inactive students" checkbox. | Inactive students are filtered out of the list. |

### 8.6 Daily Report

| # | Prompt | Expected Result |
|---|--------|-----------------|
| 8.6.1 | In Settings → **Daily Report** section, click the generate report button. | A report dialog opens showing today's attendance with **per-section breakdown**: total enrolled, present, absent for each section. |
| 8.6.2 | Verify the numbers match the attendance actions performed so far. | Counts are accurate. |

### 8.7 Google Sheets Summary

| # | Prompt | Expected Result |
|---|--------|-----------------|
| 8.7.1 | (If credentials are configured) In Settings → **Sheets Summary**, enter a Google Sheet URL and click Push. | Attendance summary is pushed to the sheet. Success message shown. |
| 8.7.2 | (If credentials are NOT configured) Click Push without credentials. | Clear error message about missing credentials. No crash. |

### 8.8 Google Sheets Import (Legacy)

| # | Prompt | Expected Result |
|---|--------|-----------------|
| 8.8.1 | (If credentials configured) Click Import → enter a Google Sheet URL. | Import preview dialog opens showing student counts, RFID status, attendance counts. |
| 8.8.2 | Set an attendance threshold of 3. Confirm import. | Students below the threshold without RFID are excluded. Others are imported. |
| 8.8.3 | (Without credentials) Attempt import. | Clear error message. No crash. |

---

## 9. PIN Lockout

| # | Prompt | Expected Result |
|---|--------|-----------------|
| 9.1 | Press Ctrl+P. Enter a wrong PIN 5 times in a row. | After 5 failed attempts, the PIN dialog closes automatically (lockout). |
| 9.2 | Press Ctrl+P again. Enter the correct PIN. | Admin Panel opens (lockout resets between dialog instances). |

---

## 10. Auto-Backup

| # | Prompt | Expected Result |
|---|--------|-----------------|
| 10.1 | Check the `backups/` folder after the app has been running. | At least one auto-created backup file should exist (created on startup). |
| 10.2 | (Optional: wait 4 hours or check backup scheduling logic.) | Additional auto-backups are created at 4-hour intervals. |

---

## 11. Backup Pruning

| # | Prompt | Expected Result |
|---|--------|-----------------|
| 11.1 | Manually create backups until there are 12+ files in `backups/`. | After the next auto-backup runs, only the 10 most recent files should remain (oldest are pruned). |

---

## 12. Error Handling

| # | Prompt | Expected Result |
|---|--------|-----------------|
| 12.1 | Delete the `attendance.db` file while the app is running. Try to tap a card. | A user-friendly error dialog appears — **no raw Python traceback**. |
| 12.2 | Provide a non-existent path for Google credentials in Settings. Try to import/push. | Clear error message. No crash. |
| 12.3 | Confirm that `logs/` folder contains log files with today's date. | Log file exists with entries for startup, card taps, errors, etc. |

---

## 13. Window & UI Behavior

| # | Prompt | Expected Result |
|---|--------|-----------------|
| 13.1 | Resize the main window. | Window is resizable. Content adjusts properly. |
| 13.2 | Open Admin Panel. Try to interact with the main window behind it. | Admin Panel is modal (`grab_set()`) — main window should not be interactable while panel is open. |
| 13.3 | Close Admin Panel using the X button. | Panel closes. Attendance screen refreshes and regains focus. |
| 13.4 | Verify RFID hidden entry regains focus after closing Admin Panel. | Tapping a card in Sim panel works immediately after panel close. |

---

## 14. Pagination (Students Tab)

| # | Prompt | Expected Result |
|---|--------|-----------------|
| 14.1 | Register 25+ students (use Sim panel with unique 10-digit IDs). | Students are created. |
| 14.2 | Open Admin Panel → Students tab. | Only the first 20 students are shown (PAGE_SIZE=20). Pagination controls (Next/Previous) are visible. |
| 14.3 | Click Next page. | Remaining students appear. |
| 14.4 | Click Previous page. | Returns to the first page. |

---

## 15. Multi-Section Attendance (Same Day)

| # | Prompt | Expected Result |
|---|--------|-----------------|
| 15.1 | Ensure Ali Yılmaz is enrolled in **two sections that match today's weekday** (Contemporary + Ballet Advanced). | Verified from section 3.2. |
| 15.2 | Delete today's attendance records for Ali (via manual attendance dialog — mark absent, or reset DB). Re-tap card `1234567890`. | **Green flash**. Ali is marked present in **both** sections simultaneously. Attendance log shows two entries — one per section. |

---

## 16. Locale-Independent Weekday

| # | Prompt | Expected Result |
|---|--------|-----------------|
| 16.1 | Switch language to Turkish. | UI shows Turkish labels. |
| 16.2 | Tap a known student's card who has sections on today's weekday. | Attendance is processed correctly — weekday matching uses English internally regardless of UI language. |

---

## 17. Student Deletion Cascade

| # | Prompt | Expected Result |
|---|--------|-----------------|
| 17.1 | Delete a student (e.g., Elif Kaya) from the Students tab. Confirm. | Student is deleted. All associated attendance records and section assignments are removed. No orphan records. |
| 17.2 | Tap Elif's old card `9876543210`. | **Red flash** — unknown card. Registration dialog opens (card is no longer linked). |

---

## 18. Section Deletion Cascade

| # | Prompt | Expected Result |
|---|--------|-----------------|
| 18.1 | Delete a section that has enrolled students and attendance records. | Deletion cascades correctly: attendance → sessions → student_sections → section. No FK errors. |
| 18.2 | Verify affected students still exist but no longer show the deleted section. | Students are intact. Section is removed from their enrollment. |

---

## 19. Full Workflow — End-to-End

| # | Prompt | Expected Result |
|---|--------|-----------------|
| 19.1 | Fresh start (delete `attendance.db`). Launch app. | App starts cleanly. No errors. Attendance screen with LISTENING indicator. |
| 19.2 | Create 3 sections via Admin Panel (at least 2 on today's weekday). | Sections created. |
| 19.3 | Tap 5 unknown cards. Register all 5 students with various section assignments. | All 5 registered. Green flashes for those with today's sections. |
| 19.4 | Tap all 5 cards again. | Yellow flashes for those already present. Appropriate handling for others. |
| 19.5 | Open Admin Panel → Students. Verify all 5 students appear. Search, sort, edit one student's name. | All CRUD operations work. |
| 19.6 | Open Admin Panel → Settings → Generate Daily Report. | Report shows accurate per-section breakdown. |
| 19.7 | Create a backup. Delete one student. Restore from backup. | Student reappears after restore. |
| 19.8 | Switch language to Turkish and back to English. | UI updates correctly both ways. |
| 19.9 | Close and relaunch the app. | All data persists. Language preference is remembered. |

---

## 20. Performance Checks

| # | Prompt | Expected Result |
|---|--------|-----------------|
| 20.1 | Tap a card — measure response time visually. | Flash feedback appears within ~500ms of pressing Enter. |
| 20.2 | Tap two cards rapidly in sequence (< 1 second apart). | Both taps are processed correctly. No merged/corrupted card IDs. |
| 20.3 | With 50+ students in the DB, open the Students tab. | List loads promptly (< 1 second). Pagination works. |

---

*End of test prompts.*

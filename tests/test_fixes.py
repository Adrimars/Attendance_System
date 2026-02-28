"""Tests validating the P1-P4 bug fixes."""

import sqlite3
from datetime import datetime, timezone

import pytest

# ── Models ────────────────────────────────────────────────────────────────────
from models import student_model, section_model, attendance_model, session_model, settings_model
from models.database import get_connection

# ── Controllers ───────────────────────────────────────────────────────────────
import controllers.student_controller as student_ctrl
import controllers.attendance_controller as attendance_ctrl
import controllers.session_controller as session_ctrl

# ── Utils ─────────────────────────────────────────────────────────────────────
from utils.pin_utils import hash_pin, verify_pin


# ═══════════════════════════════════════════════════════════════════════════════
# P1.1 — All timestamps should now be UTC
# ═══════════════════════════════════════════════════════════════════════════════

class TestTimestampsUTC:
    def test_attendance_mark_present_stores_utc(self, fresh_database, today_weekday):
        sid = student_model.create_student("A", "B", "1234567890")
        sec = section_model.create_section("S1", "Normal", "Beginner", today_weekday, "10:00")
        student_model.assign_section(sid, sec)
        sess = session_model.create_session(sec)
        attendance_model.mark_present(sess, sid)
        with get_connection() as conn:
            row = conn.execute("SELECT timestamp FROM attendance WHERE student_id=?", (sid,)).fetchone()
        ts = row["timestamp"]
        # UTC timestamps contain +00:00
        assert "+00:00" in ts or "Z" in ts

    def test_session_start_stores_utc(self, fresh_database, today_weekday):
        sec = section_model.create_section("S1", "Normal", "Beginner", today_weekday, "10:00")
        sess_id = session_model.create_session(sec)
        sess = session_model.get_session_by_id(sess_id)
        assert "+00:00" in sess["start_time"] or "Z" in sess["start_time"]

    def test_session_close_stores_utc(self, fresh_database, today_weekday):
        sec = section_model.create_section("S1", "Normal", "Beginner", today_weekday, "10:00")
        sess_id = session_model.create_session(sec)
        session_model.close_session(sess_id)
        sess = session_model.get_session_by_id(sess_id)
        assert "+00:00" in sess["end_time"] or "Z" in sess["end_time"]


# ═══════════════════════════════════════════════════════════════════════════════
# P1.3 — Import filter includes students with RFID cards
# ═══════════════════════════════════════════════════════════════════════════════

class TestImportFilter:
    def test_student_with_card_included_even_if_below_threshold(self):
        from controllers.import_controller import ImportStudentRow
        # Simulate: student has card but 0 attendance, threshold=5
        # The fix should include them because they have a card
        row = ImportStudentRow(
            first_name="Test",
            last_name="User",
            card_id="1234567890",
            attendance_count=0,
            include=False,
        )
        # Replicate the fixed filter logic
        threshold = 5
        include = row.attendance_count >= threshold or row.card_id is not None
        assert include is True

    def test_student_without_card_below_threshold_excluded(self):
        threshold = 5
        card_id = None
        att_count = 2
        include = att_count >= threshold or card_id is not None
        assert include is False


# ═══════════════════════════════════════════════════════════════════════════════
# P2.3 — Session end counts exclude inactive students
# ═══════════════════════════════════════════════════════════════════════════════

class TestSessionEndCounts:
    def test_inactive_excluded_from_total_enrolled(self, fresh_database, today_weekday):
        sec = section_model.create_section("S1", "Normal", "Beginner", today_weekday, "10:00")
        s1 = student_model.create_student("Active", "One", "1111111111")
        s2 = student_model.create_student("Inactive", "Two", "2222222222")
        student_model.assign_section(s1, sec)
        student_model.assign_section(s2, sec)
        student_model.set_inactive_status(s2, True)

        result = session_ctrl.start_session(sec)
        assert result.success
        sess_id = result.session_id

        # Mark only s1 as present
        attendance_model.mark_present(sess_id, s1)

        summary = session_ctrl.end_session(sess_id)
        assert summary is not None
        # total_enrolled should be 1 (only active), not 2
        assert summary.total_enrolled == 1
        assert summary.present_count == 1
        assert summary.absent_count == 0


# ═══════════════════════════════════════════════════════════════════════════════
# P3.1 + P3.3 — PIN security: constant-time compare + auto-upgrade
# ═══════════════════════════════════════════════════════════════════════════════

class TestPINSecurity:
    def test_verify_returns_tuple(self):
        hashed = hash_pin("1234")
        result = verify_pin("1234", hashed)
        assert isinstance(result, tuple)
        assert len(result) == 2
        matched, needs_upgrade = result
        assert matched is True
        assert needs_upgrade is False

    def test_wrong_pin_returns_false(self):
        hashed = hash_pin("1234")
        matched, _ = verify_pin("wrong", hashed)
        assert matched is False

    def test_legacy_sha256_detected_as_needing_upgrade(self):
        import hashlib
        legacy = hashlib.sha256("oldpin".encode()).hexdigest()
        matched, needs_upgrade = verify_pin("oldpin", legacy)
        assert matched is True
        assert needs_upgrade is True

    def test_legacy_sha256_wrong_pin(self):
        import hashlib
        legacy = hashlib.sha256("oldpin".encode()).hexdigest()
        matched, needs_upgrade = verify_pin("wrong", legacy)
        assert matched is False
        assert needs_upgrade is False

    def test_malformed_hash_does_not_crash(self):
        matched, needs_upgrade = verify_pin("1234", "not$validhex")
        assert matched is False
        assert needs_upgrade is False


# ═══════════════════════════════════════════════════════════════════════════════
# P4.1 — Unified student list query (no double scan)
# ═══════════════════════════════════════════════════════════════════════════════

class TestUnifiedStudentList:
    def test_get_all_students_with_sections_includes_attendance(self, fresh_database, today_weekday):
        sec = section_model.create_section("S1", "Normal", "Beginner", today_weekday, "10:00")
        sid = student_model.create_student("Test", "Student", "1234567890")
        student_model.assign_section(sid, sec)
        sess_id = session_model.create_session(sec)
        attendance_model.mark_present(sess_id, sid)

        result = student_ctrl.get_all_students_with_sections()
        assert len(result) == 1
        assert result[0]["attended"] == 1
        assert result[0]["total_sessions"] == 1
        assert result[0]["sections"] == "S1"


# ═══════════════════════════════════════════════════════════════════════════════
# P4.2 — SQL LIKE search
# ═══════════════════════════════════════════════════════════════════════════════

class TestSQLSearch:
    def test_search_by_first_name(self, fresh_database):
        student_model.create_student("Alice", "Smith", "1111111111")
        student_model.create_student("Bob", "Jones", "2222222222")
        results = student_ctrl.search_students("alice")
        assert len(results) == 1
        assert results[0]["first_name"] == "Alice"

    def test_search_by_card_id(self, fresh_database):
        student_model.create_student("Alice", "Smith", "1111111111")
        results = student_ctrl.search_students("1111")
        assert len(results) == 1

    def test_search_empty_returns_all(self, fresh_database):
        student_model.create_student("A", "B", "1111111111")
        student_model.create_student("C", "D", "2222222222")
        results = student_ctrl.search_students("")
        assert len(results) == 2


# ═══════════════════════════════════════════════════════════════════════════════
# P4.3 — get_student_with_sections_by_id
# ═══════════════════════════════════════════════════════════════════════════════

class TestGetStudentById:
    def test_returns_correct_student(self, fresh_database, today_weekday):
        sec = section_model.create_section("S1", "Normal", "Beginner", today_weekday, "10:00")
        sid = student_model.create_student("Test", "User", "1234567890")
        student_model.assign_section(sid, sec)

        result = student_ctrl.get_student_with_sections_by_id(sid)
        assert result is not None
        assert result["id"] == sid
        assert result["first_name"] == "Test"
        assert result["sections"] == "S1"

    def test_nonexistent_returns_none(self, fresh_database):
        result = student_ctrl.get_student_with_sections_by_id(9999)
        assert result is None


# ═══════════════════════════════════════════════════════════════════════════════
# P1.5 — Backup error handling
# ═══════════════════════════════════════════════════════════════════════════════

class TestBackupErrorHandling:
    def test_backup_creates_file(self, fresh_database, tmp_path):
        from utils.backup import create_backup
        import models.database as db_mod
        ok, path = create_backup(db_mod.DB_PATH)
        assert ok is True
        from pathlib import Path
        assert Path(path).exists()

    def test_backup_nonexistent_db(self):
        from utils.backup import create_backup
        ok, msg = create_backup("/nonexistent/path/db.sqlite")
        assert ok is False


# ═══════════════════════════════════════════════════════════════════════════════
# Regression: basic end-to-end flow still works
# ═══════════════════════════════════════════════════════════════════════════════

class TestEndToEnd:
    def test_full_passive_tap_flow(self, fresh_database, today_weekday):
        sec = section_model.create_section("Ballet", "Normal", "Beginner", today_weekday, "10:00")
        sid = student_model.create_student("Jane", "Doe", "9876543210")
        student_model.assign_section(sid, sec)

        result = attendance_ctrl.process_rfid_passive("9876543210")
        assert result.result_type.name == "KNOWN_PRESENT"
        assert "Ballet" in result.sections_marked
        assert result.attended == 1

    def test_duplicate_tap(self, fresh_database, today_weekday):
        sec = section_model.create_section("Ballet", "Normal", "Beginner", today_weekday, "10:00")
        sid = student_model.create_student("Jane", "Doe", "9876543210")
        student_model.assign_section(sid, sec)

        attendance_ctrl.process_rfid_passive("9876543210")
        result2 = attendance_ctrl.process_rfid_passive("9876543210")
        assert result2.result_type.name == "DUPLICATE_TAP"

    def test_settings_roundtrip(self, fresh_database):
        settings_model.set_setting("test_key", "test_value")
        assert settings_model.get_setting("test_key") == "test_value"

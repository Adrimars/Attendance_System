"""
import_controller.py — Legacy Google Sheets import controller (Phase 2, Task 2.7).

Reads a legacy attendance Google Sheet with the following column structure:
  • name            — full name  OR  first_name + last_name  columns
  • rfid            — RFID card ID (may be empty)
  • D_YYYY_MM_DD    — one column per session date; value "1" or non-empty = attended

Import rules (per spec, FR-2.7 / FR-2.8):
  • Count the number of D_ columns where the student has a non-empty / truthy value
    to get their total attendance.
  • Exclude students whose attendance count is below the threshold AND who have
    no RFID card assigned (they will never be able to tap in).
  • Include all students who have an RFID card (regardless of attendance count).
  • Include all students who have met/exceeded the threshold.

Two-phase API:
  1. preview_import(sheet_url, threshold, credentials_path) → ImportPreview
  2. commit_import(preview)                                  → (imported_count, skipped_count)
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

import models.student_model as student_model
import models.settings_model as settings_model
from models.database import transaction
from utils.logger import log_info, log_error, log_warning


# ──────────────────────────────────────────────────────────────────────────────
# Data structures
# ──────────────────────────────────────────────────────────────────────────────

@dataclass
class ImportStudentRow:
    """One student parsed from the Google Sheet."""
    first_name: str
    last_name: str
    card_id: Optional[str]          # None / "" if not present in sheet
    attendance_count: int           # number of D_ columns with a truthy value
    include: bool                   # will be imported if True


@dataclass
class ImportPreview:
    """
    Summary and row list returned by preview_import().

    Fields:
        sheet_title:       Name of the Google Sheet tab.
        total_rows:        Total rows parsed from the sheet (excl. header).
        with_rfid:         Rows that have a non-empty rfid column.
        without_rfid:      Rows that have no rfid column value.
        session_count:     Number of D_ date columns found.
        will_import:       Rows that pass the threshold/RFID filter.
        will_skip:         Rows that fail the filter.
        students:          Full list (ImportStudentRow) for display.
        error:             Non-None if a non-fatal warning occurred.
    """
    sheet_title: str
    total_rows: int
    with_rfid: int
    without_rfid: int
    session_count: int
    will_import: int
    will_skip: int
    students: list[ImportStudentRow] = field(default_factory=list)
    error: Optional[str] = None


# ──────────────────────────────────────────────────────────────────────────────
# Preview
# ──────────────────────────────────────────────────────────────────────────────

def preview_import(
    sheet_url: str,
    threshold: int,
    credentials_path: Optional[str] = None,
) -> tuple[Optional[ImportPreview], str]:
    """
    Connect to the Google Sheet, parse rows, and return a preview without
    writing anything to the local database.

    Args:
        sheet_url:        Full URL or share link for the Google Sheet.
        threshold:        Minimum attendance count; students below this AND
                          without RFID will be excluded.
        credentials_path: Path to the service-account JSON key file.
                          Falls back to the value stored in settings if None.

    Returns:
        (ImportPreview, "")     on success.
        (None, error_message)   on failure.
    """
    # ── Resolve credentials ───────────────────────────────────────────────────
    creds_path = credentials_path or settings_model.get_setting(
        "google_credentials_path"
    )
    if not creds_path:
        return None, (
            "Google credentials path is not configured.\n"
            "Set it in Settings → Google Credentials Path."
        )

    # ── Connect to Google Sheets ──────────────────────────────────────────────
    try:
        import gspread
        from google.oauth2.service_account import Credentials

        scopes = [
            "https://www.googleapis.com/auth/spreadsheets.readonly",
            "https://www.googleapis.com/auth/drive.readonly",
        ]
        creds = Credentials.from_service_account_file(creds_path, scopes=scopes)
        gc = gspread.authorize(creds)
    except FileNotFoundError:
        return None, f"Credentials file not found:\n{creds_path}"
    except Exception as exc:  # noqa: BLE001
        log_error(f"import_controller: credentials error — {exc}")
        return None, f"Could not load credentials:\n{exc}"

    # ── Open the spreadsheet ──────────────────────────────────────────────────
    try:
        spreadsheet = gc.open_by_url(sheet_url)
        ws = spreadsheet.sheet1
        sheet_title = ws.title
    except Exception as exc:  # noqa: BLE001
        log_error(f"import_controller: could not open sheet — {exc}")
        return None, (
            f"Could not open the Google Sheet.\n\n"
            f"Check the URL and that the service account has 'Viewer' access.\n\n"
            f"Error: {exc}"
        )

    # ── Parse rows ────────────────────────────────────────────────────────────
    try:
        records = ws.get_all_records(default_blank="")
    except Exception as exc:  # noqa: BLE001
        log_error(f"import_controller: could not read records — {exc}")
        return None, f"Could not read sheet data:\n{exc}"

    if not records:
        return None, "The sheet appears to be empty (no data rows found)."

    # Normalise header names to lowercase-stripped for case-insensitive lookup
    sample_keys = [k.strip().lower() for k in records[0].keys()] if records else []
    date_col_keys = [
        k for k in records[0].keys()
        if k.strip().lower().startswith("d_") and len(k.strip()) >= 8
    ]

    # Determine name columns
    has_split_names = (
        "first_name" in sample_keys and "last_name" in sample_keys
    )
    has_full_name = "name" in sample_keys
    if not has_split_names and not has_full_name:
        return None, (
            "Sheet must contain a 'name' column  OR  both 'first_name' and "
            "'last_name' columns."
        )

    # Find the rfid column (case-insensitive)
    rfid_key: Optional[str] = next(
        (k for k in records[0].keys() if k.strip().lower() == "rfid"),
        None,
    )

    parsed: list[ImportStudentRow] = []
    for row in records:
        # Parse name
        if has_split_names:
            first = str(row.get("first_name", "")).strip()
            last  = str(row.get("last_name",  "")).strip()
        else:
            full = str(row.get("name", "")).strip()
            parts = full.split(None, 1)
            first = parts[0] if parts else ""
            last  = parts[1] if len(parts) > 1 else ""

        if not first and not last:
            continue  # skip blank rows

        # Parse rfid
        card_raw = str(row.get(rfid_key, "")).strip() if rfid_key else ""
        card_id: Optional[str] = card_raw if card_raw else None

        # Count sessions attended
        att_count = sum(
            1 for col in date_col_keys
            if str(row.get(col, "")).strip() not in ("", "0")
        )

        # Apply filter rule
        has_card = bool(card_id)
        include  = has_card or (att_count >= threshold)

        parsed.append(
            ImportStudentRow(
                first_name=first,
                last_name=last,
                card_id=card_id,
                attendance_count=att_count,
                include=include,
            )
        )

    with_rfid    = sum(1 for r in parsed if r.card_id)
    without_rfid = len(parsed) - with_rfid
    will_import  = sum(1 for r in parsed if r.include)
    will_skip    = len(parsed) - will_import

    log_info(
        f"Import preview: sheet='{sheet_title}' "
        f"rows={len(parsed)} will_import={will_import} will_skip={will_skip}"
    )

    return ImportPreview(
        sheet_title=sheet_title,
        total_rows=len(parsed),
        with_rfid=with_rfid,
        without_rfid=without_rfid,
        session_count=len(date_col_keys),
        will_import=will_import,
        will_skip=will_skip,
        students=parsed,
    ), ""


# ──────────────────────────────────────────────────────────────────────────────
# Commit
# ──────────────────────────────────────────────────────────────────────────────

def commit_import(preview: ImportPreview) -> tuple[int, int, str]:
    """
    Insert accepted rows from a previously built ImportPreview into the DB.

    Optimisations vs. the original:
    - C2: Pre-fetch the student list **once** before the loop — O(N+M) instead
      of O(N×M) for N import rows and M existing students.
    - C3: All inserts share a **single transaction** so a crash or error rolls
      back the entire import atomically — no partial-import state.

    Args:
        preview: An ImportPreview returned by preview_import().

    Returns:
        (imported, skipped, error_message)
        error_message is "" on success.
    """
    to_import = [r for r in preview.students if r.include]
    if not to_import:
        return 0, 0, ""

    # ── Pre-fetch existing data ONCE (C2) ──────────────────────────────────────
    existing_all = student_model.get_all_students()
    known_names: set[tuple[str, str]] = {
        (s["first_name"].lower(), s["last_name"].lower())
        for s in existing_all
    }
    known_cards: set[str] = {
        s["card_id"] for s in existing_all if s["card_id"]
    }

    imported = 0
    skipped  = 0

    # ── Atomic transaction for all writes (C3) ──────────────────────────────
    # Raw SQL is used here because all writes must share one connection for
    # true atomicity — calling student_model.create_student() would open its
    # own connection, breaking the transaction boundary.
    try:
        with transaction() as conn:
            for row in to_import:
                name_key = (row.first_name.lower(), row.last_name.lower())

                if name_key in known_names:
                    log_warning(
                        f"Import skip (name exists): "
                        f"'{row.first_name} {row.last_name}'"
                    )
                    skipped += 1
                    continue

                if row.card_id and row.card_id in known_cards:
                    log_warning(
                        f"Import skip (card taken): "
                        f"'{row.first_name} {row.last_name}' card='{row.card_id}'"
                    )
                    skipped += 1
                    continue

                created_at = datetime.now(timezone.utc).isoformat()
                conn.execute(
                    """
                    INSERT INTO students (first_name, last_name, card_id, created_at)
                    VALUES (?, ?, ?, ?);
                    """,
                    (row.first_name, row.last_name, row.card_id, created_at),
                )

                # Update in-memory sets so later rows in the same batch see
                # the newly inserted student (avoids inserting duplicates
                # within a single import run).
                known_names.add(name_key)
                if row.card_id:
                    known_cards.add(row.card_id)
                imported += 1

    except sqlite3.Error as exc:
        log_error(f"import_controller: DB error during commit — {exc}")
        return 0, 0, f"Database error during import (rolled back):\n{exc}"
    except Exception as exc:  # noqa: BLE001
        log_error(f"import_controller: unexpected error during commit — {exc}")
        return 0, 0, f"Unexpected error (rolled back):\n{exc}"

    log_info(f"Import committed: imported={imported} skipped={skipped}")
    return imported, skipped, ""

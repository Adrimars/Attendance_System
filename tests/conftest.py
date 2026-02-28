"""Shared fixtures for all test modules."""

import sys
import os
from pathlib import Path
from datetime import datetime

import pytest

# Ensure src/ is on sys.path so imports like `from models.database import ...` work.
_SRC = str(Path(__file__).resolve().parents[1] / "src")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

from models.database import initialise_database, close_connection, _local, DB_PATH
import models.database as _db_mod


@pytest.fixture(autouse=True)
def fresh_database(tmp_path, monkeypatch):
    """Give every test its own empty SQLite database."""
    db_file = tmp_path / "test_attendance.db"

    # Monkey-patch DB_PATH so all production code uses the temp file.
    monkeypatch.setattr(_db_mod, "DB_PATH", str(db_file))

    # Make sure the thread-local cache is clear.
    if hasattr(_local, "conn"):
        try:
            _local.conn.close()
        except Exception:
            pass
        del _local.conn

    initialise_database()
    yield db_file

    # Tear down: close and clear the cached connection.
    close_connection()
    if hasattr(_local, "conn"):
        try:
            _local.conn.close()
        except Exception:
            pass
        del _local.conn


# ── helpers ──────────────────────────────────────────────────────────────────

_DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


@pytest.fixture()
def today_weekday():
    """Return today's English weekday name."""
    return _DAYS[datetime.now().weekday()]


@pytest.fixture()
def other_weekday():
    """Return a weekday that is NOT today."""
    idx = (datetime.now().weekday() + 1) % 7
    return _DAYS[idx]

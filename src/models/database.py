"""
database.py — SQLite connection manager.

Responsibilities:
- Resolve the path to attendance.db (project root).
- Open connections with WAL journal mode enabled on every open.
- Initialise the full schema (6 tables) on first run.
- Provide a lightweight migration mechanism via a schema_version table.
"""

import sqlite3
import os
from pathlib import Path
from contextlib import contextmanager
from typing import Generator

from utils.logger import log_info, log_error, log_debug

# ── Database file path ────────────────────────────────────────────────────────
_SRC_DIR = Path(__file__).resolve().parent      # src/models/
_ROOT_DIR = _SRC_DIR.parents[1]                 # project root
DB_PATH: str = str(_ROOT_DIR / "attendance.db")

# ── Current schema version ────────────────────────────────────────────────────
_SCHEMA_VERSION = 1

# ── DDL statements ─────────────────────────────────────────────────────────────
_DDL_SCHEMA_VERSION = """
CREATE TABLE IF NOT EXISTS schema_version (
    version  INTEGER PRIMARY KEY
);
"""

_DDL_STUDENTS = """
CREATE TABLE IF NOT EXISTS students (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    first_name  TEXT NOT NULL,
    last_name   TEXT NOT NULL,
    card_id     TEXT UNIQUE,
    created_at  TEXT NOT NULL
);
"""

_DDL_SECTIONS = """
CREATE TABLE IF NOT EXISTS sections (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT NOT NULL,
    type        TEXT NOT NULL,
    level       TEXT NOT NULL,
    day         TEXT NOT NULL,
    time        TEXT NOT NULL
);
"""

_DDL_STUDENT_SECTIONS = """
CREATE TABLE IF NOT EXISTS student_sections (
    student_id  INTEGER NOT NULL REFERENCES students(id),
    section_id  INTEGER NOT NULL REFERENCES sections(id),
    PRIMARY KEY (student_id, section_id)
);
"""

_DDL_SESSIONS = """
CREATE TABLE IF NOT EXISTS sessions (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    section_id  INTEGER NOT NULL REFERENCES sections(id),
    date        TEXT NOT NULL,
    start_time  TEXT NOT NULL,
    end_time    TEXT,
    status      TEXT NOT NULL DEFAULT 'active'
);
"""

_DDL_ATTENDANCE = """
CREATE TABLE IF NOT EXISTS attendance (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id  INTEGER NOT NULL REFERENCES sessions(id),
    student_id  INTEGER NOT NULL REFERENCES students(id),
    status      TEXT NOT NULL,
    method      TEXT NOT NULL,
    timestamp   TEXT NOT NULL,
    UNIQUE (session_id, student_id)
);
"""

_DDL_SETTINGS = """
CREATE TABLE IF NOT EXISTS settings (
    key    TEXT PRIMARY KEY,
    value  TEXT NOT NULL
);
"""

_ALL_DDL = [
    _DDL_SCHEMA_VERSION,
    _DDL_STUDENTS,
    _DDL_SECTIONS,
    _DDL_STUDENT_SECTIONS,
    _DDL_SESSIONS,
    _DDL_ATTENDANCE,
    _DDL_SETTINGS,
]

# ── Default settings rows ─────────────────────────────────────────────────────
_DEFAULT_SETTINGS: list[tuple[str, str]] = [
    ("absence_threshold", "3"),
    ("admin_pin", ""),           # Empty means not yet configured; PIN dialog will prompt
    ("language", "en"),
    ("google_credentials_path", ""),
]


def _get_raw_connection() -> sqlite3.Connection:
    """
    Open a new SQLite connection with the required PRAGMAs applied.
    WAL mode is enabled on every open as required by the spec.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA foreign_keys=ON;")
    return conn


@contextmanager
def get_connection() -> Generator[sqlite3.Connection, None, None]:
    """
    Context manager that yields an open SQLite connection and commits/rolls back
    automatically.

    Usage::

        with get_connection() as conn:
            conn.execute("INSERT INTO ...")
    """
    conn = _get_raw_connection()
    try:
        yield conn
        conn.commit()
    except sqlite3.Error as exc:
        conn.rollback()
        log_error(f"DB error — rolling back transaction: {exc}")
        raise
    finally:
        conn.close()


def initialise_database() -> None:
    """
    Create all tables if they do not exist and seed default settings.
    Runs the schema migration if the stored version is older than current.
    Safe to call on every startup.
    """
    log_info(f"Initialising database at {DB_PATH}")
    conn = _get_raw_connection()
    try:
        cursor = conn.cursor()

        # Create all tables
        for ddl in _ALL_DDL:
            cursor.execute(ddl)

        # Seed default settings (INSERT OR IGNORE to avoid overwriting user data)
        for key, value in _DEFAULT_SETTINGS:
            cursor.execute(
                "INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?);",
                (key, value),
            )

        # Record schema version
        cursor.execute(
            "INSERT OR IGNORE INTO schema_version (version) VALUES (?);",
            (_SCHEMA_VERSION,),
        )

        conn.commit()
        log_debug(f"Schema initialised at version {_SCHEMA_VERSION}.")

        # Run any pending migrations
        _run_migrations(cursor, conn)

    except sqlite3.Error as exc:
        conn.rollback()
        log_error(f"Schema initialisation failed: {exc}")
        raise
    finally:
        conn.close()


def _run_migrations(cursor: sqlite3.Cursor, conn: sqlite3.Connection) -> None:
    """
    Apply incremental schema migrations.
    Currently a stub — add migration blocks as schema evolves.
    """
    row = cursor.execute("SELECT version FROM schema_version;").fetchone()
    stored_version: int = row["version"] if row else 0

    if stored_version < _SCHEMA_VERSION:
        # Future migrations go here, e.g.:
        # if stored_version < 2:
        #     cursor.execute("ALTER TABLE students ADD COLUMN ...")
        cursor.execute(
            "UPDATE schema_version SET version = ?;", (_SCHEMA_VERSION,)
        )
        conn.commit()
        log_info(f"Migrated schema from v{stored_version} → v{_SCHEMA_VERSION}.")

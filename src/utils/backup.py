"""
backup.py — Automated database backup utility.

Creates timestamped copies of the SQLite database in a ``backups/`` folder.
Retains only the most recent MAX_BACKUPS copies to save disk space.

Usage (manual)::

    from utils.backup import create_backup
    ok, info = create_backup("attendance.db")

Automatic periodic backups are scheduled by ``views/app.py`` via
``App._schedule_auto_backup()``.
"""

from __future__ import annotations

import shutil
from datetime import datetime
from pathlib import Path

from utils.logger import log_info, log_warning

MAX_BACKUPS = 10
_BACKUP_DIR = Path("backups")


def create_backup(db_path: str | Path) -> tuple[bool, str]:
    """Create a timestamped backup of the database file.

    Args:
        db_path: Path to the ``attendance.db`` file.

    Returns:
        ``(True, backup_path_str)`` on success.
        ``(False, error_message)`` on failure.
    """
    db_path = Path(db_path)
    if not db_path.exists():
        msg = f"Database file not found: {db_path}"
        log_warning(f"Backup skipped — {msg}")
        return False, msg

    backup_dir = db_path.parent / "backups"
    backup_dir.mkdir(exist_ok=True)

    timestamp   = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"attendance_{timestamp}.db"
    backup_path = backup_dir / backup_name

    try:
        shutil.copy2(db_path, backup_path)
        log_info(f"Auto-backup created: {backup_path}")
    except OSError as exc:
        log_warning(f"Backup failed: {exc}")
        return False, str(exc)

    _prune_old_backups(backup_dir)
    return True, str(backup_path)


def _prune_old_backups(backup_dir: Path) -> None:
    """Keep only the most recent MAX_BACKUPS backup files."""
    backups = sorted(
        backup_dir.glob("attendance_*.db"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    for old in backups[MAX_BACKUPS:]:
        try:
            old.unlink()
            log_info(f"Pruned old backup: {old.name}")
        except OSError:
            pass

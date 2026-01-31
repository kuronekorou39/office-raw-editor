"""Backup management for Office Open XML files."""

import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional

from ..utils.constants import BACKUP_SUFFIX


class BackupManager:
    """Manages backup creation for Office Open XML files."""

    def __init__(self, backup_dir: Optional[Path] = None):
        """Initialize the BackupManager.

        Args:
            backup_dir: Optional directory to store backups.
                       If None, backups are created next to the original file.
        """
        self.backup_dir = backup_dir

    def create_backup(self, file_path: Path, timestamped: bool = True) -> Path:
        """Create a backup of the specified file.

        Args:
            file_path: Path to the file to backup.
            timestamped: If True, add timestamp to backup filename.

        Returns:
            Path to the created backup file.

        Raises:
            FileNotFoundError: If the file doesn't exist.
            PermissionError: If permission denied.
        """
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        if timestamped:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"{file_path.stem}_{timestamp}{BACKUP_SUFFIX}{file_path.suffix}"
        else:
            backup_name = f"{file_path.stem}{BACKUP_SUFFIX}{file_path.suffix}"

        if self.backup_dir:
            self.backup_dir.mkdir(parents=True, exist_ok=True)
            backup_path = self.backup_dir / backup_name
        else:
            backup_path = file_path.parent / backup_name

        shutil.copy2(file_path, backup_path)
        return backup_path

    def list_backups(self, original_path: Path) -> list[Path]:
        """List all backups for a specific file.

        Args:
            original_path: Path to the original file.

        Returns:
            List of backup file paths, sorted by modification time (newest first).
        """
        if self.backup_dir:
            search_dir = self.backup_dir
        else:
            search_dir = original_path.parent

        pattern = f"{original_path.stem}*{BACKUP_SUFFIX}{original_path.suffix}"
        backups = list(search_dir.glob(pattern))
        backups.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        return backups

    def restore_backup(self, backup_path: Path, restore_path: Path) -> bool:
        """Restore a file from backup.

        Args:
            backup_path: Path to the backup file.
            restore_path: Path to restore the file to.

        Returns:
            True if restoration was successful.

        Raises:
            FileNotFoundError: If the backup file doesn't exist.
            PermissionError: If permission denied.
        """
        if not backup_path.exists():
            raise FileNotFoundError(f"Backup not found: {backup_path}")

        shutil.copy2(backup_path, restore_path)
        return True

    def cleanup_old_backups(self, original_path: Path, keep_count: int = 5) -> int:
        """Remove old backups, keeping only the most recent ones.

        Args:
            original_path: Path to the original file.
            keep_count: Number of backups to keep.

        Returns:
            Number of backups removed.
        """
        backups = self.list_backups(original_path)
        removed = 0

        for backup in backups[keep_count:]:
            try:
                backup.unlink()
                removed += 1
            except (PermissionError, OSError):
                pass

        return removed

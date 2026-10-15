"""Tests for BackupManager."""

import os
import time

import pytest

from office_raw_editor.core.backup import BackupManager
from office_raw_editor.utils.constants import BACKUP_SUFFIX


def test_create_backup_next_to_original(sample_docx):
    backup = BackupManager().create_backup(sample_docx)

    assert backup.parent == sample_docx.parent
    assert backup.name.startswith("sample_")
    assert backup.name.endswith(f"{BACKUP_SUFFIX}.docx")
    assert backup.read_bytes() == sample_docx.read_bytes()


def test_create_backup_without_timestamp(sample_docx):
    backup = BackupManager().create_backup(sample_docx, timestamped=False)
    assert backup.name == f"sample{BACKUP_SUFFIX}.docx"


def test_create_backup_in_dedicated_dir(sample_docx, tmp_path):
    backup_dir = tmp_path / "backups" / "nested"
    backup = BackupManager(backup_dir=backup_dir).create_backup(sample_docx)

    assert backup.parent == backup_dir
    assert backup.exists()


def test_create_backup_missing_file_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        BackupManager().create_backup(tmp_path / "missing.docx")


def test_list_backups_newest_first(sample_docx):
    manager = BackupManager()
    older = manager.create_backup(sample_docx, timestamped=False)
    newer = manager.create_backup(sample_docx)
    # Force a clear mtime ordering independent of filesystem resolution
    now = time.time()
    os.utime(older, (now - 100, now - 100))
    os.utime(newer, (now, now))

    backups = manager.list_backups(sample_docx)
    assert backups == [newer, older]


def test_list_backups_ignores_other_files(sample_docx):
    manager = BackupManager()
    manager.create_backup(sample_docx)
    (sample_docx.parent / "other.docx").write_bytes(b"x")
    (sample_docx.parent / "sample_notes.txt").write_text("x")

    assert len(manager.list_backups(sample_docx)) == 1


def test_cleanup_old_backups_keeps_most_recent(sample_docx):
    manager = BackupManager()
    created = []
    now = time.time()
    for i in range(4):
        path = manager.create_backup(sample_docx, timestamped=False)
        renamed = path.with_name(f"sample_{i}{BACKUP_SUFFIX}.docx")
        path.rename(renamed)
        os.utime(renamed, (now + i, now + i))
        created.append(renamed)

    removed = manager.cleanup_old_backups(sample_docx, keep_count=2)

    assert removed == 2
    remaining = set(manager.list_backups(sample_docx))
    assert remaining == {created[3], created[2]}


def test_restore_backup(sample_docx, tmp_path):
    manager = BackupManager()
    backup = manager.create_backup(sample_docx)
    sample_docx.write_bytes(b"corrupted")

    assert manager.restore_backup(backup, sample_docx)
    assert sample_docx.read_bytes() == backup.read_bytes()


def test_restore_missing_backup_raises(sample_docx, tmp_path):
    with pytest.raises(FileNotFoundError):
        BackupManager().restore_backup(tmp_path / "nope.docx", sample_docx)

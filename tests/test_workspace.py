"""Tests for WorkspaceManager (extract, change tracking, repackage, revert)."""

import zipfile
from pathlib import Path

import pytest

from office_raw_editor.core.workspace import WorkspaceManager
from office_raw_editor.utils.constants import WORKDIR_PREFIX
from tests.conftest import make_office_file

DOC = str(Path("word") / "document.xml")
STYLES = str(Path("word") / "styles.xml")
NEW_FILE = str(Path("word") / "new.xml")


def test_open_file_extracts_into_base_dir(workspace, sample_docx, tmp_path):
    ws = workspace.open_file(sample_docx, create_backup=False)

    assert ws.parent == tmp_path / "workspaces"
    assert ws.name.startswith(f"{WORKDIR_PREFIX}sample_")
    assert (ws / "word" / "document.xml").is_file()
    assert workspace.current_workspace == ws
    assert workspace.source_file == sample_docx.resolve()
    assert workspace.source_docx == workspace.source_file
    assert not workspace.is_modified


def test_open_file_creates_backup_by_default(workspace, sample_docx):
    workspace.open_file(sample_docx)
    backups = list(sample_docx.parent.glob("sample_*.backup.docx"))
    assert len(backups) == 1


def test_open_file_rejects_missing_and_invalid(workspace, tmp_path):
    with pytest.raises(FileNotFoundError):
        workspace.open_file(tmp_path / "missing.docx")

    bogus = tmp_path / "bogus.docx"
    bogus.write_text("nope")
    with pytest.raises(ValueError):
        workspace.open_file(bogus)
    assert workspace.current_workspace is None


def test_open_file_closes_previous_workspace(workspace, sample_docx, sample_xlsx):
    first = workspace.open_file(sample_docx, create_backup=False)
    second = workspace.open_file(sample_xlsx, create_backup=False)

    assert not first.exists()
    assert second.exists()
    assert workspace.source_file == sample_xlsx.resolve()


def test_unchanged_workspace_reports_no_modifications(open_workspace):
    assert not open_workspace.check_modifications()
    assert open_workspace.get_file_statuses() == {}
    assert not open_workspace.is_modified


def test_statuses_track_modified_added_deleted(open_workspace):
    ws = open_workspace.current_workspace
    (ws / DOC).write_text("<w:document/>", encoding="utf-8")
    (ws / NEW_FILE).write_text("<new/>", encoding="utf-8")
    (ws / STYLES).unlink()

    assert open_workspace.check_modifications()
    assert open_workspace.is_modified
    assert open_workspace.get_file_statuses() == {DOC: "M", NEW_FILE: "A", STYLES: "D"}


def test_rewriting_identical_content_is_not_a_change(open_workspace):
    ws = open_workspace.current_workspace
    doc = ws / DOC
    doc.write_bytes(doc.read_bytes())

    assert not open_workspace.check_modifications()
    assert open_workspace.get_file_statuses() == {}


def test_save_as_repackages_changes_and_resets_state(open_workspace, tmp_path):
    ws = open_workspace.current_workspace
    (ws / DOC).write_text("<w:document>edited</w:document>", encoding="utf-8")
    (ws / STYLES).unlink()
    open_workspace.check_modifications()

    out = open_workspace.save_as(tmp_path / "out" / "edited.docx")

    with zipfile.ZipFile(out) as zf:
        assert b"edited" in zf.read("word/document.xml")
        assert "word/styles.xml" not in zf.namelist()
    assert not open_workspace.is_modified
    assert open_workspace.get_file_statuses() == {}
    # The original is untouched
    with zipfile.ZipFile(open_workspace.source_file) as zf:
        assert "word/styles.xml" in zf.namelist()


def test_save_as_refuses_overwrite_unless_asked(open_workspace, tmp_path):
    target = tmp_path / "existing.docx"
    target.write_bytes(b"old")

    with pytest.raises(FileExistsError):
        open_workspace.save_as(target)
    assert target.read_bytes() == b"old"

    open_workspace.save_as(target, overwrite=True)
    assert zipfile.is_zipfile(target)


def test_save_overwrites_source(open_workspace):
    ws = open_workspace.current_workspace
    (ws / DOC).write_text("<w:document>saved</w:document>", encoding="utf-8")

    saved = open_workspace.save()

    assert saved == open_workspace.source_file
    with zipfile.ZipFile(saved) as zf:
        assert b"saved" in zf.read("word/document.xml")


def test_save_without_workspace_raises(workspace, tmp_path):
    with pytest.raises(RuntimeError):
        workspace.save()
    with pytest.raises(RuntimeError):
        workspace.save_as(tmp_path / "x.docx")


def test_revert_modified_file_restores_original_bytes(open_workspace):
    ws = open_workspace.current_workspace
    original = (ws / DOC).read_bytes()
    (ws / DOC).write_text("<broken/>", encoding="utf-8")
    assert open_workspace.can_revert_file(DOC)

    assert open_workspace.revert_file(DOC)

    assert (ws / DOC).read_bytes() == original
    assert open_workspace.get_file_statuses() == {}


def test_revert_deleted_file_recreates_it(open_workspace):
    ws = open_workspace.current_workspace
    (ws / STYLES).unlink()

    assert open_workspace.revert_file(STYLES)

    assert (ws / STYLES).is_file()
    assert open_workspace.get_file_statuses() == {}


def test_revert_added_file_removes_it(open_workspace):
    ws = open_workspace.current_workspace
    (ws / NEW_FILE).write_text("<new/>", encoding="utf-8")

    assert open_workspace.revert_file(NEW_FILE)

    assert not (ws / NEW_FILE).exists()


def test_revert_unchanged_file_is_noop(open_workspace):
    assert not open_workspace.can_revert_file(DOC)
    assert not open_workspace.revert_file(DOC)


def test_revert_without_workspace_raises(workspace):
    with pytest.raises(RuntimeError):
        workspace.revert_file(DOC)


def test_close_removes_workspace_dir(open_workspace):
    ws = open_workspace.current_workspace
    open_workspace.close()

    assert not ws.exists()
    assert open_workspace.current_workspace is None
    assert open_workspace.source_file is None
    assert open_workspace.get_file_statuses() == {}


def test_get_absolute_path_and_file_tree(open_workspace, workspace):
    ws = open_workspace.current_workspace
    assert open_workspace.get_absolute_path(DOC) == ws / DOC

    tree = open_workspace.get_file_tree()
    by_path = {entry["path"]: entry for entry in tree}
    assert by_path["word"]["is_dir"] is True
    assert by_path[DOC]["is_dir"] is False
    assert by_path[DOC]["size"] == (ws / DOC).stat().st_size

    workspace.close()
    assert workspace.get_absolute_path(DOC) is None
    assert workspace.get_file_tree() == []


def test_xlsx_round_trip(workspace, sample_xlsx, tmp_path):
    ws = workspace.open_file(sample_xlsx, create_backup=False)
    sheet = ws / "xl" / "worksheets" / "sheet1.xml"
    sheet.write_text(sheet.read_text(encoding="utf-8").replace("<sheetData/>", "<sheetData><row/></sheetData>"), encoding="utf-8")

    out = workspace.save_as(tmp_path / "edited.xlsx")

    with zipfile.ZipFile(out) as zf:
        assert b"<row/>" in zf.read("xl/worksheets/sheet1.xml")
        assert "xl/workbook.xml" in zf.namelist()

"""Shared fixtures: minimal Office files, isolated workspaces and settings."""

import os
import zipfile
from pathlib import Path

# Must be set before any Qt module is imported so tests never need a display
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6.QtCore import QSettings

from office_raw_editor.core.workspace import WorkspaceManager
from office_raw_editor.utils import settings as settings_module


CONTENT_TYPES_XML = (
    '<?xml version="1.0" encoding="UTF-8"?>'
    '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
    '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
    '<Default Extension="xml" ContentType="application/xml"/>'
    '<Default Extension="png" ContentType="image/png"/>'
    '</Types>'
)

DOCUMENT_XML = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
    '<w:body><w:p><w:r><w:t>Hello {{placeholder}}</w:t></w:r></w:p>'
    '<w:p><w:r><w:t>second placeholder line</w:t></w:r></w:p></w:body></w:document>'
)

# 1x1 PNG (binary content, must be skipped by text search and preserved byte-for-byte)
PNG_BYTES = bytes.fromhex(
    "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c489"
    "0000000d49444154789c6360000002000154a24f5d0000000049454e44ae426082"
)

# Default members for each supported package kind
_DOCX_FILES = {
    "[Content_Types].xml": CONTENT_TYPES_XML,
    "_rels/.rels": '<?xml version="1.0"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"/>',
    "word/document.xml": DOCUMENT_XML,
    "word/styles.xml": '<?xml version="1.0"?><w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"/>',
    "word/_rels/document.xml.rels": '<?xml version="1.0"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"/>',
    "word/media/image1.png": PNG_BYTES,
}

_XLSX_FILES = {
    "[Content_Types].xml": CONTENT_TYPES_XML,
    "_rels/.rels": '<?xml version="1.0"?><Relationships/>',
    "xl/workbook.xml": '<?xml version="1.0"?><workbook/>',
    "xl/worksheets/sheet1.xml": '<?xml version="1.0"?><worksheet><sheetData/></worksheet>',
    "xl/sharedStrings.xml": '<?xml version="1.0"?><sst><si><t>placeholder</t></si></sst>',
}


def make_office_file(path: Path, files: dict | None = None) -> Path:
    """Write a ZIP with the given members (defaults to a minimal .docx layout)."""
    files = _DOCX_FILES if files is None else files
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zf:
        for name, content in files.items():
            zf.writestr(name, content)
    return path


@pytest.fixture
def sample_docx(tmp_path) -> Path:
    return make_office_file(tmp_path / "sample.docx")


@pytest.fixture
def sample_xlsx(tmp_path) -> Path:
    return make_office_file(tmp_path / "book.xlsx", _XLSX_FILES)


@pytest.fixture
def workspace(tmp_path) -> WorkspaceManager:
    """WorkspaceManager whose working copies live under tmp_path."""
    manager = WorkspaceManager(base_dir=tmp_path / "workspaces")
    yield manager
    manager.close()


@pytest.fixture
def open_workspace(workspace, sample_docx):
    """A workspace with sample.docx already extracted (backup disabled)."""
    workspace.open_file(sample_docx, create_backup=False)
    return workspace


@pytest.fixture(autouse=True)
def isolated_settings(tmp_path, monkeypatch):
    """Back Settings with an INI file under tmp_path so tests never touch the registry.

    QSettings(org, app) always uses the native backend (the registry on Windows),
    so the constructor is swapped for the explicit INI-file form.
    """
    ini_path = tmp_path / "settings" / "test.ini"
    ini_path.parent.mkdir(parents=True, exist_ok=True)

    def _init(self):
        self._settings = QSettings(str(ini_path), QSettings.Format.IniFormat)

    monkeypatch.setattr(settings_module.Settings, "__init__", _init)
    monkeypatch.setattr(settings_module, "_settings", None)
    yield


@pytest.fixture(autouse=True)
def no_modal_dialogs(monkeypatch):
    """Turn any unexpected modal dialog into a test failure instead of a hang.

    Tests that expect a dialog override the specific static method themselves.
    """
    from PySide6.QtWidgets import QDialog, QMessageBox

    def _unexpected(*args, **kwargs):
        raise AssertionError("unexpected modal dialog in test")

    for name in ("question", "warning", "critical", "information"):
        monkeypatch.setattr(QMessageBox, name, staticmethod(_unexpected))
    monkeypatch.setattr(QMessageBox, "exec", _unexpected)
    monkeypatch.setattr(QDialog, "exec", _unexpected)
    yield


def close_editor_window():
    """Drop every editor tab and close the EditorWindow singleton without prompting."""
    from office_raw_editor.ui.editor_window import EditorWindow

    instance = EditorWindow._instance
    if instance is not None:
        instance._editors.clear()
        instance.tab_widget.clear()
        instance.close()
        instance.deleteLater()
        EditorWindow._instance = None


@pytest.fixture(autouse=True)
def reset_editor_window(monkeypatch):
    """Give every test a fresh EditorWindow singleton and close it afterwards."""
    from office_raw_editor.ui.editor_window import EditorWindow

    monkeypatch.setattr(EditorWindow, "_instance", None)
    yield
    close_editor_window()

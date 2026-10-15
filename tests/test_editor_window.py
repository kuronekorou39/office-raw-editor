"""Tests for the tabbed EditorWindow."""

from pathlib import Path

import pytest
from PySide6.QtWidgets import QMessageBox

from office_raw_editor.ui.editor_window import EditorWindow


@pytest.fixture
def xml_files(tmp_path) -> list[Path]:
    paths = []
    for i in range(2):
        path = tmp_path / f"file{i}.xml"
        path.write_text(f"<r>{i}</r>", encoding="utf-8")
        paths.append(path)
    return paths


@pytest.fixture
def window(qtbot) -> EditorWindow:
    # Not registered with qtbot: its auto-close would prompt for dirty tabs.
    # conftest.reset_editor_window closes it without prompting.
    return EditorWindow.get_instance()


def test_get_instance_is_singleton_while_visible(window):
    window.show()
    assert EditorWindow.get_instance() is window

    window.hide()
    # A hidden window is treated as closed: the next call creates a fresh one
    assert EditorWindow.get_instance() is not window


def test_open_file_adds_tab_with_tooltip(window, xml_files):
    assert window.open_file(xml_files[0])

    assert window.tab_widget.count() == 1
    assert window.tab_widget.tabText(0) == "file0.xml"
    assert window.tab_widget.tabToolTip(0) == str(xml_files[0])
    assert window.is_file_open(xml_files[0])
    assert window.isVisible()


def test_opening_same_file_twice_focuses_existing_tab(window, xml_files):
    window.open_file(xml_files[0])
    window.open_file(xml_files[1])
    assert window.tab_widget.currentIndex() == 1

    window.open_file(xml_files[0])

    assert window.tab_widget.count() == 2
    assert window.tab_widget.currentIndex() == 0


def test_open_missing_file_warns_and_returns_false(window, tmp_path, monkeypatch):
    monkeypatch.setattr(QMessageBox, "warning", lambda *a, **k: None)
    assert not window.open_file(tmp_path / "missing.xml")
    assert window.tab_widget.count() == 0


def test_modified_tab_shows_marker_and_unsaved_list(window, xml_files):
    window.open_file(xml_files[0])
    editor = window._editors[str(xml_files[0])]

    editor.editor.setPlainText("<r>changed</r>")

    assert window.tab_widget.tabText(0) == "● file0.xml"
    assert window.has_unsaved_changes()
    assert window.get_unsaved_files() == [str(xml_files[0])]


def test_save_all_writes_every_dirty_editor_and_relays_signal(window, xml_files, qtbot):
    for path in xml_files:
        window.open_file(path)
    for path in xml_files:
        window._editors[str(path)].editor.setPlainText(f"<saved>{path.name}</saved>")

    with qtbot.waitSignal(window.file_saved, timeout=1000):
        assert window.save_all()

    assert not window.has_unsaved_changes()
    for path in xml_files:
        assert path.read_text(encoding="utf-8") == f"<saved>{path.name}</saved>"
    assert window.tab_widget.tabText(0) == "file0.xml"


def test_closing_last_tab_closes_window(window, xml_files):
    window.open_file(xml_files[0])
    window._close_current_tab()
    assert window.tab_widget.count() == 0
    assert not window.is_file_open(xml_files[0])
    assert not window.isVisible()


def test_closing_dirty_tab_asks_and_can_cancel(window, xml_files, monkeypatch):
    window.open_file(xml_files[0])
    window._editors[str(xml_files[0])].editor.setPlainText("<dirty/>")

    monkeypatch.setattr(QMessageBox, "question", lambda *a, **k: QMessageBox.StandardButton.Cancel)
    window._close_current_tab()
    assert window.tab_widget.count() == 1

    monkeypatch.setattr(QMessageBox, "question", lambda *a, **k: QMessageBox.StandardButton.Discard)
    window._close_current_tab()
    assert window.tab_widget.count() == 0
    assert xml_files[0].read_text(encoding="utf-8") == "<r>0</r>"


def test_closing_window_with_dirty_editor_can_be_cancelled(window, xml_files, monkeypatch):
    window.open_file(xml_files[0])
    window._editors[str(xml_files[0])].editor.setPlainText("<dirty/>")
    monkeypatch.setattr(QMessageBox, "question", lambda *a, **k: QMessageBox.StandardButton.Cancel)

    assert not window.close()
    assert window.tab_widget.count() == 1

"""Tests for MainWindow (workspace lifecycle, content search, UI state)."""

from pathlib import Path

import pytest
from PySide6.QtWidgets import QMessageBox

from office_raw_editor.core.workspace import WorkspaceManager
from office_raw_editor.ui.editor_window import EditorWindow
from office_raw_editor.ui.main_window import MainWindow
from office_raw_editor.utils.constants import APP_TITLE
from tests.conftest import close_editor_window

DOC = str(Path("word") / "document.xml")
STYLES = str(Path("word") / "styles.xml")


@pytest.fixture
def window(qtbot, tmp_path) -> MainWindow:
    win = MainWindow()
    # Keep working copies inside tmp_path instead of the system temp dir
    win.workspace = WorkspaceManager(base_dir=tmp_path / "workspaces")
    win.show()
    yield win
    # Discard all state first so closeEvent never prompts (qtbot.addWidget would close too early)
    win._modification_timer.stop()
    close_editor_window()
    win.workspace.close()
    win.close()
    win.deleteLater()


@pytest.fixture
def loaded(window, sample_docx) -> MainWindow:
    window._load_docx(sample_docx)
    return window


def test_initial_state_shows_welcome(window):
    assert window.welcome_widget.isVisibleTo(window)
    assert not window.content_widget.isVisibleTo(window)
    assert window.windowTitle() == APP_TITLE
    for action in (window.action_save, window.action_save_as, window.action_close, window.action_refresh):
        assert not action.isEnabled()
    assert not window.btn_save.isEnabled()


def test_load_docx_switches_to_content_view(loaded, sample_docx):
    assert loaded.content_widget.isVisibleTo(loaded)
    assert not loaded.welcome_widget.isVisibleTo(loaded)
    assert loaded.windowTitle() == f"{sample_docx.name} - {APP_TITLE}"
    assert DOC in loaded.file_tree._items_map
    assert loaded.action_save.isEnabled()
    assert loaded.btn_save.isEnabled()
    assert str(loaded.workspace.current_workspace) in loaded.info_banner_path.toolTip()
    assert sample_docx.name in loaded.status_label.text()


def test_load_invalid_file_shows_error_and_stays_on_welcome(window, tmp_path, monkeypatch):
    errors = []
    monkeypatch.setattr(QMessageBox, "critical", lambda *a, **k: errors.append(a))
    bogus = tmp_path / "bogus.docx"
    bogus.write_text("nope")

    window._load_docx(bogus)

    assert len(errors) == 1
    assert window.welcome_widget.isVisibleTo(window)


def test_selecting_file_shows_info_and_preview(loaded):
    loaded.file_tree.setCurrentItem(loaded.file_tree._items_map[DOC])

    assert loaded.info_label.text() == "document.xml"
    text = loaded.info_text.toPlainText()
    assert "ファイル: document.xml" in text
    assert "{{placeholder}}" in text
    assert not loaded.image_scroll.isVisibleTo(loaded)


def test_selecting_image_shows_preview(loaded):
    image = str(Path("word") / "media" / "image1.png")
    loaded.file_tree.setCurrentItem(loaded.file_tree._items_map[image])

    assert loaded.image_scroll.isVisibleTo(loaded)
    assert "画像プレビュー" in loaded.info_text.toPlainText()


def test_selecting_folder_shows_folder_info(loaded):
    loaded.file_tree.setCurrentItem(loaded.file_tree._items_map["word"])
    assert loaded.info_text.toPlainText() == "フォルダ: word"


def test_content_search_marks_matching_files(loaded):
    loaded.content_search_input.setText("placeholder")
    loaded._run_content_search()

    tree = loaded.file_tree
    assert tree._search_matches == {DOC}
    assert tree._items_map[DOC].text(1).endswith("(2件)")
    assert "1ファイル / 2件" in loaded.status_label.text()
    assert not tree._items_map[STYLES].isHidden()


def test_content_search_skips_binary_files(loaded):
    counts = loaded._search_files_for_text("PNG")
    assert str(Path("word") / "media" / "image1.png") not in counts


def test_content_search_is_case_sensitive(loaded):
    assert DOC in loaded._search_files_for_text("Hello")
    assert DOC not in loaded._search_files_for_text("hello")


def test_filter_checkbox_hides_non_matches(loaded):
    loaded.content_search_input.setText("placeholder")
    loaded.chk_content_filter.setChecked(True)

    assert loaded.file_tree._items_map[STYLES].isHidden()
    assert not loaded.file_tree._items_map[DOC].isHidden()

    loaded.chk_content_filter.setChecked(False)
    assert not loaded.file_tree._items_map[STYLES].isHidden()


def test_search_with_no_hits_reports_it(loaded):
    loaded.content_search_input.setText("no-such-text")
    loaded._run_content_search()
    assert "ヒットなし" in loaded.status_label.text()
    assert loaded.file_tree._search_matches == set()


def test_clear_content_search_resets_input_and_tree(loaded):
    loaded.content_search_input.setText("placeholder")
    loaded.chk_content_filter.setChecked(True)
    loaded._run_content_search()

    loaded._clear_content_search()

    assert loaded.content_search_input.text() == ""
    assert all(not item.isHidden() for item in loaded.file_tree._items_map.values())


def test_modification_check_updates_header_and_title(loaded, sample_docx):
    ws = loaded.workspace.current_workspace
    (ws / DOC).write_text("<w:document/>", encoding="utf-8")
    (ws / STYLES).unlink()

    loaded._check_modifications()

    assert loaded.tree_header.text() == "ファイル構造  (M:1, D:1)"
    assert loaded.windowTitle().startswith("● ")
    assert loaded.modified_label.text().strip() == "● 未保存"
    assert loaded.file_tree._items_map[DOC].text(3) == "M"
    assert loaded.file_tree._items_map[STYLES].text(3) == "D"


def test_save_docx_writes_back_to_source(loaded, sample_docx):
    import zipfile

    (loaded.workspace.current_workspace / DOC).write_text("<w:document>saved</w:document>", encoding="utf-8")
    loaded._check_modifications()

    loaded.save_docx()

    with zipfile.ZipFile(sample_docx) as zf:
        assert b"saved" in zf.read("word/document.xml")
    assert not loaded.workspace.is_modified
    assert loaded.modified_label.text() == ""
    assert "保存完了" in loaded.status_label.text()


def test_editor_save_marks_workspace_modified(loaded, qtbot):
    path = loaded.workspace.current_workspace / DOC
    loaded._open_in_internal_editor(path)
    editor_window = EditorWindow._instance
    editor = editor_window._editors[str(path)]
    editor.editor.setPlainText("<w:document>from editor</w:document>")

    with qtbot.waitSignal(editor_window.file_saved, timeout=1000):
        editor.save_file()

    assert loaded.workspace.is_modified
    assert "保存しました" in loaded.status_label.text()


def test_reopening_editor_connects_signal_once(loaded):
    path = loaded.workspace.current_workspace / DOC
    loaded._open_in_internal_editor(path)
    loaded._open_in_internal_editor(path)
    editor_window = EditorWindow._instance

    assert loaded._connected_editor_window is editor_window
    assert editor_window.tab_widget.count() == 1
    # Exactly one connection: a save produces exactly one status update
    calls = []
    editor_window.file_saved.connect(lambda p: calls.append(p))
    editor_window._editors[str(path)].editor.setPlainText("<w:document>x</w:document>")
    editor_window._editors[str(path)].save_file()
    assert calls == [str(path)]


def test_close_workspace_returns_to_welcome(loaded):
    ws = loaded.workspace.current_workspace
    loaded.close_workspace()

    assert not ws.exists()
    assert loaded.welcome_widget.isVisibleTo(loaded)
    assert loaded.file_tree.topLevelItemCount() == 0
    assert loaded.windowTitle() == APP_TITLE


def test_confirm_close_asks_when_modified_and_respects_cancel(loaded, monkeypatch):
    (loaded.workspace.current_workspace / DOC).write_text("<w:document/>", encoding="utf-8")

    monkeypatch.setattr(QMessageBox, "question", lambda *a, **k: QMessageBox.StandardButton.Cancel)
    assert not loaded._confirm_close_current()

    monkeypatch.setattr(QMessageBox, "question", lambda *a, **k: QMessageBox.StandardButton.Discard)
    assert loaded._confirm_close_current()


def test_confirm_close_can_save_before_closing(loaded, sample_docx, monkeypatch):
    import zipfile

    (loaded.workspace.current_workspace / DOC).write_text("<w:document>kept</w:document>", encoding="utf-8")
    monkeypatch.setattr(QMessageBox, "question", lambda *a, **k: QMessageBox.StandardButton.Save)

    assert loaded._confirm_close_current()

    with zipfile.ZipFile(sample_docx) as zf:
        assert b"kept" in zf.read("word/document.xml")


def test_confirm_close_is_silent_when_clean(loaded, monkeypatch):
    monkeypatch.setattr(QMessageBox, "question", lambda *a, **k: pytest.fail("should not ask"))
    assert loaded._confirm_close_current()


def test_file_revert_from_tree_restores_original(loaded, monkeypatch):
    monkeypatch.setattr(QMessageBox, "question", lambda *a, **k: QMessageBox.StandardButton.Yes)
    ws = loaded.workspace.current_workspace
    original = (ws / DOC).read_bytes()
    (ws / DOC).write_text("<w:document/>", encoding="utf-8")
    loaded._check_modifications()

    loaded._on_file_revert(DOC)

    assert (ws / DOC).read_bytes() == original
    assert loaded.file_tree._items_map[DOC].text(3) == ""


def test_file_delete_from_tree(loaded, monkeypatch):
    monkeypatch.setattr(QMessageBox, "question", lambda *a, **k: QMessageBox.StandardButton.Yes)
    ws = loaded.workspace.current_workspace

    loaded._on_file_delete(STYLES)

    assert not (ws / STYLES).exists()
    assert loaded.file_tree._items_map[STYLES].text(3) == "D"

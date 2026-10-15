"""Tests for XmlEditorWidget (load/save, search, formatting, zoom)."""

from pathlib import Path

import pytest
from PySide6.QtGui import QTextCursor

from office_raw_editor.ui.xml_editor import CodeEditor, XmlEditorWidget

SAMPLE_XML = '<?xml version="1.0"?><root><a x="1">foo</a><b>foo bar foo</b></root>'


@pytest.fixture
def xml_file(tmp_path) -> Path:
    path = tmp_path / "sample.xml"
    path.write_text(SAMPLE_XML, encoding="utf-8")
    return path


@pytest.fixture
def editor(qtbot) -> XmlEditorWidget:
    widget = XmlEditorWidget()
    qtbot.addWidget(widget)
    return widget


@pytest.fixture
def loaded(editor, xml_file) -> XmlEditorWidget:
    assert editor.load_file(xml_file)
    return editor


def test_load_file_populates_editor(loaded, xml_file):
    assert loaded.editor.toPlainText() == SAMPLE_XML
    assert loaded.get_current_file() == xml_file
    assert loaded.file_label.text() == "sample.xml"
    assert not loaded.has_unsaved_changes()
    assert not loaded.btn_save.isEnabled()
    assert loaded.editor.textCursor().position() == 0


def test_load_missing_file_returns_false(editor, tmp_path):
    assert not editor.load_file(tmp_path / "missing.xml")
    assert editor.get_current_file() is None


def test_load_file_falls_back_to_cp932(editor, tmp_path):
    path = tmp_path / "sjis.xml"
    path.write_bytes("<r>日本語</r>".encode("cp932"))
    assert editor.load_file(path)
    assert "日本語" in editor.editor.toPlainText()


def test_editing_marks_modified_and_emits_signal(loaded, qtbot):
    with qtbot.waitSignal(loaded.content_modified, timeout=1000):
        loaded.editor.appendPlainText("<!-- more -->")

    assert loaded.has_unsaved_changes()
    assert loaded.file_label.text().endswith("[M]")
    assert loaded.btn_save.isEnabled()


def test_reverting_text_clears_modified_flag(loaded):
    loaded.editor.setPlainText(SAMPLE_XML + "x")
    assert loaded.has_unsaved_changes()
    loaded.editor.setPlainText(SAMPLE_XML)
    assert not loaded.has_unsaved_changes()


def test_save_file_writes_utf8_and_emits_path(loaded, xml_file, qtbot):
    loaded.editor.setPlainText("<root>保存</root>")

    with qtbot.waitSignal(loaded.file_saved, timeout=1000) as blocker:
        assert loaded.save_file()

    assert blocker.args == [str(xml_file)]
    assert xml_file.read_text(encoding="utf-8") == "<root>保存</root>"
    assert not loaded.has_unsaved_changes()
    assert not loaded.btn_save.isEnabled()


def test_save_without_file_returns_false(editor):
    assert not editor.save_file()


def test_search_counts_and_cycles_through_matches(loaded):
    loaded.show_search_bar()
    loaded.search_input.setText("foo")

    assert len(loaded._search_matches) == 3
    assert loaded.search_result_label.text() == "1/3 件"
    assert loaded.editor.textCursor().selectedText() == "foo"
    first = loaded.editor.textCursor().selectionStart()

    loaded.find_next()
    assert loaded.search_result_label.text() == "2/3 件"
    assert loaded.editor.textCursor().selectionStart() > first

    loaded.find_next()
    assert loaded.search_result_label.text() == "3/3 件"

    loaded.find_next()  # wraps
    assert loaded.search_result_label.text() == "1/3 件"
    assert loaded.editor.textCursor().selectionStart() == first


def test_find_previous_wraps_to_last_match(loaded):
    loaded.show_search_bar()
    loaded.search_input.setText("foo")
    assert loaded.search_result_label.text() == "1/3 件"

    loaded.find_previous()
    assert loaded.search_result_label.text() == "3/3 件"

    loaded.find_previous()
    assert loaded.search_result_label.text() == "2/3 件"


def test_search_starts_from_cursor_position(loaded):
    cursor = loaded.editor.textCursor()
    cursor.setPosition(SAMPLE_XML.index("<b>"))
    loaded.editor.setTextCursor(cursor)

    loaded.search_input.setText("foo")

    # The first two "foo" occurrences are before the cursor, so we land on the 3rd... no: 2nd is inside <b>
    assert loaded.editor.textCursor().selectionStart() >= SAMPLE_XML.index("<b>")
    assert loaded.search_result_label.text() == "2/3 件"


def test_search_with_no_hits(loaded):
    loaded.search_input.setText("zzz")
    assert loaded.search_result_label.text() == "0 件"
    assert loaded._search_matches == []


def test_editing_invalidates_search_matches(loaded):
    loaded.search_input.setText("foo")
    assert loaded._search_matches
    loaded.editor.appendPlainText("x")
    assert loaded._search_matches == []


def test_toggle_and_hide_search_bar(loaded):
    assert not loaded.search_bar.isVisible()
    loaded.toggle_search_bar()
    assert loaded.search_bar.isVisibleTo(loaded)
    loaded.toggle_search_bar()
    assert not loaded.search_bar.isVisibleTo(loaded)


def test_format_xml_pretty_prints_and_keeps_declaration(loaded):
    loaded.format_xml()

    text = loaded.editor.toPlainText()
    lines = text.splitlines()
    assert lines[0].startswith("<?xml")
    assert '  <a x="1">foo</a>' in lines
    assert text.count("\n") >= 4
    assert loaded.has_unsaved_changes()


def test_format_xml_without_declaration_adds_none(editor, tmp_path):
    path = tmp_path / "nodecl.xml"
    path.write_text("<r><c/></r>", encoding="utf-8")
    editor.load_file(path)

    editor.format_xml()

    assert editor.editor.toPlainText().splitlines() == ["<r>", "  <c/>", "</r>"]


def test_format_invalid_xml_shows_warning_and_keeps_text(loaded, monkeypatch):
    from PySide6.QtWidgets import QMessageBox

    calls = []
    monkeypatch.setattr(QMessageBox, "warning", lambda *a, **k: calls.append(a))
    loaded.editor.setPlainText("<broken>")

    loaded.format_xml()

    assert len(calls) == 1
    assert loaded.editor.toPlainText() == "<broken>"


def test_large_file_disables_highlighting(editor, tmp_path):
    path = tmp_path / "big.xml"
    path.write_text("<r>\n" + "<x/>\n" * 30000 + "</r>", encoding="utf-8")

    editor.load_file(path)

    assert not editor.btn_highlight.isChecked()
    assert not editor.highlighter._enabled


def test_zoom_changes_font_size_and_label(loaded):
    default = CodeEditor.DEFAULT_FONT_SIZE
    assert loaded.zoom_label.text() == "100%"

    loaded._zoom_in()
    assert loaded.editor.get_font_size() == default + 1

    loaded._zoom_reset()
    assert loaded.editor.get_font_size() == default
    assert loaded.zoom_label.text() == "100%"

    for _ in range(100):
        loaded._zoom_out()
    assert loaded.editor.get_font_size() == CodeEditor.MIN_FONT_SIZE


def test_cursor_position_label(loaded):
    cursor = loaded.editor.textCursor()
    cursor.movePosition(QTextCursor.MoveOperation.End)
    loaded.editor.setTextCursor(cursor)
    assert loaded.line_col_label.text() == f"行: 1, 列: {len(SAMPLE_XML) + 1}"


def test_clear_resets_state(loaded):
    loaded.editor.setPlainText("changed")
    loaded.clear()
    assert loaded.get_current_file() is None
    assert loaded.editor.toPlainText() == ""
    assert not loaded.has_unsaved_changes()
    assert not loaded.btn_save.isEnabled()


def test_confirm_discard_is_true_when_clean(loaded):
    assert loaded.confirm_discard_changes()

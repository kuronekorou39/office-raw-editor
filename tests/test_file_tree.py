"""Tests for FileTreeWidget."""

from pathlib import Path

import pytest
from PySide6.QtCore import Qt

from office_raw_editor.ui.file_tree import FileTreeWidget

DOC = str(Path("word") / "document.xml")
STYLES = str(Path("word") / "styles.xml")
IMAGE = str(Path("word") / "media" / "image1.png")
RELS = str(Path("word") / "_rels" / "document.xml.rels")


@pytest.fixture
def tree(qtbot, open_workspace):
    widget = FileTreeWidget()
    qtbot.addWidget(widget)
    widget.load_workspace(open_workspace.current_workspace)
    return widget


def test_load_workspace_builds_items_for_every_path(tree):
    items = tree._items_map
    assert {"[Content_Types].xml", "_rels", "word", DOC, STYLES, IMAGE, RELS} <= set(items)

    assert items["word"].text(2) == "Folder"
    assert items["word"].text(1) == ""
    assert items[DOC].text(2) == "XML File"
    assert items[RELS].text(2) == "Relationships"
    assert items[IMAGE].text(2) == "PNG Image"
    assert items[DOC].text(1).endswith("B")
    # Children hang off their parent folder
    assert items[DOC].parent() is items["word"]
    assert items["word"].parent() is None


def test_main_content_file_is_bold_with_tooltip(tree):
    assert tree._items_map[DOC].font(0).bold()
    assert tree._items_map[DOC].toolTip(0) == "メインコンテンツファイル"
    assert not tree._items_map[STYLES].font(0).bold()


def test_item_user_role_holds_relative_path(tree):
    assert tree._items_map[DOC].data(0, Qt.ItemDataRole.UserRole) == DOC


def test_statuses_are_shown_in_status_column(tree):
    tree.update_file_statuses({DOC: "M", STYLES: "A"})

    assert tree._items_map[DOC].text(3) == "M"
    assert tree._items_map[STYLES].text(3) == "A"
    assert tree._items_map[RELS].text(3) == ""
    assert tree._items_map[DOC].foreground(3).color().name().upper() == FileTreeWidget.STATUS_COLORS["M"].upper()


def test_deleted_file_is_listed_with_strikeout(tree, open_workspace):
    ws = open_workspace.current_workspace
    (ws / STYLES).unlink()

    tree.update_file_statuses({STYLES: "D"})

    item = tree._items_map[STYLES]
    assert item.text(3) == "D"
    assert item.font(0).strikeOut()
    assert item.text(1) == "0 B"


def test_clearing_status_restores_default_look(tree):
    tree.update_file_statuses({DOC: "M"})
    tree.update_file_statuses({})
    assert tree._items_map[DOC].text(3) == ""
    assert not tree._items_map[DOC].font(0).strikeOut()


def test_search_highlights_matches_and_shows_hit_count(tree):
    size_text = tree._items_map[DOC].text(1)

    tree.apply_search({DOC}, filter_active=False, match_counts={DOC: 3})

    assert tree._items_map[DOC].text(1) == f"{size_text}  (3件)"
    assert tree._items_map[DOC].background(0).color().name().upper() == FileTreeWidget.SEARCH_HIGHLIGHT_COLOR
    assert tree._items_map[STYLES].text(1) == tree._items_map[STYLES].data(1, FileTreeWidget.SIZE_TEXT_ROLE)
    assert not tree._items_map[STYLES].isHidden()


def test_repeated_search_does_not_stack_hit_counts(tree):
    size_text = tree._items_map[DOC].text(1)
    tree.apply_search({DOC}, False, {DOC: 3})
    tree.apply_search({DOC}, False, {DOC: 5})
    assert tree._items_map[DOC].text(1) == f"{size_text}  (5件)"


def test_filter_hides_non_matches_but_keeps_ancestors(tree):
    tree.apply_search({DOC}, filter_active=True, match_counts={DOC: 1})

    assert not tree._items_map[DOC].isHidden()
    assert not tree._items_map["word"].isHidden()
    assert tree._items_map[STYLES].isHidden()
    assert tree._items_map["_rels"].isHidden()
    assert tree._items_map["[Content_Types].xml"].isHidden()


def test_clear_search_restores_everything(tree):
    size_text = tree._items_map[DOC].text(1)
    tree.apply_search({DOC}, True, {DOC: 2})

    tree.clear_search()

    assert all(not item.isHidden() for item in tree._items_map.values())
    assert tree._items_map[DOC].text(1) == size_text
    assert tree._items_map[DOC].background(0).style() == Qt.BrushStyle.NoBrush


def test_search_state_survives_refresh(tree):
    tree.apply_search({DOC}, True, {DOC: 2})
    tree.refresh()
    assert tree._items_map[STYLES].isHidden()
    assert tree._items_map[DOC].text(1).endswith("(2件)")


def test_double_click_on_file_emits_relative_path(tree, qtbot):
    with qtbot.waitSignal(tree.file_double_clicked, timeout=1000) as blocker:
        tree._on_item_double_clicked(tree._items_map[DOC], 0)
    assert blocker.args == [DOC]


def test_double_click_on_folder_emits_nothing(tree, qtbot):
    with qtbot.assertNotEmitted(tree.file_double_clicked):
        tree._on_item_double_clicked(tree._items_map["word"], 0)


def test_selection_helpers(tree, open_workspace):
    assert tree.get_selected_path() is None
    assert tree.get_selected_absolute_path() is None

    tree.setCurrentItem(tree._items_map[DOC])

    assert tree.get_selected_path() == DOC
    assert tree.get_selected_absolute_path() == open_workspace.current_workspace / DOC


def test_clear_workspace_empties_tree(tree):
    tree.clear_workspace()
    assert tree.topLevelItemCount() == 0
    assert tree._items_map == {}
    assert tree.get_selected_path() is None

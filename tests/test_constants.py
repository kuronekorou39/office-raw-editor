"""Tests for pure helpers in utils.constants."""

import pytest

from office_raw_editor.utils.constants import format_file_size, is_main_content_file


@pytest.mark.parametrize("size, expected", [
    (0, "0 B"),
    (1023, "1023 B"),
    (1024, "1.0 KB"),
    (1536, "1.5 KB"),
    (1024 * 1024, "1.0 MB"),
    (int(2.5 * 1024 * 1024), "2.5 MB"),
])
def test_format_file_size(size, expected):
    assert format_file_size(size) == expected


@pytest.mark.parametrize("rel_path", [
    "word/document.xml",
    "word\\document.xml",
    "WORD/DOCUMENT.XML",
    "word/document2.xml",
    "xl/workbook.xml",
    "xl/worksheets/sheet12.xml",
    "ppt/presentation.xml",
    "ppt/slides/slide3.xml",
])
def test_is_main_content_file_true(rel_path):
    assert is_main_content_file(rel_path)


@pytest.mark.parametrize("rel_path", [
    "word/styles.xml",
    "word/_rels/document.xml.rels",
    "xl/sharedStrings.xml",
    "xl/worksheets/_rels/sheet1.xml.rels",
    "ppt/slideLayouts/slideLayout1.xml",
    "[Content_Types].xml",
    "other/word/document.xml",
])
def test_is_main_content_file_false(rel_path):
    assert not is_main_content_file(rel_path)

"""Tests for OfficeFileHandler (ZIP extraction / repackaging)."""

import zipfile
from pathlib import Path

import pytest

from office_raw_editor.core.docx_handler import OfficeFileHandler
from tests.conftest import PNG_BYTES, make_office_file


@pytest.mark.parametrize("name", [
    "a.docx", "a.docm", "a.dotx", "a.dotm",
    "a.xlsx", "a.xlsm", "a.xltx", "a.xltm",
    "a.pptx", "a.pptm", "a.potx", "a.potm", "a.ppsx", "a.ppsm",
    "UPPER.DOCX",
])
def test_is_supported_extension(name):
    assert OfficeFileHandler.is_supported_extension(Path(name))


@pytest.mark.parametrize("name", ["a.doc", "a.xls", "a.zip", "a.txt", "noext"])
def test_is_supported_extension_rejects_others(name):
    assert not OfficeFileHandler.is_supported_extension(Path(name))


def test_is_valid_file_accepts_minimal_package(sample_docx, sample_xlsx):
    assert OfficeFileHandler.is_valid_file(sample_docx)
    assert OfficeFileHandler.is_valid_file(sample_xlsx)


def test_is_valid_file_rejects_missing_file(tmp_path):
    assert not OfficeFileHandler.is_valid_file(tmp_path / "nope.docx")


def test_is_valid_file_rejects_non_zip(tmp_path):
    bogus = tmp_path / "bogus.docx"
    bogus.write_text("this is not a zip")
    assert not OfficeFileHandler.is_valid_file(bogus)


def test_is_valid_file_rejects_zip_without_content_types(tmp_path):
    path = make_office_file(tmp_path / "plain.docx", {"word/document.xml": "<w/>"})
    assert not OfficeFileHandler.is_valid_file(path)


def test_is_valid_file_rejects_unsupported_extension(tmp_path):
    path = make_office_file(tmp_path / "archive.zip")
    assert not OfficeFileHandler.is_valid_file(path)


def test_extract_preserves_structure(sample_docx, tmp_path):
    out = tmp_path / "out"
    assert OfficeFileHandler.extract(sample_docx, out)

    assert (out / "[Content_Types].xml").is_file()
    assert (out / "word" / "document.xml").is_file()
    assert (out / "word" / "_rels" / "document.xml.rels").is_file()
    assert (out / "word" / "media" / "image1.png").read_bytes() == PNG_BYTES


def test_extract_missing_file_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        OfficeFileHandler.extract(tmp_path / "missing.docx", tmp_path / "out")


def test_repackage_round_trip(sample_docx, tmp_path):
    out_dir = tmp_path / "out"
    OfficeFileHandler.extract(sample_docx, out_dir)

    # Edit one member and add another
    doc = out_dir / "word" / "document.xml"
    doc.write_text(doc.read_text(encoding="utf-8").replace("Hello", "Bye"), encoding="utf-8")
    (out_dir / "customXml").mkdir()
    (out_dir / "customXml" / "item1.xml").write_text("<item/>", encoding="utf-8")

    result = tmp_path / "nested" / "result.docx"
    assert OfficeFileHandler.repackage(out_dir, result)

    with zipfile.ZipFile(result) as zf:
        names = set(zf.namelist())
        # Archive member names must use forward slashes regardless of OS
        assert all("\\" not in n for n in names)
        assert {"[Content_Types].xml", "word/document.xml", "customXml/item1.xml"} <= names
        assert b"Bye" in zf.read("word/document.xml")
        assert zf.read("word/media/image1.png") == PNG_BYTES

    assert OfficeFileHandler.is_valid_file(result)


def test_repackage_requires_content_types(tmp_path):
    src = tmp_path / "src"
    (src / "word").mkdir(parents=True)
    (src / "word" / "document.xml").write_text("<w/>")
    with pytest.raises(ValueError):
        OfficeFileHandler.repackage(src, tmp_path / "out.docx")


def test_repackage_missing_dir_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        OfficeFileHandler.repackage(tmp_path / "missing", tmp_path / "out.docx")


def test_get_file_list_and_read_file(sample_docx):
    names = OfficeFileHandler.get_file_list(sample_docx)
    assert "word/document.xml" in names
    assert b"{{placeholder}}" in OfficeFileHandler.read_file(sample_docx, "word/document.xml")
    with pytest.raises(KeyError):
        OfficeFileHandler.read_file(sample_docx, "word/missing.xml")

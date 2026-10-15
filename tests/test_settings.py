"""Tests for the QSettings-backed Settings wrapper (isolated to tmp_path by conftest)."""

from office_raw_editor.utils.settings import Settings, get_settings


def test_defaults_are_empty():
    settings = Settings()
    assert settings.get_external_editor() == ""
    assert settings.get_use_external_editor() is False
    assert settings.get_last_open_dir() == ""
    assert settings.get_last_save_dir() == ""


def test_values_round_trip_through_storage():
    settings = Settings()
    settings.set_external_editor(r"C:\Tools\editor.exe")
    settings.set_use_external_editor(True)
    settings.set_last_open_dir(r"C:\docs")
    settings.set_last_save_dir(r"C:\out")
    settings.sync()

    reloaded = Settings()
    assert reloaded.get_external_editor() == r"C:\Tools\editor.exe"
    assert reloaded.get_use_external_editor() is True
    assert reloaded.get_last_open_dir() == r"C:\docs"
    assert reloaded.get_last_save_dir() == r"C:\out"


def test_get_settings_returns_singleton():
    assert get_settings() is get_settings()

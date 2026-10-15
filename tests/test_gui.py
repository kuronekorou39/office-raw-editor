"""Tests for the console-less launcher (office_raw_editor.gui)."""

import sys

import pytest

from office_raw_editor import gui


def test_ensure_streams_replaces_missing_stdio(monkeypatch):
    monkeypatch.setattr(sys, "stdout", None)
    monkeypatch.setattr(sys, "stderr", None)

    gui._ensure_streams()

    print("must not raise")
    assert sys.stdout is not None and sys.stderr is not None


def test_ensure_streams_keeps_existing_stdio():
    before = sys.stdout
    gui._ensure_streams()
    assert sys.stdout is before


def test_crash_is_written_to_log_and_reported(tmp_path, monkeypatch):
    log = tmp_path / "startup-error.log"
    monkeypatch.setattr(gui, "ERROR_LOG", log)
    boxes = []
    if sys.platform == "win32":
        import ctypes
        monkeypatch.setattr(ctypes.windll.user32, "MessageBoxW", lambda *a: boxes.append(a))

    def boom():
        raise RuntimeError("no display")

    monkeypatch.setattr(gui, "_ensure_streams", lambda: None)
    monkeypatch.setitem(sys.modules, "office_raw_editor.app", type(sys)("office_raw_editor.app"))
    sys.modules["office_raw_editor.app"].OfficeRawEditorApp = boom

    assert gui.main() == 1

    assert "RuntimeError: no display" in log.read_text(encoding="utf-8")
    if sys.platform == "win32":
        assert len(boxes) == 1
        assert str(log) in boxes[0][1]  # (hwnd, text, title, flags)


def test_main_returns_app_exit_code(monkeypatch):
    class FakeApp:
        def run(self):
            return 0

    monkeypatch.setitem(sys.modules, "office_raw_editor.app", type(sys)("office_raw_editor.app"))
    sys.modules["office_raw_editor.app"].OfficeRawEditorApp = FakeApp
    assert gui.main() == 0

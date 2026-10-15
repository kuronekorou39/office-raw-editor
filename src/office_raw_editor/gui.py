"""ダブルクリックで画面を開く起点。コンソール無しの exe が使う。

`python -m office_raw_editor.gui [ファイル]` は `python -m office_raw_editor [ファイル]` と同じ。
"""

import os
import sys
import traceback
from pathlib import Path

from .utils.constants import APP_NAME

ERROR_LOG = Path.home() / f".{APP_NAME}" / "startup-error.log"
"""コンソール無しの exe が起動に失敗したときの行き先。表示する場所が他に無い。"""


def _ensure_streams() -> None:
    """コンソール無しの exe では標準出力・標準エラーが None になる。

    そのままだとライブラリがエラーを書いた時点で AttributeError になるので、捨て先を用意する。
    """
    for name in ("stdout", "stderr"):
        if getattr(sys, name) is None:
            setattr(sys, name, open(os.devnull, "w", encoding="utf-8"))


def _report_crash(text: str) -> None:
    """ログに残し、Qt に頼らずメッセージボックスで場所を知らせる。"""
    try:
        ERROR_LOG.parent.mkdir(parents=True, exist_ok=True)
        ERROR_LOG.write_text(text, encoding="utf-8")
    except OSError:
        pass
    if sys.platform == "win32":
        import ctypes

        ctypes.windll.user32.MessageBoxW(
            None, f"起動できませんでした。\n{ERROR_LOG}", APP_NAME, 0x10
        )


def main() -> int:
    _ensure_streams()
    try:
        from .app import OfficeRawEditorApp

        return OfficeRawEditorApp().run()
    except SystemExit:
        raise
    except BaseException:  # 何が起きても黙って消えない
        _report_crash(traceback.format_exc())
        return 1


if __name__ == "__main__":
    sys.exit(main())

# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller の設定。`scripts/build_exe.ps1` から使う。

dist/office-raw-editor/office-raw-editor.exe(画面。コンソール無し)を出す。
onefile にはしない。起動が速く、ウイルス対策にも引っかかりにくいため。
版は src/office_raw_editor/__init__.py の __version__ から取る。
"""
import re
from pathlib import Path

from PyInstaller.utils.win32.versioninfo import (
    FixedFileInfo,
    StringFileInfo,
    StringStruct,
    StringTable,
    VarFileInfo,
    VarStruct,
    VSVersionInfo,
)

APP_NAME = "office-raw-editor"
PACKAGE = Path("src") / "office_raw_editor"
ICON = str(PACKAGE / "ui" / "assets" / "app.ico")
DATAS = [(str(PACKAGE / "ui" / "assets"), "office_raw_editor/ui/assets")]
# 使っていない Qt モジュール。import されたぶんしか入らないが、名指しで外して確実にする
EXCLUDES = [
    "tkinter",
    "pytest",
    "_pytest",
    "PySide6.QtQuick",
    "PySide6.QtQml",
    "PySide6.QtPdf",
    "PySide6.QtNetwork",
    "PySide6.QtOpenGL",
    "PySide6.QtWebEngineCore",
    "PySide6.QtWebEngineWidgets",
    "PySide6.QtMultimedia",
    "PySide6.QtCharts",
    "PySide6.Qt3DCore",
]

VERSION = re.search(
    r'__version__\s*=\s*"([^"]+)"', (PACKAGE / "__init__.py").read_text(encoding="utf-8")
).group(1)


def version_info(version):
    """exe のプロパティの「詳細」に出る版(0.2.0 → 0.2.0.0)。"""
    numbers = tuple(int(part) for part in version.split(".")) + (0,)
    strings = [
        StringStruct("FileDescription", "office-raw-editor"),
        StringStruct("FileVersion", version),
        StringStruct("InternalName", APP_NAME),
        StringStruct("LegalCopyright", "MIT License"),
        StringStruct("OriginalFilename", f"{APP_NAME}.exe"),
        StringStruct("ProductName", "office-raw-editor"),
        StringStruct("ProductVersion", version),
    ]
    return VSVersionInfo(
        ffi=FixedFileInfo(filevers=numbers, prodvers=numbers, mask=0x3F, flags=0x0, OS=0x40004,
                          fileType=0x1, subtype=0x0, date=(0, 0)),
        kids=[
            StringFileInfo([StringTable("041104B0", strings)]),  # 日本語・Unicode
            VarFileInfo([VarStruct("Translation", [0x0411, 1200])]),
        ],
    )


a = Analysis(
    ["scripts/run_gui.py"],
    pathex=["src"],
    datas=DATAS,
    hiddenimports=[],
    excludes=EXCLUDES,
    noarchive=False,
)

exe = EXE(
    PYZ(a.pure),
    a.scripts,
    [],
    exclude_binaries=True,
    name=APP_NAME,
    icon=ICON,
    version=version_info(VERSION),
    console=False,
    upx=False,
)

COLLECT(exe, a.binaries, a.datas, name=APP_NAME, upx=False)

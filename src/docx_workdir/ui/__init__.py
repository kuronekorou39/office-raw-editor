"""UI components for docx-workdir."""

from .main_window import MainWindow
from .file_tree import FileTreeWidget
from .dialogs import ConfirmDialog, ErrorDialog
from .xml_editor import XmlEditorWidget
from .settings_dialog import SettingsDialog

__all__ = [
    "MainWindow",
    "FileTreeWidget",
    "ConfirmDialog",
    "ErrorDialog",
    "XmlEditorWidget",
    "SettingsDialog",
]

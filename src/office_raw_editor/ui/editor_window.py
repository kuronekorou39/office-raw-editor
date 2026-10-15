"""Separate editor window with tabbed interface for editing multiple files."""

from pathlib import Path
from typing import Optional

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QCloseEvent, QKeySequence, QShortcut
from PyQt6.QtWidgets import (
    QMainWindow,
    QTabWidget,
    QMessageBox,
    QVBoxLayout,
    QWidget,
)

from .xml_editor import XmlEditorWidget
from .styles import APP_STYLESHEET
from ..utils.constants import APP_NAME


class EditorWindow(QMainWindow):
    """Separate window for editing files with tabs."""

    file_saved = pyqtSignal(str)  # Emits path when a file is saved
    window_closed = pyqtSignal()

    _instance: Optional['EditorWindow'] = None

    @classmethod
    def get_instance(cls) -> 'EditorWindow':
        """Get or create the singleton editor window instance."""
        if cls._instance is None or not cls._instance.isVisible():
            cls._instance = EditorWindow()
        return cls._instance

    def __init__(self, parent=None):
        super().__init__(parent)
        self._editors: dict[str, XmlEditorWidget] = {}  # path -> editor
        self._setup_ui()
        self._setup_shortcuts()

    def _setup_ui(self):
        """Set up the window UI."""
        self.setWindowTitle(f"エディタ - {APP_NAME}")
        self.setMinimumSize(600, 400)
        self.resize(900, 700)

        # Apply stylesheet
        self.setStyleSheet(APP_STYLESHEET)

        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(4, 4, 4, 4)

        # Tab widget for multiple files
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.setMovable(True)
        self.tab_widget.setDocumentMode(True)
        self.tab_widget.tabCloseRequested.connect(self._on_tab_close_requested)
        layout.addWidget(self.tab_widget)

    def _setup_shortcuts(self):
        """Set up keyboard shortcuts."""
        # Close tab with Ctrl+W
        close_tab_shortcut = QShortcut(QKeySequence("Ctrl+W"), self)
        close_tab_shortcut.activated.connect(self._close_current_tab)

    def open_file(self, file_path: Path) -> bool:
        """Open a file in a new tab or focus existing tab.

        Args:
            file_path: Path to the file to open.

        Returns:
            True if file was opened successfully.
        """
        path_str = str(file_path)

        # Check if file is already open
        if path_str in self._editors:
            # Focus the existing tab
            editor = self._editors[path_str]
            index = self.tab_widget.indexOf(editor)
            if index >= 0:
                self.tab_widget.setCurrentIndex(index)
                self.show()
                self.raise_()
                self.activateWindow()
                return True

        # Create new editor tab
        editor = XmlEditorWidget()
        if not editor.load_file(file_path):
            QMessageBox.warning(
                self,
                "エラー",
                f"ファイルを開けませんでした:\n{file_path.name}"
            )
            return False

        # Connect signals
        editor.file_saved.connect(self._on_file_saved)
        editor.content_modified.connect(lambda: self._update_tab_title(path_str))

        # Add tab
        self._editors[path_str] = editor
        index = self.tab_widget.addTab(editor, file_path.name)
        self.tab_widget.setCurrentIndex(index)
        self.tab_widget.setTabToolTip(index, path_str)

        # Show window
        self.show()
        self.raise_()
        self.activateWindow()

        return True

    def _on_file_saved(self, file_path: str):
        """Handle file saved in an editor."""
        self._update_tab_title(file_path)
        self.file_saved.emit(file_path)

    def _update_tab_title(self, file_path: str):
        """Update tab title to show modified state."""
        if file_path not in self._editors:
            return

        editor = self._editors[file_path]
        index = self.tab_widget.indexOf(editor)
        if index < 0:
            return

        name = Path(file_path).name
        if editor.has_unsaved_changes():
            self.tab_widget.setTabText(index, f"● {name}")
        else:
            self.tab_widget.setTabText(index, name)

    def _on_tab_close_requested(self, index: int):
        """Handle tab close request."""
        editor = self.tab_widget.widget(index)
        if not isinstance(editor, XmlEditorWidget):
            return

        # Find the path for this editor
        path_str = None
        for path, ed in self._editors.items():
            if ed is editor:
                path_str = path
                break

        if path_str is None:
            return

        # Check for unsaved changes
        if editor.has_unsaved_changes():
            if not editor.confirm_discard_changes():
                return

        # Remove tab and editor
        self.tab_widget.removeTab(index)
        del self._editors[path_str]

        # Close window if no tabs left
        if self.tab_widget.count() == 0:
            self.close()

    def _close_current_tab(self):
        """Close the current tab."""
        index = self.tab_widget.currentIndex()
        if index >= 0:
            self._on_tab_close_requested(index)

    def has_unsaved_changes(self) -> bool:
        """Check if any editor has unsaved changes."""
        for editor in self._editors.values():
            if editor.has_unsaved_changes():
                return True
        return False

    def get_unsaved_files(self) -> list[str]:
        """Get list of files with unsaved changes."""
        unsaved = []
        for path, editor in self._editors.items():
            if editor.has_unsaved_changes():
                unsaved.append(path)
        return unsaved

    def save_all(self) -> bool:
        """Save all open files.

        Returns:
            True if all files were saved successfully.
        """
        success = True
        for editor in self._editors.values():
            if editor.has_unsaved_changes():
                if not editor.save_file():
                    success = False
        return success

    def closeEvent(self, event: QCloseEvent):
        """Handle window close event."""
        # Check for unsaved changes
        unsaved = self.get_unsaved_files()
        if unsaved:
            result = QMessageBox.question(
                self,
                "未保存の変更",
                f"{len(unsaved)}個のファイルに未保存の変更があります。\n\n"
                "保存せずに閉じますか？",
                QMessageBox.StandardButton.Save |
                QMessageBox.StandardButton.Discard |
                QMessageBox.StandardButton.Cancel,
                QMessageBox.StandardButton.Cancel,
            )

            if result == QMessageBox.StandardButton.Save:
                if not self.save_all():
                    event.ignore()
                    return
            elif result == QMessageBox.StandardButton.Cancel:
                event.ignore()
                return

        # Clear editors
        self._editors.clear()
        self.tab_widget.clear()

        self.window_closed.emit()
        event.accept()

    def is_file_open(self, file_path: Path) -> bool:
        """Check if a file is currently open."""
        return str(file_path) in self._editors

    def focus_file(self, file_path: Path):
        """Focus the tab for a specific file if open."""
        path_str = str(file_path)
        if path_str in self._editors:
            editor = self._editors[path_str]
            index = self.tab_widget.indexOf(editor)
            if index >= 0:
                self.tab_widget.setCurrentIndex(index)
                self.show()
                self.raise_()
                self.activateWindow()

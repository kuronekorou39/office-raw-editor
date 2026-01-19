"""Main window for docx-workdir application."""

import os
import subprocess
import sys
from pathlib import Path
from typing import Optional

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QAction, QKeySequence, QCloseEvent
from PyQt6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QToolBar,
    QStatusBar,
    QLabel,
    QPushButton,
    QSplitter,
    QTabWidget,
)

from ..core.workspace import WorkspaceManager
from ..utils.constants import (
    APP_TITLE,
    DEFAULT_WINDOW_WIDTH,
    DEFAULT_WINDOW_HEIGHT,
    MIN_WINDOW_WIDTH,
    MIN_WINDOW_HEIGHT,
    DIALOG_TITLE_ERROR,
    MSG_ERROR_OPEN,
    MSG_ERROR_SAVE,
    MSG_EXTRACT_SUCCESS,
    MSG_REPACKAGE_SUCCESS,
)
from ..utils.settings import get_settings
from .file_tree import FileTreeWidget
from .xml_editor import XmlEditorWidget
from .dialogs import ConfirmDialog, ErrorDialog, FileDialogs
from .settings_dialog import SettingsDialog


class MainWindow(QMainWindow):
    """Main application window."""

    def __init__(self):
        """Initialize the main window."""
        super().__init__()
        self.workspace = WorkspaceManager()
        self.settings = get_settings()
        self._modification_timer: Optional[QTimer] = None

        self._setup_ui()
        self._create_menus()
        self._create_toolbar()
        self._create_status_bar()
        self._connect_signals()
        self._start_modification_check()

        self._update_window_title()
        self._update_ui_state()

    def _setup_ui(self):
        """Set up the main UI components."""
        self.setWindowTitle(APP_TITLE)
        self.setMinimumSize(MIN_WINDOW_WIDTH, MIN_WINDOW_HEIGHT)
        self.resize(DEFAULT_WINDOW_WIDTH, DEFAULT_WINDOW_HEIGHT)

        # Central widget
        central = QWidget()
        self.setCentralWidget(central)

        # Main layout
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)

        # Splitter for tree and editor panel
        self.splitter = QSplitter(Qt.Orientation.Horizontal)

        # File tree
        self.file_tree = FileTreeWidget()
        self.splitter.addWidget(self.file_tree)

        # Right panel with tabs (editor + info)
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)

        # Tab widget for editor and file info
        self.tab_widget = QTabWidget()

        # XML Editor tab
        self.xml_editor = XmlEditorWidget()
        self.tab_widget.addTab(self.xml_editor, "エディタ")

        # File info tab
        info_widget = QWidget()
        info_layout = QVBoxLayout(info_widget)
        self.info_label = QLabel("ファイルを選択してください")
        self.info_label.setWordWrap(True)
        info_layout.addWidget(self.info_label)

        from PyQt6.QtWidgets import QTextEdit
        self.info_text = QTextEdit()
        self.info_text.setReadOnly(True)
        self.info_text.setPlaceholderText("ファイル情報がここに表示されます")
        info_layout.addWidget(self.info_text)
        self.tab_widget.addTab(info_widget, "ファイル情報")

        right_layout.addWidget(self.tab_widget)
        self.splitter.addWidget(right_panel)

        # Set splitter sizes
        self.splitter.setSizes([300, 500])

        layout.addWidget(self.splitter)

    def _create_menus(self):
        """Create menu bar."""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("ファイル(&F)")

        self.action_open = QAction("開く(&O)...", self)
        self.action_open.setShortcut(QKeySequence.StandardKey.Open)
        self.action_open.triggered.connect(self.open_docx)
        file_menu.addAction(self.action_open)

        file_menu.addSeparator()

        self.action_save = QAction("上書き保存(&S)", self)
        self.action_save.setShortcut(QKeySequence.StandardKey.Save)
        self.action_save.triggered.connect(self.save_docx)
        file_menu.addAction(self.action_save)

        self.action_save_as = QAction("名前を付けて保存(&A)...", self)
        self.action_save_as.setShortcut(QKeySequence("Ctrl+Shift+S"))
        self.action_save_as.triggered.connect(self.save_docx_as)
        file_menu.addAction(self.action_save_as)

        file_menu.addSeparator()

        self.action_close = QAction("閉じる(&C)", self)
        self.action_close.setShortcut(QKeySequence.StandardKey.Close)
        self.action_close.triggered.connect(self.close_workspace)
        file_menu.addAction(self.action_close)

        file_menu.addSeparator()

        self.action_exit = QAction("終了(&X)", self)
        self.action_exit.setShortcut(QKeySequence.StandardKey.Quit)
        self.action_exit.triggered.connect(self.close)
        file_menu.addAction(self.action_exit)

        # Edit menu
        edit_menu = menubar.addMenu("編集(&E)")

        self.action_refresh = QAction("更新(&R)", self)
        self.action_refresh.setShortcut(QKeySequence.StandardKey.Refresh)
        self.action_refresh.triggered.connect(self.refresh_tree)
        edit_menu.addAction(self.action_refresh)

        edit_menu.addSeparator()

        self.action_open_internal = QAction("内蔵エディタで開く(&I)", self)
        self.action_open_internal.setShortcut(QKeySequence("Ctrl+I"))
        self.action_open_internal.triggered.connect(self.open_in_internal_editor)
        edit_menu.addAction(self.action_open_internal)

        self.action_open_external = QAction("外部エディタで開く(&E)", self)
        self.action_open_external.setShortcut(QKeySequence("Ctrl+E"))
        self.action_open_external.triggered.connect(self.open_in_external_editor)
        edit_menu.addAction(self.action_open_external)

        edit_menu.addSeparator()

        self.action_open_folder = QAction("フォルダを開く(&F)", self)
        self.action_open_folder.triggered.connect(self.open_workspace_folder)
        edit_menu.addAction(self.action_open_folder)

        # Tools menu
        tools_menu = menubar.addMenu("ツール(&T)")

        self.action_settings = QAction("設定(&S)...", self)
        self.action_settings.triggered.connect(self.show_settings)
        tools_menu.addAction(self.action_settings)

        # Help menu
        help_menu = menubar.addMenu("ヘルプ(&H)")

        self.action_about = QAction("バージョン情報(&A)", self)
        self.action_about.triggered.connect(self.show_about)
        help_menu.addAction(self.action_about)

    def _create_toolbar(self):
        """Create toolbar."""
        toolbar = QToolBar("Main Toolbar")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        # Open button
        self.btn_open = QPushButton("開く")
        self.btn_open.clicked.connect(self.open_docx)
        toolbar.addWidget(self.btn_open)

        toolbar.addSeparator()

        # Save button
        self.btn_save = QPushButton("保存")
        self.btn_save.clicked.connect(self.save_docx)
        toolbar.addWidget(self.btn_save)

        # Save As button
        self.btn_save_as = QPushButton("名前を付けて保存")
        self.btn_save_as.clicked.connect(self.save_docx_as)
        toolbar.addWidget(self.btn_save_as)

        toolbar.addSeparator()

        # Refresh button
        self.btn_refresh = QPushButton("更新")
        self.btn_refresh.clicked.connect(self.refresh_tree)
        toolbar.addWidget(self.btn_refresh)

        toolbar.addSeparator()

        # Open internal editor button
        self.btn_open_internal = QPushButton("内蔵エディタ")
        self.btn_open_internal.clicked.connect(self.open_in_internal_editor)
        toolbar.addWidget(self.btn_open_internal)

        # Open external button
        self.btn_open_external = QPushButton("外部エディタ")
        self.btn_open_external.clicked.connect(self.open_in_external_editor)
        toolbar.addWidget(self.btn_open_external)

        toolbar.addSeparator()

        # Settings button
        self.btn_settings = QPushButton("設定")
        self.btn_settings.clicked.connect(self.show_settings)
        toolbar.addWidget(self.btn_settings)

    def _create_status_bar(self):
        """Create status bar."""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        self.status_label = QLabel("準備完了")
        self.status_bar.addWidget(self.status_label)

        self.modified_label = QLabel("")
        self.status_bar.addPermanentWidget(self.modified_label)

    def _connect_signals(self):
        """Connect widget signals."""
        self.file_tree.file_double_clicked.connect(self._on_file_double_clicked)
        self.file_tree.itemSelectionChanged.connect(self._on_selection_changed)
        self.xml_editor.file_saved.connect(self._on_editor_file_saved)
        self.xml_editor.content_modified.connect(self._on_editor_content_modified)

    def _start_modification_check(self):
        """Start timer for checking file modifications."""
        self._modification_timer = QTimer(self)
        self._modification_timer.timeout.connect(self._check_modifications)
        self._modification_timer.start(2000)  # Check every 2 seconds

    def _check_modifications(self):
        """Check for modifications in the workspace."""
        if self.workspace.current_workspace:
            was_modified = self.workspace.is_modified
            self.workspace.check_modifications()
            if self.workspace.is_modified != was_modified:
                self._update_ui_state()

    def _update_window_title(self):
        """Update the window title."""
        title = APP_TITLE
        if self.workspace.source_docx:
            title = f"{self.workspace.source_docx.name} - {APP_TITLE}"
            if self.workspace.is_modified or self.xml_editor.has_unsaved_changes():
                title = f"* {title}"
        self.setWindowTitle(title)

    def _update_ui_state(self):
        """Update UI elements based on current state."""
        has_workspace = self.workspace.current_workspace is not None
        has_selection = self.file_tree.get_selected_path() is not None
        selected_is_file = False
        if has_selection:
            abs_path = self.file_tree.get_selected_absolute_path()
            selected_is_file = abs_path and abs_path.is_file()

        # Enable/disable actions
        self.action_save.setEnabled(has_workspace)
        self.action_save_as.setEnabled(has_workspace)
        self.action_close.setEnabled(has_workspace)
        self.action_refresh.setEnabled(has_workspace)
        self.action_open_internal.setEnabled(has_workspace and selected_is_file)
        self.action_open_external.setEnabled(has_workspace and selected_is_file)
        self.action_open_folder.setEnabled(has_workspace)

        # Enable/disable toolbar buttons
        self.btn_save.setEnabled(has_workspace)
        self.btn_save_as.setEnabled(has_workspace)
        self.btn_refresh.setEnabled(has_workspace)
        self.btn_open_internal.setEnabled(has_workspace and selected_is_file)
        self.btn_open_external.setEnabled(has_workspace and selected_is_file)

        # Update modified indicator
        if self.workspace.is_modified or self.xml_editor.has_unsaved_changes():
            self.modified_label.setText("変更あり")
        else:
            self.modified_label.setText("")

        self._update_window_title()

    def _set_status(self, message: str):
        """Update status bar message.

        Args:
            message: Status message to display.
        """
        self.status_label.setText(message)

    def open_docx(self):
        """Open a docx file."""
        if not self._confirm_close_current():
            return

        initial_dir = self.settings.get_last_open_dir()
        file_path = FileDialogs.open_docx(self, initial_dir)
        if not file_path:
            return

        self.settings.set_last_open_dir(str(Path(file_path).parent))
        self._load_docx(Path(file_path))

    def _load_docx(self, docx_path: Path):
        """Load a docx file into the workspace.

        Args:
            docx_path: Path to the docx file.
        """
        try:
            workspace_path = self.workspace.open_docx(docx_path)
            self.file_tree.load_workspace(workspace_path)
            self.xml_editor.clear()
            self._set_status(MSG_EXTRACT_SUCCESS.format(docx_path.name))
            self._update_ui_state()
        except FileNotFoundError as e:
            ErrorDialog.show_error(self, DIALOG_TITLE_ERROR, MSG_ERROR_OPEN.format(str(e)))
        except ValueError as e:
            ErrorDialog.show_error(self, DIALOG_TITLE_ERROR, MSG_ERROR_OPEN.format(str(e)))
        except Exception as e:
            ErrorDialog.show_error(self, DIALOG_TITLE_ERROR, MSG_ERROR_OPEN.format(str(e)))

    def save_docx(self):
        """Save changes to the original docx file."""
        if not self.workspace.current_workspace:
            return

        # First save any changes in the editor
        if self.xml_editor.has_unsaved_changes():
            self.xml_editor.save_file()

        if not self.workspace.source_docx:
            self.save_docx_as()
            return

        try:
            self.workspace.save()
            self._set_status(MSG_REPACKAGE_SUCCESS.format(self.workspace.source_docx.name))
            self._update_ui_state()
        except Exception as e:
            ErrorDialog.show_error(self, DIALOG_TITLE_ERROR, MSG_ERROR_SAVE.format(str(e)))

    def save_docx_as(self):
        """Save changes to a new docx file."""
        if not self.workspace.current_workspace:
            return

        # First save any changes in the editor
        if self.xml_editor.has_unsaved_changes():
            self.xml_editor.save_file()

        initial_dir = self.settings.get_last_save_dir()
        suggested_name = ""
        if self.workspace.source_docx:
            if not initial_dir:
                initial_dir = str(self.workspace.source_docx.parent)
            suggested_name = f"{self.workspace.source_docx.stem}_edited.docx"

        file_path = FileDialogs.save_docx(self, initial_dir, suggested_name)
        if not file_path:
            return

        output_path = Path(file_path)
        self.settings.set_last_save_dir(str(output_path.parent))

        if not output_path.suffix.lower() == ".docx":
            output_path = output_path.with_suffix(".docx")

        # Check for overwrite
        if output_path.exists():
            if not ConfirmDialog.confirm_overwrite(self, str(output_path)):
                return

        try:
            self.workspace.save_as(output_path, overwrite=True)
            self._set_status(MSG_REPACKAGE_SUCCESS.format(output_path.name))
            self._update_ui_state()
        except Exception as e:
            ErrorDialog.show_error(self, DIALOG_TITLE_ERROR, MSG_ERROR_SAVE.format(str(e)))

    def close_workspace(self):
        """Close the current workspace."""
        if not self._confirm_close_current():
            return

        self.workspace.close()
        self.file_tree.clear_workspace()
        self.xml_editor.clear()
        self.info_label.setText("ファイルを選択してください")
        self.info_text.clear()
        self._set_status("準備完了")
        self._update_ui_state()

    def refresh_tree(self):
        """Refresh the file tree."""
        self.file_tree.refresh()
        self._set_status("ツリーを更新しました")

    def open_in_internal_editor(self):
        """Open selected file in the internal editor."""
        abs_path = self.file_tree.get_selected_absolute_path()
        if not abs_path or not abs_path.is_file():
            return

        # Check if there are unsaved changes in current editor
        if not self.xml_editor.confirm_discard_changes():
            return

        if self.xml_editor.load_file(abs_path):
            self.tab_widget.setCurrentIndex(0)  # Switch to editor tab
            self._set_status(f"内蔵エディタで開きました: {abs_path.name}")
        else:
            ErrorDialog.show_error(self, DIALOG_TITLE_ERROR, f"ファイルを開けませんでした: {abs_path.name}")

    def open_in_external_editor(self):
        """Open selected file in external editor."""
        abs_path = self.file_tree.get_selected_absolute_path()
        if not abs_path or not abs_path.is_file():
            return

        self._open_with_external_editor(abs_path)

    def _open_with_external_editor(self, file_path: Path):
        """Open a file with the configured external editor or default app.

        Args:
            file_path: Path to the file to open.
        """
        external_editor = self.settings.get_external_editor()

        try:
            # Expand environment variables and normalize path
            if external_editor:
                external_editor = os.path.expandvars(external_editor)
                external_editor = os.path.normpath(external_editor)

            if external_editor and os.path.isfile(external_editor):
                # Use configured external editor
                subprocess.Popen([external_editor, str(file_path)])
                self._set_status(f"外部エディタで開きました: {file_path.name}")
            else:
                # Fall back to system default
                if sys.platform == "win32":
                    os.startfile(str(file_path))
                elif sys.platform == "darwin":
                    subprocess.run(["open", str(file_path)], check=True)
                else:
                    subprocess.run(["xdg-open", str(file_path)], check=True)
                self._set_status(f"既定のアプリで開きました: {file_path.name}")
        except Exception as e:
            ErrorDialog.show_error(self, DIALOG_TITLE_ERROR, f"ファイルを開けませんでした: {e}")

    def open_workspace_folder(self):
        """Open the workspace folder in file explorer."""
        if not self.workspace.current_workspace:
            return

        try:
            if sys.platform == "win32":
                os.startfile(str(self.workspace.current_workspace))
            elif sys.platform == "darwin":
                subprocess.run(["open", str(self.workspace.current_workspace)], check=True)
            else:
                subprocess.run(["xdg-open", str(self.workspace.current_workspace)], check=True)
        except Exception as e:
            ErrorDialog.show_error(self, DIALOG_TITLE_ERROR, f"フォルダを開けませんでした: {e}")

    def _on_file_double_clicked(self, rel_path: str):
        """Handle double-click on a file in the tree.

        Args:
            rel_path: Relative path of the clicked file.
        """
        abs_path = self.workspace.get_absolute_path(rel_path)
        if not abs_path or not abs_path.is_file():
            return

        # Check user preference
        if self.settings.get_use_external_editor():
            self._open_with_external_editor(abs_path)
        else:
            # Check if there are unsaved changes in current editor
            if not self.xml_editor.confirm_discard_changes():
                return

            if self.xml_editor.load_file(abs_path):
                self.tab_widget.setCurrentIndex(0)  # Switch to editor tab
                self._set_status(f"内蔵エディタで開きました: {abs_path.name}")
            else:
                ErrorDialog.show_error(self, DIALOG_TITLE_ERROR, f"ファイルを開けませんでした: {abs_path.name}")

    def _on_selection_changed(self):
        """Handle selection change in the tree."""
        abs_path = self.file_tree.get_selected_absolute_path()
        if not abs_path:
            self.info_label.setText("ファイルを選択してください")
            self.info_text.clear()
            self._update_ui_state()
            return

        self.info_label.setText(str(abs_path.name))

        # Show file info
        if abs_path.is_file():
            try:
                size = abs_path.stat().st_size
                info = f"サイズ: {self._format_size(size)}\n"
                info += f"パス: {abs_path.relative_to(self.workspace.current_workspace)}\n"

                # Try to show content preview for text files
                if abs_path.suffix.lower() in [".xml", ".rels"]:
                    try:
                        content = abs_path.read_text(encoding="utf-8")
                        if len(content) > 5000:
                            content = content[:5000] + "\n\n... (truncated)"
                        info += f"\n--- 内容プレビュー ---\n{content}"
                    except Exception:
                        pass

                self.info_text.setText(info)
            except Exception:
                self.info_text.setText("ファイル情報を取得できませんでした")
        else:
            self.info_text.setText(f"フォルダ: {abs_path.name}")

        self._update_ui_state()

    def _on_editor_file_saved(self, file_path: str):
        """Handle file saved in editor.

        Args:
            file_path: Path to the saved file.
        """
        self._set_status(f"保存しました: {Path(file_path).name}")
        self.workspace.is_modified = True
        self._update_ui_state()

    def _on_editor_content_modified(self):
        """Handle content modification in editor."""
        self._update_ui_state()

    def _format_size(self, size: int) -> str:
        """Format file size for display.

        Args:
            size: File size in bytes.

        Returns:
            Formatted size string.
        """
        if size < 1024:
            return f"{size} B"
        elif size < 1024 * 1024:
            return f"{size / 1024:.1f} KB"
        else:
            return f"{size / (1024 * 1024):.1f} MB"

    def _confirm_close_current(self) -> bool:
        """Confirm closing the current workspace if there are modifications.

        Returns:
            True if it's OK to proceed, False to cancel.
        """
        # Check editor unsaved changes
        if self.xml_editor.has_unsaved_changes():
            if not self.xml_editor.confirm_discard_changes():
                return False

        if not self.workspace.current_workspace:
            return True

        # Check for modifications
        self.workspace.check_modifications()
        if not self.workspace.is_modified:
            return True

        result = ConfirmDialog.confirm_exit_with_changes(self)
        if result is None:
            return False  # Cancel
        elif result:
            # Save and continue
            self.save_docx()
            return True
        else:
            # Don't save, just continue
            return True

    def show_settings(self):
        """Show the settings dialog."""
        dialog = SettingsDialog(self)
        dialog.exec()

    def show_about(self):
        """Show about dialog."""
        from ..utils.constants import APP_NAME, APP_VERSION
        ErrorDialog.show_info(
            self,
            "バージョン情報",
            f"{APP_NAME}\nバージョン: {APP_VERSION}\n\n.docxファイルの内容を編集するためのGUIツール\n\n"
            "ダブルクリック: 内蔵エディタで開く (設定で変更可)\n"
            "Ctrl+I: 内蔵エディタで開く\n"
            "Ctrl+E: 外部エディタで開く",
        )

    def closeEvent(self, event: QCloseEvent):
        """Handle window close event.

        Args:
            event: Close event.
        """
        if self._confirm_close_current():
            # Stop modification timer
            if self._modification_timer:
                self._modification_timer.stop()

            # Clean up workspace
            self.workspace.close()
            event.accept()
        else:
            event.ignore()

"""Main window for docx-workdir application."""

import os
import subprocess
import sys
from pathlib import Path
from typing import Optional

from PyQt6.QtCore import Qt, QTimer, QSize
from PyQt6.QtGui import QAction, QKeySequence, QCloseEvent, QIcon, QFont
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
    QFrame,
    QToolButton,
    QSizePolicy,
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
from .editor_window import EditorWindow
from .dialogs import ConfirmDialog, ErrorDialog, FileDialogs
from .settings_dialog import SettingsDialog
from .styles import TOOLBAR_BUTTON_STYLE, PRIMARY_BUTTON_STYLE


class WelcomeWidget(QWidget):
    """Welcome screen shown when no file is open."""

    open_clicked = None  # Will be set to signal

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Icon/Logo
        icon_label = QLabel("📄")
        icon_label.setStyleSheet("font-size: 64px;")
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(icon_label)

        layout.addSpacing(16)

        # Title
        title = QLabel("docx-workdir")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #1E293B;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # Subtitle
        subtitle = QLabel(".docxファイルの内部構造を編集")
        subtitle.setStyleSheet("font-size: 14px; color: #64748B;")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle)

        layout.addSpacing(32)

        # Open button
        self.btn_open = QPushButton("  ファイルを開く")
        self.btn_open.setStyleSheet(PRIMARY_BUTTON_STYLE)
        self.btn_open.setFixedSize(200, 48)
        self.btn_open.setCursor(Qt.CursorShape.PointingHandCursor)
        layout.addWidget(self.btn_open, alignment=Qt.AlignmentFlag.AlignCenter)

        layout.addSpacing(16)

        # Hint
        hint = QLabel("または Ctrl+O を押すか、ファイルをドラッグ＆ドロップ")
        hint.setStyleSheet("font-size: 12px; color: #94A3B8;")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(hint)

        layout.addSpacing(48)

        # Tips
        tips_frame = QFrame()
        tips_frame.setStyleSheet("""
            QFrame {
                background-color: #F1F5F9;
                border-radius: 8px;
                padding: 16px;
            }
        """)
        tips_layout = QVBoxLayout(tips_frame)

        tips_title = QLabel("💡 使い方")
        tips_title.setStyleSheet("font-weight: bold; color: #475569;")
        tips_layout.addWidget(tips_title)

        tips_text = QLabel(
            "1. .docxファイルを開くと内部構造がツリー表示されます\n"
            "2. ファイルをダブルクリックで内蔵エディタで編集\n"
            "3. 編集後「保存」で.docxとして出力\n\n"
            "🔒 元ファイルは変更されません（コピーで作業）"
        )
        tips_text.setStyleSheet("color: #64748B; line-height: 1.6;")
        tips_layout.addWidget(tips_text)

        layout.addWidget(tips_frame, alignment=Qt.AlignmentFlag.AlignCenter)


class MainWindow(QMainWindow):
    """Main application window."""

    def __init__(self):
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

        # Enable drag and drop
        self.setAcceptDrops(True)

    def _setup_ui(self):
        """Set up the main UI components."""
        self.setWindowTitle(APP_TITLE)
        self.setMinimumSize(MIN_WINDOW_WIDTH, MIN_WINDOW_HEIGHT)
        self.resize(1000, 700)  # Slightly larger default

        # Central widget with stacked layout
        central = QWidget()
        self.setCentralWidget(central)

        self.main_layout = QVBoxLayout(central)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # Welcome widget (shown when no file is open)
        self.welcome_widget = WelcomeWidget()
        self.welcome_widget.btn_open.clicked.connect(self.open_docx)
        self.main_layout.addWidget(self.welcome_widget)

        # Main content widget (hidden initially)
        self.content_widget = QWidget()
        content_layout = QVBoxLayout(self.content_widget)
        content_layout.setContentsMargins(8, 8, 8, 8)
        content_layout.setSpacing(8)

        # Info banner showing working on copy
        self.info_banner = QWidget()
        self.info_banner.setStyleSheet("""
            QWidget {
                background-color: #DBEAFE;
                border-radius: 6px;
            }
            QLabel {
                background: transparent;
            }
        """)
        info_banner_layout = QHBoxLayout(self.info_banner)
        info_banner_layout.setContentsMargins(12, 6, 12, 6)
        info_banner_layout.setSpacing(8)

        self.info_banner_icon = QLabel("🔒")
        info_banner_layout.addWidget(self.info_banner_icon)

        self.info_banner_text = QLabel("コピーで作業中")
        self.info_banner_text.setStyleSheet("font-weight: 600; color: #1E40AF; font-size: 12px;")
        info_banner_layout.addWidget(self.info_banner_text)

        self.info_banner_path = QLabel("")
        self.info_banner_path.setStyleSheet("color: #3B82F6; font-size: 11px;")
        self.info_banner_path.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        info_banner_layout.addWidget(self.info_banner_path, 1)

        # Button to open workspace in Explorer
        self.btn_open_workspace = QPushButton("📂 開く")
        self.btn_open_workspace.setToolTip("作業フォルダをエクスプローラーで開く")
        self.btn_open_workspace.setStyleSheet("""
            QPushButton {
                background-color: #2563EB;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 4px 10px;
                font-size: 11px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #1D4ED8;
            }
        """)
        self.btn_open_workspace.clicked.connect(self.open_workspace_folder)
        info_banner_layout.addWidget(self.btn_open_workspace)

        self.info_banner.setFixedHeight(36)
        content_layout.addWidget(self.info_banner)

        # Splitter for tree and editor panel
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.splitter.setHandleWidth(2)

        # Left panel - File tree with header
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(4)

        # Tree header
        self.tree_header = QLabel("📁 ファイル構造")
        self.tree_header.setStyleSheet("""
            font-weight: 600;
            color: #475569;
            padding: 8px 4px;
        """)
        left_layout.addWidget(self.tree_header)

        self.file_tree = FileTreeWidget()
        left_layout.addWidget(self.file_tree)

        self.splitter.addWidget(left_panel)

        # Right panel - File info (no tabs, simpler)
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(8, 8, 8, 8)
        right_layout.setSpacing(8)

        # Header
        info_header = QLabel("ℹ️ ファイル情報")
        info_header.setStyleSheet("""
            font-weight: 600;
            color: #475569;
            padding: 4px;
        """)
        right_layout.addWidget(info_header)

        self.info_label = QLabel("ファイルを選択してください")
        self.info_label.setStyleSheet("font-weight: 600; font-size: 14px; color: #1E293B;")
        self.info_label.setWordWrap(True)
        right_layout.addWidget(self.info_label)

        # Image preview area (hidden by default)
        from PyQt6.QtWidgets import QScrollArea
        from PyQt6.QtGui import QPixmap
        self.image_scroll = QScrollArea()
        self.image_scroll.setWidgetResizable(True)
        self.image_scroll.setStyleSheet("QScrollArea { border: 1px solid #E2E8F0; border-radius: 8px; }")
        self.image_scroll.setMaximumHeight(250)
        self.image_preview = QLabel()
        self.image_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_preview.setStyleSheet("background-color: #F8FAFC; padding: 8px;")
        self.image_scroll.setWidget(self.image_preview)
        self.image_scroll.hide()
        right_layout.addWidget(self.image_scroll)

        from PyQt6.QtWidgets import QTextEdit
        self.info_text = QTextEdit()
        self.info_text.setReadOnly(True)
        self.info_text.setPlaceholderText("ファイルを選択すると情報が表示されます")
        right_layout.addWidget(self.info_text)

        self.splitter.addWidget(right_panel)

        # Set splitter proportions - wider file tree
        self.splitter.setSizes([450, 350])

        content_layout.addWidget(self.splitter)

        self.content_widget.hide()
        self.main_layout.addWidget(self.content_widget)

    def _create_menus(self):
        """Create menu bar."""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("ファイル(&F)")

        self.action_open = QAction("📂 開く(&O)...", self)
        self.action_open.setShortcut(QKeySequence.StandardKey.Open)
        self.action_open.triggered.connect(self.open_docx)
        file_menu.addAction(self.action_open)

        file_menu.addSeparator()

        self.action_save = QAction("💾 上書き保存(&S)", self)
        self.action_save.setShortcut(QKeySequence.StandardKey.Save)
        self.action_save.triggered.connect(self.save_docx)
        file_menu.addAction(self.action_save)

        self.action_save_as = QAction("📝 名前を付けて保存(&A)...", self)
        self.action_save_as.setShortcut(QKeySequence("Ctrl+Shift+S"))
        self.action_save_as.triggered.connect(self.save_docx_as)
        file_menu.addAction(self.action_save_as)

        file_menu.addSeparator()

        self.action_close = QAction("✖ 閉じる(&C)", self)
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

        self.action_refresh = QAction("🔄 更新(&R)", self)
        self.action_refresh.setShortcut(QKeySequence.StandardKey.Refresh)
        self.action_refresh.triggered.connect(self.refresh_tree)
        edit_menu.addAction(self.action_refresh)

        edit_menu.addSeparator()

        self.action_open_folder = QAction("📁 作業フォルダを開く(&F)", self)
        self.action_open_folder.triggered.connect(self.open_workspace_folder)
        edit_menu.addAction(self.action_open_folder)

        # Tools menu
        tools_menu = menubar.addMenu("ツール(&T)")

        self.action_settings = QAction("⚙️ 設定(&S)...", self)
        self.action_settings.triggered.connect(self.show_settings)
        tools_menu.addAction(self.action_settings)

        # Help menu
        help_menu = menubar.addMenu("ヘルプ(&H)")

        self.action_about = QAction("ℹ️ バージョン情報(&A)", self)
        self.action_about.triggered.connect(self.show_about)
        help_menu.addAction(self.action_about)

    def _create_toolbar_button(self, text: str, tooltip: str = "") -> QPushButton:
        """Create a styled toolbar button."""
        btn = QPushButton(text)
        btn.setStyleSheet(TOOLBAR_BUTTON_STYLE)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        if tooltip:
            btn.setToolTip(tooltip)
        return btn

    def _create_toolbar(self):
        """Create toolbar."""
        toolbar = QToolBar("Main Toolbar")
        toolbar.setMovable(False)
        toolbar.setIconSize(QSize(20, 20))
        self.addToolBar(toolbar)

        # Open button
        self.btn_open = self._create_toolbar_button("📂 開く", "ファイルを開く (Ctrl+O)")
        self.btn_open.clicked.connect(self.open_docx)
        toolbar.addWidget(self.btn_open)

        toolbar.addSeparator()

        # Save button
        self.btn_save = self._create_toolbar_button("💾 保存", "上書き保存 (Ctrl+S)")
        self.btn_save.clicked.connect(self.save_docx)
        toolbar.addWidget(self.btn_save)

        # Save As button
        self.btn_save_as = self._create_toolbar_button("📝 別名保存", "名前を付けて保存 (Ctrl+Shift+S)")
        self.btn_save_as.clicked.connect(self.save_docx_as)
        toolbar.addWidget(self.btn_save_as)

        toolbar.addSeparator()

        # Refresh button
        self.btn_refresh = self._create_toolbar_button("🔄 更新", "ツリーを更新 (F5)")
        self.btn_refresh.clicked.connect(self.refresh_tree)
        toolbar.addWidget(self.btn_refresh)

        # Spacer
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        toolbar.addWidget(spacer)

        # Settings button (right aligned)
        self.btn_settings = self._create_toolbar_button("⚙️ 設定", "設定を開く")
        self.btn_settings.clicked.connect(self.show_settings)
        toolbar.addWidget(self.btn_settings)

    def _create_status_bar(self):
        """Create status bar."""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        self.status_label = QLabel("  📋 準備完了")
        self.status_label.setStyleSheet("color: #64748B;")
        self.status_bar.addWidget(self.status_label)

        self.modified_label = QLabel("")
        self.modified_label.setStyleSheet("color: #F59E0B; font-weight: 500;")
        self.status_bar.addPermanentWidget(self.modified_label)

    def _connect_signals(self):
        """Connect widget signals."""
        self.file_tree.file_double_clicked.connect(self._on_file_double_clicked)
        self.file_tree.itemSelectionChanged.connect(self._on_selection_changed)
        # File operation signals
        self.file_tree.file_replace_requested.connect(self._on_file_replace)
        self.file_tree.file_delete_requested.connect(self._on_file_delete)
        self.file_tree.file_add_requested.connect(self._on_file_add)
        self.file_tree.folder_add_requested.connect(self._on_folder_add)
        self.file_tree.file_revert_requested.connect(self._on_file_revert)

    def _start_modification_check(self):
        """Start timer for checking file modifications."""
        self._modification_timer = QTimer(self)
        self._modification_timer.timeout.connect(self._check_modifications)
        self._modification_timer.start(2000)

    def _check_modifications(self):
        """Check for modifications in the workspace."""
        if self.workspace.current_workspace:
            was_modified = self.workspace.is_modified
            self.workspace.check_modifications()

            # Update file tree with status indicators
            file_statuses = self.workspace.get_file_statuses()
            self.file_tree.update_file_statuses(file_statuses)
            self._update_tree_header(file_statuses)

            if self.workspace.is_modified != was_modified:
                self._update_ui_state()

    def _update_tree_header(self, file_statuses: dict[str, str] = None):
        """Update the tree header with change counts."""
        if file_statuses is None:
            file_statuses = self.workspace.get_file_statuses() if self.workspace.current_workspace else {}

        # Count each status
        counts = {'M': 0, 'A': 0, 'D': 0}
        for status in file_statuses.values():
            if status in counts:
                counts[status] += 1

        # Build header text
        total = sum(counts.values())
        if total > 0:
            parts = []
            if counts['M'] > 0:
                parts.append(f"M:{counts['M']}")
            if counts['A'] > 0:
                parts.append(f"A:{counts['A']}")
            if counts['D'] > 0:
                parts.append(f"D:{counts['D']}")
            self.tree_header.setText(f"📁 ファイル構造  ({', '.join(parts)})")
        else:
            self.tree_header.setText("📁 ファイル構造")

    def _update_window_title(self):
        """Update the window title."""
        title = APP_TITLE
        if self.workspace.source_docx:
            title = f"{self.workspace.source_docx.name} - {APP_TITLE}"
            if self.workspace.is_modified:
                title = f"● {title}"
        self.setWindowTitle(title)

    def _update_info_banner(self, source_path: Path, workspace_path: Path):
        """Update the info banner with workspace information."""
        self.info_banner_text.setText(f"コピーで作業中")
        # Show workspace path (shortened if too long)
        ws_str = str(workspace_path)
        if len(ws_str) > 60:
            ws_str = "..." + ws_str[-57:]
        self.info_banner_path.setText(f"📂 {ws_str}")
        self.info_banner_path.setToolTip(f"元ファイル: {source_path}\n作業フォルダ: {workspace_path}")

    def _update_ui_state(self):
        """Update UI elements based on current state."""
        has_workspace = self.workspace.current_workspace is not None
        has_selection = self.file_tree.get_selected_path() is not None
        selected_is_file = False
        if has_selection:
            abs_path = self.file_tree.get_selected_absolute_path()
            selected_is_file = abs_path and abs_path.is_file()

        # Show/hide welcome vs content
        self.welcome_widget.setVisible(not has_workspace)
        self.content_widget.setVisible(has_workspace)

        # Enable/disable actions
        self.action_save.setEnabled(has_workspace)
        self.action_save_as.setEnabled(has_workspace)
        self.action_close.setEnabled(has_workspace)
        self.action_refresh.setEnabled(has_workspace)
        self.action_open_folder.setEnabled(has_workspace)

        # Enable/disable toolbar buttons
        self.btn_save.setEnabled(has_workspace)
        self.btn_save_as.setEnabled(has_workspace)
        self.btn_refresh.setEnabled(has_workspace)

        # Update modified indicator in status bar
        # This shows if .docx needs to be re-saved (workspace modified)
        if self.workspace.is_modified:
            self.modified_label.setText("● docx未保存  ")
        else:
            self.modified_label.setText("")

        self._update_window_title()

    def _set_status(self, message: str):
        """Update status bar message."""
        self.status_label.setText(f"  📋 {message}")

    # ===== Drag and Drop =====

    def dragEnterEvent(self, event):
        """Handle drag enter event."""
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                if url.toLocalFile().lower().endswith('.docx'):
                    event.acceptProposedAction()
                    return
        event.ignore()

    def dropEvent(self, event):
        """Handle drop event."""
        for url in event.mimeData().urls():
            file_path = url.toLocalFile()
            if file_path.lower().endswith('.docx'):
                if self._confirm_close_current():
                    self._load_docx(Path(file_path))
                break

    # ===== File Operations =====

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
        """Load a docx file into the workspace."""
        try:
            workspace_path = self.workspace.open_docx(docx_path)
            self.file_tree.load_workspace(workspace_path)
            self._update_info_banner(docx_path, workspace_path)
            self._set_status(f"展開完了: {docx_path.name}")
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

        # Save any unsaved changes in editor window
        editor_window = EditorWindow._instance
        if editor_window and editor_window.has_unsaved_changes():
            editor_window.save_all()

        if not self.workspace.source_docx:
            self.save_docx_as()
            return

        try:
            self.workspace.save()
            self._set_status(f"保存完了: {self.workspace.source_docx.name}")
            self._update_ui_state()
        except Exception as e:
            ErrorDialog.show_error(self, DIALOG_TITLE_ERROR, MSG_ERROR_SAVE.format(str(e)))

    def save_docx_as(self):
        """Save changes to a new docx file."""
        if not self.workspace.current_workspace:
            return

        # Save any unsaved changes in editor window
        editor_window = EditorWindow._instance
        if editor_window and editor_window.has_unsaved_changes():
            editor_window.save_all()

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

        if output_path.exists():
            if not ConfirmDialog.confirm_overwrite(self, str(output_path)):
                return

        try:
            self.workspace.save_as(output_path, overwrite=True)
            self._set_status(f"保存完了: {output_path.name}")
            self._update_ui_state()
        except Exception as e:
            ErrorDialog.show_error(self, DIALOG_TITLE_ERROR, MSG_ERROR_SAVE.format(str(e)))

    def close_workspace(self):
        """Close the current workspace."""
        if not self._confirm_close_current():
            return

        self.workspace.close()
        self.file_tree.clear_workspace()
        self.info_label.setText("ファイルを選択してください")
        self.info_text.clear()
        self.image_scroll.hide()
        self._set_status("準備完了")
        self._update_ui_state()

    def refresh_tree(self):
        """Refresh the file tree."""
        # Get fresh file statuses from workspace and update tree
        if self.workspace.current_workspace:
            file_statuses = self.workspace.get_file_statuses()
            self.file_tree.update_file_statuses(file_statuses)
            self._update_tree_header(file_statuses)
        self.file_tree.refresh()
        self._set_status("ツリーを更新しました")

    def _open_with_external_editor(self, file_path: Path):
        """Open a file with the configured external editor or default app."""
        external_editor = self.settings.get_external_editor()

        try:
            if external_editor:
                external_editor = os.path.expandvars(external_editor)
                external_editor = os.path.normpath(external_editor)

            if external_editor and os.path.isfile(external_editor):
                subprocess.Popen([external_editor, str(file_path)])
                self._set_status(f"外部エディタで開きました: {file_path.name}")
            else:
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
        """Handle double-click on a file in the tree."""
        abs_path = self.workspace.get_absolute_path(rel_path)
        if not abs_path or not abs_path.is_file():
            return

        # Show dialog to choose editor
        from PyQt6.QtWidgets import QMessageBox
        msg = QMessageBox(self)
        msg.setWindowTitle("ファイルを開く")
        msg.setText(f"{abs_path.name} をどのエディタで開きますか？")
        msg.setIcon(QMessageBox.Icon.Question)

        btn_internal = msg.addButton("内蔵エディタ", QMessageBox.ButtonRole.AcceptRole)
        btn_external = msg.addButton("外部エディタ", QMessageBox.ButtonRole.ActionRole)
        msg.addButton("キャンセル", QMessageBox.ButtonRole.RejectRole)

        msg.exec()

        clicked = msg.clickedButton()
        if clicked == btn_internal:
            self._open_in_internal_editor(abs_path)
        elif clicked == btn_external:
            self._open_with_external_editor(abs_path)

    def _open_in_internal_editor(self, file_path: Path):
        """Open a file in the internal editor window."""
        editor_window = EditorWindow.get_instance()
        # Connect signal only if not already connected (avoid duplicates)
        try:
            editor_window.file_saved.disconnect(self._on_editor_file_saved)
        except TypeError:
            pass  # Not connected yet
        editor_window.file_saved.connect(self._on_editor_file_saved)
        if editor_window.open_file(file_path):
            self._set_status(f"エディタで開きました: {file_path.name}")

    def _on_selection_changed(self):
        """Handle selection change in the tree."""
        abs_path = self.file_tree.get_selected_absolute_path()
        if not abs_path:
            self.info_label.setText("ファイルを選択してください")
            self.info_text.clear()
            self.image_scroll.hide()
            self._update_ui_state()
            return

        self.info_label.setText(str(abs_path.name))

        # Image file extensions
        image_extensions = ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.ico']

        if abs_path.is_file():
            try:
                size = abs_path.stat().st_size
                info = f"📄 ファイル: {abs_path.name}\n"
                info += f"📦 サイズ: {self._format_size(size)}\n"
                info += f"📍 パス: {abs_path.relative_to(self.workspace.current_workspace)}\n"

                suffix_lower = abs_path.suffix.lower()

                # Check if it's an image file
                if suffix_lower in image_extensions:
                    self._show_image_preview(abs_path)
                    info += f"\n🖼️ 画像プレビューを上に表示中"
                else:
                    self.image_scroll.hide()

                if suffix_lower in [".xml", ".rels"]:
                    try:
                        content = abs_path.read_text(encoding="utf-8")
                        if len(content) > 5000:
                            content = content[:5000] + "\n\n... (省略)"
                        info += f"\n{'─' * 40}\n📝 内容プレビュー:\n{'─' * 40}\n{content}"
                    except Exception:
                        pass

                self.info_text.setText(info)
            except Exception:
                self.info_text.setText("ファイル情報を取得できませんでした")
                self.image_scroll.hide()
        else:
            self.info_text.setText(f"📁 フォルダ: {abs_path.name}")
            self.image_scroll.hide()

        self._update_ui_state()

    def _show_image_preview(self, image_path: Path):
        """Show image preview in the info panel."""
        from PyQt6.QtGui import QPixmap

        pixmap = QPixmap(str(image_path))
        if pixmap.isNull():
            self.image_preview.setText("画像を読み込めませんでした")
            self.image_scroll.show()
            return

        # Scale image to fit in preview area while maintaining aspect ratio
        max_width = 400
        max_height = 300
        if pixmap.width() > max_width or pixmap.height() > max_height:
            pixmap = pixmap.scaled(
                max_width, max_height,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )

        self.image_preview.setPixmap(pixmap)
        self.image_scroll.show()

    # ===== File Operations =====

    def _on_file_replace(self, rel_path: str):
        """Handle file replace request."""
        abs_path = self.workspace.get_absolute_path(rel_path)
        if not abs_path or not abs_path.is_file():
            return

        # Get file extension for filter
        suffix = abs_path.suffix
        filter_str = f"Same type (*{suffix});;All files (*.*)" if suffix else "All files (*.*)"

        from PyQt6.QtWidgets import QFileDialog
        new_file, _ = QFileDialog.getOpenFileName(
            self,
            f"差し替えるファイルを選択 - {abs_path.name}",
            "",
            filter_str
        )

        if not new_file:
            return

        try:
            import shutil
            shutil.copy2(new_file, abs_path)
            self.workspace.is_modified = True
            self._set_status(f"差し替え完了: {abs_path.name}")
            self.refresh_tree()
            self._update_ui_state()
        except Exception as e:
            ErrorDialog.show_error(self, DIALOG_TITLE_ERROR, f"ファイルの差し替えに失敗しました:\n{e}")

    def _on_file_revert(self, rel_path: str):
        """Handle file revert request."""
        status = self.workspace.get_file_statuses().get(rel_path, '')
        if not status:
            return

        # Determine message based on status
        if status == 'A':
            msg = f"追加したファイルを削除しますか？\n\n{rel_path}"
        elif status == 'D':
            msg = f"削除したファイルを復元しますか？\n\n{rel_path}"
        else:  # M
            msg = f"ファイルを元の状態に戻しますか？\n\n{rel_path}\n\n※現在の変更は失われます"

        result = ConfirmDialog.confirm(self, "元に戻す", msg)
        if not result:
            return

        try:
            self.workspace.revert_file(rel_path)
            self._set_status(f"元に戻しました: {Path(rel_path).name}")
            self.refresh_tree()
            self._update_ui_state()
        except Exception as e:
            ErrorDialog.show_error(self, DIALOG_TITLE_ERROR, f"元に戻せませんでした:\n{e}")

    def _on_file_delete(self, rel_path: str):
        """Handle file delete request."""
        abs_path = self.workspace.get_absolute_path(rel_path)
        if not abs_path:
            return

        # Confirmation dialog
        result = ConfirmDialog.confirm(
            self,
            "ファイル削除の確認",
            f"以下のファイルを削除しますか？\n\n{rel_path}\n\n※右クリック→「元に戻す」で復元できます"
        )

        if not result:
            return

        try:
            if abs_path.is_file():
                abs_path.unlink()
            elif abs_path.is_dir():
                import shutil
                shutil.rmtree(abs_path)

            self.workspace.is_modified = True
            self._set_status(f"削除完了: {Path(rel_path).name}")
            self.refresh_tree()
            self._update_ui_state()
        except Exception as e:
            ErrorDialog.show_error(self, DIALOG_TITLE_ERROR, f"削除に失敗しました:\n{e}")

    def _on_file_add(self, rel_folder_path: str):
        """Handle file add request to a folder."""
        abs_folder = self.workspace.get_absolute_path(rel_folder_path)
        if not abs_folder or not abs_folder.is_dir():
            return

        from PyQt6.QtWidgets import QFileDialog
        new_files, _ = QFileDialog.getOpenFileNames(
            self,
            f"追加するファイルを選択 - {rel_folder_path}",
            "",
            "All files (*.*)"
        )

        if not new_files:
            return

        try:
            import shutil
            added = []
            for new_file in new_files:
                src = Path(new_file)
                dst = abs_folder / src.name
                shutil.copy2(src, dst)
                added.append(src.name)

            self.workspace.is_modified = True
            self._set_status(f"追加完了: {', '.join(added)}")
            self.refresh_tree()
            self._update_ui_state()
        except Exception as e:
            ErrorDialog.show_error(self, DIALOG_TITLE_ERROR, f"ファイルの追加に失敗しました:\n{e}")

    def _on_folder_add(self, rel_folder_path: str):
        """Handle folder add request."""
        abs_folder = self.workspace.get_absolute_path(rel_folder_path)
        if not abs_folder or not abs_folder.is_dir():
            return

        from PyQt6.QtWidgets import QInputDialog
        folder_name, ok = QInputDialog.getText(
            self,
            "新しいフォルダ",
            "フォルダ名を入力してください:",
            text="新しいフォルダ"
        )

        if not ok or not folder_name:
            return

        try:
            new_folder = abs_folder / folder_name
            new_folder.mkdir(parents=True, exist_ok=True)

            self.workspace.is_modified = True
            self._set_status(f"フォルダ作成完了: {folder_name}")
            self.refresh_tree()
            self._update_ui_state()
        except Exception as e:
            ErrorDialog.show_error(self, DIALOG_TITLE_ERROR, f"フォルダの作成に失敗しました:\n{e}")

    def _on_editor_file_saved(self, file_path: str):
        """Handle file saved in editor."""
        self._set_status(f"保存しました: {Path(file_path).name}")
        self.workspace.is_modified = True
        self._update_ui_state()

    def _format_size(self, size: int) -> str:
        """Format file size for display."""
        if size < 1024:
            return f"{size} B"
        elif size < 1024 * 1024:
            return f"{size / 1024:.1f} KB"
        else:
            return f"{size / (1024 * 1024):.1f} MB"

    def _confirm_close_current(self) -> bool:
        """Confirm closing the current workspace if there are modifications."""
        # Check if editor window has unsaved changes
        editor_window = EditorWindow._instance
        if editor_window and editor_window.has_unsaved_changes():
            unsaved = editor_window.get_unsaved_files()
            from PyQt6.QtWidgets import QMessageBox
            result = QMessageBox.question(
                self,
                "未保存の変更",
                f"エディタに{len(unsaved)}個の未保存ファイルがあります。\n保存せずに続行しますか？",
                QMessageBox.StandardButton.Save |
                QMessageBox.StandardButton.Discard |
                QMessageBox.StandardButton.Cancel,
                QMessageBox.StandardButton.Cancel,
            )
            if result == QMessageBox.StandardButton.Save:
                editor_window.save_all()
            elif result == QMessageBox.StandardButton.Cancel:
                return False

        if not self.workspace.current_workspace:
            return True

        self.workspace.check_modifications()
        if not self.workspace.is_modified:
            return True

        result = ConfirmDialog.confirm_exit_with_changes(self)
        if result is None:
            return False
        elif result:
            self.save_docx()
            return True
        else:
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
            f"📄 {APP_NAME}\n"
            f"バージョン: {APP_VERSION}\n\n"
            f".docxファイルの内部構造を編集するためのGUIツール\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"📌 ショートカットキー:\n"
            f"  Ctrl+O  ファイルを開く\n"
            f"  Ctrl+S  保存\n"
            f"  Ctrl+I  内蔵エディタで開く\n"
            f"  Ctrl+E  外部エディタで開く\n"
            f"  Ctrl+F  検索",
        )

    def closeEvent(self, event: QCloseEvent):
        """Handle window close event."""
        if self._confirm_close_current():
            if self._modification_timer:
                self._modification_timer.stop()
            self.workspace.close()
            event.accept()
        else:
            event.ignore()

"""Settings dialog for docx-workdir application."""

import os
from pathlib import Path

from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QGroupBox,
    QLabel,
    QLineEdit,
    QPushButton,
    QCheckBox,
    QFileDialog,
    QDialogButtonBox,
)
from PyQt6.QtCore import Qt

from ..utils.settings import get_settings


class SettingsDialog(QDialog):
    """Dialog for configuring application settings."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.settings = get_settings()
        self._setup_ui()
        self._load_settings()

    def _setup_ui(self):
        """Set up the dialog UI."""
        self.setWindowTitle("設定")
        self.setMinimumWidth(600)

        layout = QVBoxLayout(self)

        # External editor group
        editor_group = QGroupBox("外部エディタ")
        editor_layout = QVBoxLayout(editor_group)

        # Use external editor checkbox
        self.chk_use_external = QCheckBox("ダブルクリック時に外部エディタを使用する")
        editor_layout.addWidget(self.chk_use_external)

        # Editor path
        path_layout = QHBoxLayout()
        path_layout.addWidget(QLabel("エディタのパス:"))

        self.txt_editor_path = QLineEdit()
        self.txt_editor_path.setPlaceholderText("例: C:\\Program Files\\Microsoft VS Code\\Code.exe")
        self.txt_editor_path.textChanged.connect(self._on_path_changed)
        path_layout.addWidget(self.txt_editor_path)

        self.btn_browse = QPushButton("参照...")
        self.btn_browse.clicked.connect(self._browse_editor)
        path_layout.addWidget(self.btn_browse)

        editor_layout.addLayout(path_layout)

        # Status label
        self.status_label = QLabel("")
        self.status_label.setWordWrap(True)
        editor_layout.addWidget(self.status_label)

        layout.addWidget(editor_group)

        # Common external editors info
        common_group = QGroupBox("よく使われる外部エディタ (クリックで設定)")
        common_layout = QVBoxLayout(common_group)

        common_editors = [
            ("VS Code (システム)", "C:\\Program Files\\Microsoft VS Code\\Code.exe"),
            ("VS Code (ユーザー)", "%LOCALAPPDATA%\\Programs\\Microsoft VS Code\\Code.exe"),
            ("Notepad++", "C:\\Program Files\\Notepad++\\notepad++.exe"),
            ("Notepad++ (x86)", "C:\\Program Files (x86)\\Notepad++\\notepad++.exe"),
            ("サクラエディタ", "C:\\Program Files (x86)\\sakura\\sakura.exe"),
            ("メモ帳", "C:\\Windows\\notepad.exe"),
        ]

        for name, path in common_editors:
            # Check if this editor exists
            expanded = os.path.expandvars(path)
            exists = os.path.isfile(expanded)
            status = "✓" if exists else "✗"

            btn = QPushButton(f"{status} {name}")
            btn.setToolTip(f"{path}\n展開後: {expanded}")
            btn.setStyleSheet("text-align: left; padding: 5px;")
            btn.setEnabled(exists)
            btn.clicked.connect(lambda checked, p=expanded: self._set_editor_path(p))
            common_layout.addWidget(btn)

        layout.addWidget(common_group)

        layout.addStretch()

        # Dialog buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self._save_and_accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def _load_settings(self):
        """Load current settings into the UI."""
        self.txt_editor_path.setText(self.settings.get_external_editor())
        self.chk_use_external.setChecked(self.settings.get_use_external_editor())
        self._on_path_changed()

    def _on_path_changed(self):
        """Update status when path changes."""
        path = self.txt_editor_path.text().strip()
        if not path:
            self.status_label.setText("")
            self.status_label.setStyleSheet("")
            return

        # Expand and check
        expanded = os.path.expandvars(path)
        expanded = os.path.normpath(expanded)

        if os.path.isfile(expanded):
            self.status_label.setText(f"✓ 有効なパス: {expanded}")
            self.status_label.setStyleSheet("color: green;")
        else:
            self.status_label.setText(f"✗ ファイルが見つかりません: {expanded}")
            self.status_label.setStyleSheet("color: red;")

    def _browse_editor(self):
        """Open file dialog to browse for external editor."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "外部エディタを選択",
            "C:\\Program Files",
            "実行ファイル (*.exe);;すべてのファイル (*.*)",
        )
        if file_path:
            self.txt_editor_path.setText(file_path)

    def _set_editor_path(self, path: str):
        """Set the editor path from a preset."""
        self.txt_editor_path.setText(path)

    def _save_and_accept(self):
        """Save settings and close the dialog."""
        path = self.txt_editor_path.text().strip()
        # Expand and normalize before saving
        if path:
            path = os.path.expandvars(path)
            path = os.path.normpath(path)

        self.settings.set_external_editor(path)
        self.settings.set_use_external_editor(self.chk_use_external.isChecked())
        self.settings.sync()
        self.accept()

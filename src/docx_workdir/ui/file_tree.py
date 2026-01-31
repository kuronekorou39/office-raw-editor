"""File tree widget for displaying Office file contents."""

from pathlib import Path
from typing import Optional

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QIcon, QAction
from PyQt6.QtWidgets import (
    QTreeWidget,
    QTreeWidgetItem,
    QHeaderView,
    QStyle,
    QMenu,
)

from ..utils.constants import (
    TREE_COLUMN_NAME,
    TREE_COLUMN_SIZE,
    TREE_COLUMN_TYPE,
    FILE_TYPE_MAP,
    FOLDER_ICON,
    UNKNOWN_ICON,
    format_file_size,
)


class FileTreeWidget(QTreeWidget):
    """Tree widget displaying the file structure of an extracted docx."""

    file_double_clicked = pyqtSignal(str)  # Emits the relative file path

    # File operation signals
    file_replace_requested = pyqtSignal(str)  # Emits the relative file path to replace
    file_delete_requested = pyqtSignal(str)  # Emits the relative file path to delete
    file_add_requested = pyqtSignal(str)  # Emits the relative folder path to add to
    folder_add_requested = pyqtSignal(str)  # Emits the relative folder path to add folder to
    file_revert_requested = pyqtSignal(str)  # Emits the relative file path to revert

    # Status colors
    STATUS_COLORS = {
        'M': '#D97706',  # Modified - Amber
        'A': '#059669',  # Added - Green
        'D': '#DC2626',  # Deleted - Red
    }

    def __init__(self, parent=None):
        """Initialize the FileTreeWidget.

        Args:
            parent: Parent widget.
        """
        super().__init__(parent)
        self._workspace_path: Optional[Path] = None
        self._file_statuses: dict[str, str] = {}
        self._items_map: dict[str, QTreeWidgetItem] = {}
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        """Set up the tree widget UI."""
        self.setHeaderLabels([TREE_COLUMN_NAME, TREE_COLUMN_SIZE, TREE_COLUMN_TYPE, "状態"])
        self.setColumnCount(4)

        # Configure header
        header = self.header()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)

        # Enable sorting
        self.setSortingEnabled(True)
        self.sortByColumn(0, Qt.SortOrder.AscendingOrder)

        # Selection mode
        self.setSelectionMode(QTreeWidget.SelectionMode.SingleSelection)

        # Visual settings
        self.setAlternatingRowColors(True)
        self.setRootIsDecorated(True)
        self.setAnimated(True)

        # Enable context menu
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)

    def _connect_signals(self):
        """Connect internal signals."""
        self.itemDoubleClicked.connect(self._on_item_double_clicked)

    def _show_context_menu(self, position):
        """Show context menu at the given position."""
        item = self.itemAt(position)
        if not item or not self._workspace_path:
            return

        rel_path = item.data(0, Qt.ItemDataRole.UserRole)
        if not rel_path:
            return

        abs_path = self._workspace_path / rel_path
        is_dir = abs_path.is_dir() if abs_path.exists() else False

        menu = QMenu(self)

        if is_dir:
            # Folder context menu
            action_add_file = QAction("📄 ファイルを追加...", self)
            action_add_file.triggered.connect(lambda: self.file_add_requested.emit(rel_path))
            menu.addAction(action_add_file)

            action_add_folder = QAction("📁 フォルダを追加...", self)
            action_add_folder.triggered.connect(lambda: self.folder_add_requested.emit(rel_path))
            menu.addAction(action_add_folder)
        else:
            # File context menu
            status = self._file_statuses.get(rel_path, '')

            # Show revert option for modified/added/deleted files
            if status in ('M', 'A', 'D'):
                if status == 'A':
                    revert_label = "↩️ 元に戻す (追加を取り消し)"
                elif status == 'D':
                    revert_label = "↩️ 元に戻す (削除を取り消し)"
                else:
                    revert_label = "↩️ 元に戻す (変更を取り消し)"

                action_revert = QAction(revert_label, self)
                action_revert.triggered.connect(lambda: self.file_revert_requested.emit(rel_path))
                menu.addAction(action_revert)
                menu.addSeparator()

            # Only show replace/delete for existing files (not deleted)
            if status != 'D':
                action_replace = QAction("🔄 ファイルを差し替え...", self)
                action_replace.triggered.connect(lambda: self.file_replace_requested.emit(rel_path))
                menu.addAction(action_replace)

                menu.addSeparator()

                action_delete = QAction("🗑️ 削除", self)
                action_delete.triggered.connect(lambda: self.file_delete_requested.emit(rel_path))
                menu.addAction(action_delete)

        menu.exec(self.viewport().mapToGlobal(position))

    def _get_file_icon(self, is_dir: bool, suffix: str) -> QIcon:
        """Get the appropriate icon for a file or directory.

        Args:
            is_dir: True if this is a directory.
            suffix: File extension (including dot).

        Returns:
            QIcon for the item.
        """
        style = self.style()
        if is_dir:
            return style.standardIcon(QStyle.StandardPixmap.SP_DirIcon)

        # Map by file extension
        suffix_lower = suffix.lower()
        if suffix_lower in FILE_TYPE_MAP:
            file_type = FILE_TYPE_MAP[suffix_lower]
            if file_type in ["xml", "rels"]:
                return style.standardIcon(QStyle.StandardPixmap.SP_FileIcon)
            elif file_type == "image":
                return style.standardIcon(QStyle.StandardPixmap.SP_DesktopIcon)

        return style.standardIcon(QStyle.StandardPixmap.SP_FileIcon)

    def _get_file_type(self, is_dir: bool, suffix: str) -> str:
        """Get the file type description.

        Args:
            is_dir: True if this is a directory.
            suffix: File extension (including dot).

        Returns:
            File type description.
        """
        if is_dir:
            return "Folder"

        suffix_lower = suffix.lower()
        type_map = {
            ".xml": "XML File",
            ".rels": "Relationships",
            ".png": "PNG Image",
            ".jpg": "JPEG Image",
            ".jpeg": "JPEG Image",
            ".gif": "GIF Image",
            ".emf": "EMF Image",
            ".wmf": "WMF Image",
        }
        return type_map.get(suffix_lower, "File")

    def load_workspace(self, workspace_path: Path, file_statuses: Optional[dict[str, str]] = None):
        """Load the contents of a workspace directory into the tree.

        Args:
            workspace_path: Path to the workspace directory.
            file_statuses: Optional dict of relative path -> status ('M', 'A', 'D').
        """
        self.clear()
        self._workspace_path = workspace_path
        self._file_statuses = file_statuses or {}

        if not workspace_path or not workspace_path.exists():
            return

        # Build tree structure
        self._items_map.clear()

        # Collect all paths: existing files + deleted files from statuses
        existing_paths = set()
        for path in workspace_path.rglob('*'):
            rel_path = path.relative_to(workspace_path)
            existing_paths.add(str(rel_path))

        # Add deleted files from statuses
        deleted_paths = set()
        for rel_path, status in self._file_statuses.items():
            if status == 'D':
                deleted_paths.add(rel_path)

        all_paths = existing_paths | deleted_paths
        sorted_paths = sorted(all_paths)

        for rel_path_str in sorted_paths:
            parts = Path(rel_path_str).parts
            is_deleted = rel_path_str in deleted_paths

            # Build the path progressively
            for i in range(len(parts)):
                current_rel = str(Path(*parts[:i + 1]))

                if current_rel in self._items_map:
                    continue

                current_path = workspace_path / current_rel
                is_current_deleted = current_rel in deleted_paths

                if is_current_deleted:
                    # Deleted file - show with placeholder info
                    is_dir = False
                    name = parts[i]
                    suffix = Path(current_rel).suffix
                    size = 0
                else:
                    is_dir = current_path.is_dir()
                    name = parts[i]
                    suffix = current_path.suffix if not is_dir else ""
                    size = current_path.stat().st_size if current_path.is_file() else 0

                # Create tree item
                item = QTreeWidgetItem()
                item.setData(0, Qt.ItemDataRole.UserRole, current_rel)
                item.setText(0, name)
                item.setText(1, format_file_size(size) if not is_dir else "")
                item.setText(2, self._get_file_type(is_dir, suffix))
                item.setIcon(0, self._get_file_icon(is_dir, suffix))

                # Set status in column 3
                status = self._file_statuses.get(current_rel, '')
                self._apply_status_to_item(item, status, is_dir)

                # Add to parent or root
                if i == 0:
                    self.addTopLevelItem(item)
                else:
                    parent_rel = str(Path(*parts[:i]))
                    parent_item = self._items_map.get(parent_rel)
                    if parent_item:
                        parent_item.addChild(item)

                self._items_map[current_rel] = item

        # Expand important directories
        self.expandAll()

    def _apply_status_to_item(self, item: QTreeWidgetItem, status: str, is_dir: bool):
        """Apply status styling to a tree item.

        Args:
            item: The tree item.
            status: Status string ('M', 'A', 'D', or '').
            is_dir: Whether the item is a directory.
        """
        from PyQt6.QtGui import QBrush, QColor, QFont

        if not status or is_dir:
            item.setText(3, "")
            # Reset to default style
            default_font = item.font(0)
            default_font.setStrikeOut(False)
            item.setFont(0, default_font)
            item.setForeground(0, QBrush(QColor('#1E293B')))
            item.setForeground(3, QBrush(QColor('#1E293B')))
            return

        # Set status text in column 3
        item.setText(3, status)

        # Apply color to status column
        color = QColor(self.STATUS_COLORS.get(status, '#1E293B'))
        item.setForeground(3, QBrush(color))

        # For deleted files, apply strikethrough and gray color to name
        if status == 'D':
            font = item.font(0)
            font.setStrikeOut(True)
            item.setFont(0, font)
            item.setForeground(0, QBrush(QColor('#9CA3AF')))  # Gray for deleted
        else:
            # For M and A, just color the status column, keep name normal
            font = item.font(0)
            font.setStrikeOut(False)
            item.setFont(0, font)
            item.setForeground(0, QBrush(QColor('#1E293B')))

    def update_file_statuses(self, file_statuses: dict[str, str]):
        """Update the status indicators for files.

        Args:
            file_statuses: Dict of relative path -> status ('M', 'A', 'D').
        """
        old_statuses = self._file_statuses
        self._file_statuses = file_statuses

        if not self._workspace_path:
            return

        # Check if we need to reload (new deleted files appeared)
        old_deleted = {k for k, v in old_statuses.items() if v == 'D'}
        new_deleted = {k for k, v in file_statuses.items() if v == 'D'}

        if new_deleted != old_deleted:
            # Deleted files changed, need to reload the tree
            self.refresh()
            return

        # Just update status column for existing items
        for rel_path, item in self._items_map.items():
            status = file_statuses.get(rel_path, '')
            abs_path = self._workspace_path / rel_path
            is_dir = abs_path.is_dir() if abs_path.exists() else False

            self._apply_status_to_item(item, status, is_dir)

    def clear_workspace(self):
        """Clear the tree and reset workspace path."""
        self.clear()
        self._workspace_path = None

    def _on_item_double_clicked(self, item: QTreeWidgetItem, column: int):
        """Handle double-click on a tree item.

        Args:
            item: The clicked item.
            column: The clicked column.
        """
        rel_path = item.data(0, Qt.ItemDataRole.UserRole)
        if not rel_path or not self._workspace_path:
            return

        full_path = self._workspace_path / rel_path
        if full_path.is_file():
            self.file_double_clicked.emit(rel_path)

    def get_selected_path(self) -> Optional[str]:
        """Get the relative path of the currently selected item.

        Returns:
            Relative path string, or None if nothing is selected.
        """
        items = self.selectedItems()
        if not items:
            return None
        return items[0].data(0, Qt.ItemDataRole.UserRole)

    def get_selected_absolute_path(self) -> Optional[Path]:
        """Get the absolute path of the currently selected item.

        Returns:
            Absolute Path, or None if nothing is selected.
        """
        rel_path = self.get_selected_path()
        if not rel_path or not self._workspace_path:
            return None
        return self._workspace_path / rel_path

    def refresh(self):
        """Refresh the tree view from the current workspace."""
        if self._workspace_path:
            # Save expansion state
            expanded_items = set()
            for i in range(self.topLevelItemCount()):
                self._save_expansion_state(self.topLevelItem(i), expanded_items)

            # Preserve file statuses
            saved_statuses = self._file_statuses.copy()

            # Reload with preserved statuses
            self.load_workspace(self._workspace_path, saved_statuses)

            # Restore expansion state
            for i in range(self.topLevelItemCount()):
                self._restore_expansion_state(self.topLevelItem(i), expanded_items)

    def _save_expansion_state(self, item: QTreeWidgetItem, expanded_set: set):
        """Recursively save expansion state of items.

        Args:
            item: Tree item to check.
            expanded_set: Set to store expanded paths.
        """
        rel_path = item.data(0, Qt.ItemDataRole.UserRole)
        if item.isExpanded():
            expanded_set.add(rel_path)

        for i in range(item.childCount()):
            self._save_expansion_state(item.child(i), expanded_set)

    def _restore_expansion_state(self, item: QTreeWidgetItem, expanded_set: set):
        """Recursively restore expansion state of items.

        Args:
            item: Tree item to restore.
            expanded_set: Set of expanded paths.
        """
        rel_path = item.data(0, Qt.ItemDataRole.UserRole)
        if rel_path in expanded_set:
            item.setExpanded(True)

        for i in range(item.childCount()):
            self._restore_expansion_state(item.child(i), expanded_set)

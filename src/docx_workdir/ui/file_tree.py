"""File tree widget for displaying docx contents."""

import os
from pathlib import Path
from typing import Optional

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import (
    QTreeWidget,
    QTreeWidgetItem,
    QHeaderView,
    QStyle,
)

from ..utils.constants import (
    TREE_COLUMN_NAME,
    TREE_COLUMN_SIZE,
    TREE_COLUMN_TYPE,
    FILE_TYPE_MAP,
    FOLDER_ICON,
    UNKNOWN_ICON,
)


class FileTreeWidget(QTreeWidget):
    """Tree widget displaying the file structure of an extracted docx."""

    file_double_clicked = pyqtSignal(str)  # Emits the relative file path

    def __init__(self, parent=None):
        """Initialize the FileTreeWidget.

        Args:
            parent: Parent widget.
        """
        super().__init__(parent)
        self._workspace_path: Optional[Path] = None
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        """Set up the tree widget UI."""
        self.setHeaderLabels([TREE_COLUMN_NAME, TREE_COLUMN_SIZE, TREE_COLUMN_TYPE])
        self.setColumnCount(3)

        # Configure header
        header = self.header()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)

        # Enable sorting
        self.setSortingEnabled(True)
        self.sortByColumn(0, Qt.SortOrder.AscendingOrder)

        # Selection mode
        self.setSelectionMode(QTreeWidget.SelectionMode.SingleSelection)

        # Visual settings
        self.setAlternatingRowColors(True)
        self.setRootIsDecorated(True)
        self.setAnimated(True)

    def _connect_signals(self):
        """Connect internal signals."""
        self.itemDoubleClicked.connect(self._on_item_double_clicked)

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

    def load_workspace(self, workspace_path: Path):
        """Load the contents of a workspace directory into the tree.

        Args:
            workspace_path: Path to the workspace directory.
        """
        self.clear()
        self._workspace_path = workspace_path

        if not workspace_path or not workspace_path.exists():
            return

        # Build tree structure
        items_map: dict[str, QTreeWidgetItem] = {}

        # Get all paths and sort them
        paths = sorted(workspace_path.rglob('*'))

        for path in paths:
            rel_path = path.relative_to(workspace_path)
            parts = rel_path.parts

            # Build the path progressively
            for i in range(len(parts)):
                current_rel = str(Path(*parts[:i + 1]))
                current_path = workspace_path / current_rel

                if current_rel in items_map:
                    continue

                is_dir = current_path.is_dir()
                name = parts[i]
                suffix = current_path.suffix if not is_dir else ""
                size = current_path.stat().st_size if current_path.is_file() else 0

                # Create tree item
                item = QTreeWidgetItem()
                item.setText(0, name)
                item.setText(1, self._format_size(size) if not is_dir else "")
                item.setText(2, self._get_file_type(is_dir, suffix))
                item.setIcon(0, self._get_file_icon(is_dir, suffix))
                item.setData(0, Qt.ItemDataRole.UserRole, current_rel)

                # Add to parent or root
                if i == 0:
                    self.addTopLevelItem(item)
                else:
                    parent_rel = str(Path(*parts[:i]))
                    parent_item = items_map.get(parent_rel)
                    if parent_item:
                        parent_item.addChild(item)

                items_map[current_rel] = item

        # Expand important directories
        self.expandAll()

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

            # Reload
            self.load_workspace(self._workspace_path)

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

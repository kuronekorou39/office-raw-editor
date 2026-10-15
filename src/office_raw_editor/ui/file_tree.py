"""File tree widget for displaying Office file contents."""

from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIcon, QAction, QFont
from PySide6.QtWidgets import (
    QTreeWidget,
    QTreeWidgetItem,
    QHeaderView,
    QMenu,
)

from .icons import icon
from .styles import COLORS
from ..utils.constants import (
    TREE_COLUMN_NAME,
    TREE_COLUMN_SIZE,
    TREE_COLUMN_TYPE,
    FILE_TYPE_MAP,
    format_file_size,
    is_main_content_file,
)


class FileTreeWidget(QTreeWidget):
    """Tree widget displaying the file structure of an extracted docx."""

    file_double_clicked = Signal(str)  # Emits the relative file path

    # File operation signals
    file_replace_requested = Signal(str)  # Emits the relative file path to replace
    file_delete_requested = Signal(str)  # Emits the relative file path to delete
    file_add_requested = Signal(str)  # Emits the relative folder path to add to
    folder_add_requested = Signal(str)  # Emits the relative folder path to add folder to
    file_revert_requested = Signal(str)  # Emits the relative file path to revert

    # Status colors
    STATUS_COLORS = {
        'M': '#D97706',  # Modified - Amber
        'A': '#059669',  # Added - Green
        'D': '#DC2626',  # Deleted - Red
    }

    # Color used to highlight files containing the search string
    SEARCH_HIGHLIGHT_COLOR = '#FEF08A'  # 薄い黄色

    # Item data role holding the plain size text (hit counts are appended to the visible text)
    SIZE_TEXT_ROLE = Qt.ItemDataRole.UserRole + 1

    def __init__(self, parent=None):
        """Initialize the FileTreeWidget.

        Args:
            parent: Parent widget.
        """
        super().__init__(parent)
        self._workspace_path: Optional[Path] = None
        self._file_statuses: dict[str, str] = {}
        self._items_map: dict[str, QTreeWidgetItem] = {}
        self._search_matches: set[str] = set()
        self._search_match_counts: dict[str, int] = {}
        self._search_filter_active: bool = False
        self._size_heatmap_brushes: dict[str, object] = {}  # rel_path -> QBrush
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
            action_add_file = QAction(icon("file-plus"), "ファイルを追加...", self)
            action_add_file.triggered.connect(lambda: self.file_add_requested.emit(rel_path))
            menu.addAction(action_add_file)

            action_add_folder = QAction(icon("folder-plus"), "フォルダを追加...", self)
            action_add_folder.triggered.connect(lambda: self.folder_add_requested.emit(rel_path))
            menu.addAction(action_add_folder)
        else:
            # File context menu
            status = self._file_statuses.get(rel_path, '')

            # Show revert option for modified/added/deleted files
            if status in ('M', 'A', 'D'):
                if status == 'A':
                    revert_label = "元に戻す (追加を取り消し)"
                elif status == 'D':
                    revert_label = "元に戻す (削除を取り消し)"
                else:
                    revert_label = "元に戻す (変更を取り消し)"

                action_revert = QAction(icon("undo"), revert_label, self)
                action_revert.triggered.connect(lambda: self.file_revert_requested.emit(rel_path))
                menu.addAction(action_revert)
                menu.addSeparator()

            # Only show replace/delete for existing files (not deleted)
            if status != 'D':
                action_replace = QAction(icon("file-input"), "ファイルを差し替え...", self)
                action_replace.triggered.connect(lambda: self.file_replace_requested.emit(rel_path))
                menu.addAction(action_replace)

                menu.addSeparator()

                action_delete = QAction(icon("trash", COLORS['danger']), "削除", self)
                action_delete.triggered.connect(lambda: self.file_delete_requested.emit(rel_path))
                menu.addAction(action_delete)

        menu.exec(self.viewport().mapToGlobal(position))

    # Icon name and tint per file type (see FILE_TYPE_MAP)
    _TYPE_ICONS = {
        "xml": ("file-text", COLORS['primary']),
        "rels": ("file", COLORS['text_muted']),
        "image": ("image", COLORS['success']),
    }

    def _get_file_icon(self, is_dir: bool, suffix: str, is_main: bool = False) -> QIcon:
        """Get the appropriate icon for a file or directory.

        Args:
            is_dir: True if this is a directory.
            suffix: File extension (including dot).
            is_main: True for main content files (document.xml, sheet1.xml, ...).

        Returns:
            QIcon for the item.
        """
        if is_dir:
            return icon("folder", COLORS['warning'])
        if is_main:
            return icon("pin", COLORS['primary'])

        file_type = FILE_TYPE_MAP.get(suffix.lower())
        name, color = self._TYPE_ICONS.get(file_type, ("file", COLORS['text_secondary']))
        return icon(name, color)

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

                is_main = not is_dir and is_main_content_file(current_rel)
                item.setText(0, name)
                size_text = format_file_size(size) if not is_dir else ""
                item.setText(1, size_text)
                item.setData(1, self.SIZE_TEXT_ROLE, size_text)
                item.setText(2, self._get_file_type(is_dir, suffix))
                item.setIcon(0, self._get_file_icon(is_dir, suffix, is_main))

                # Bold for main content files
                if is_main:
                    font = item.font(0)
                    font.setBold(True)
                    item.setFont(0, font)
                    item.setToolTip(0, "メインコンテンツファイル")

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

        # Compute size heatmap (must come before _apply_search_visuals)
        self._compute_size_heatmap()

        # Re-apply search highlight/filter if active
        self._apply_search_visuals()

    def _apply_status_to_item(self, item: QTreeWidgetItem, status: str, is_dir: bool):
        """Apply status styling to a tree item.

        Args:
            item: The tree item.
            status: Status string ('M', 'A', 'D', or '').
            is_dir: Whether the item is a directory.
        """
        from PySide6.QtGui import QBrush, QColor, QFont

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

    def _compute_size_heatmap(self):
        """Compute and apply background color on the size column based on file size."""
        from PySide6.QtGui import QBrush, QColor

        self._size_heatmap_brushes = {}
        if not self._workspace_path:
            return

        # Collect file sizes (exclude folders and deleted files)
        sizes: dict[str, int] = {}
        for rel_path, item in self._items_map.items():
            abs_path = self._workspace_path / rel_path
            if not abs_path.exists() or not abs_path.is_file():
                continue
            try:
                size = abs_path.stat().st_size
            except OSError:
                continue
            if size > 0:
                sizes[rel_path] = size

        if not sizes:
            return

        max_size = max(sizes.values())
        # Color gradient: very light blue (small) → medium blue (large)
        # Light: (239, 246, 255) ≈ tailwind blue-50
        # Strong: (96, 165, 250) ≈ tailwind blue-400
        for rel_path, size in sizes.items():
            ratio = size / max_size
            r = int(239 + (96 - 239) * ratio)
            g = int(246 + (165 - 246) * ratio)
            b = int(255 + (250 - 255) * ratio)
            self._size_heatmap_brushes[rel_path] = QBrush(QColor(r, g, b))

    def apply_search(self, matches: set[str], filter_active: bool, match_counts: Optional[dict[str, int]] = None):
        """Apply search results: highlight matched files and optionally hide non-matches.

        Args:
            matches: Set of relative paths (str) that contain the search string.
            filter_active: If True, hide items that do not match (and folders with
                no matching descendants). If False, only highlight.
            match_counts: Optional dict of relative path -> hit count, to display
                next to the file size.
        """
        self._search_matches = set(matches)
        self._search_match_counts = dict(match_counts) if match_counts else {}
        self._search_filter_active = filter_active
        self._apply_search_visuals()

    def clear_search(self):
        """Clear search highlighting and unhide all items."""
        self._search_matches = set()
        self._search_match_counts = {}
        self._search_filter_active = False
        self._apply_search_visuals()

    def _apply_search_visuals(self):
        """Apply highlight color, hit-count text, and visibility based on search state."""
        from PySide6.QtGui import QBrush, QColor

        highlight = QBrush(QColor(self.SEARCH_HIGHLIGHT_COLOR))
        no_brush = QBrush()

        has_search = bool(self._search_matches)

        # First pass: set highlight, hit-count text, and restore size heatmap
        for rel_path, item in self._items_map.items():
            abs_path = self._workspace_path / rel_path if self._workspace_path else None
            is_dir = abs_path.is_dir() if abs_path and abs_path.exists() else False

            is_match = not is_dir and has_search and rel_path in self._search_matches

            if is_match:
                for col in range(self.columnCount()):
                    item.setBackground(col, highlight)
            else:
                for col in range(self.columnCount()):
                    if col == 1 and rel_path in self._size_heatmap_brushes:
                        item.setBackground(col, self._size_heatmap_brushes[rel_path])
                    else:
                        item.setBackground(col, no_brush)

            # Update size column text to include hit count
            if not is_dir:
                size_text = item.data(1, self.SIZE_TEXT_ROLE) or ""
                count = self._search_match_counts.get(rel_path, 0)
                if count > 0:
                    item.setText(1, f"{size_text}  ({count}件)")
                else:
                    item.setText(1, size_text)

        # Second pass: handle visibility for filter mode
        if self._search_filter_active and has_search:
            # Hide items not in matches; un-hide ancestors of matches
            visible_paths: set[str] = set()
            for match in self._search_matches:
                parts = Path(match).parts
                for i in range(len(parts)):
                    visible_paths.add(str(Path(*parts[:i + 1])))

            for rel_path, item in self._items_map.items():
                item.setHidden(rel_path not in visible_paths)
        else:
            # Show all
            for item in self._items_map.values():
                item.setHidden(False)

    def clear_workspace(self):
        """Clear the tree and reset workspace path."""
        self.clear()
        self._workspace_path = None
        self._file_statuses = {}
        self._items_map.clear()
        self._search_matches = set()
        self._search_match_counts = {}
        self._search_filter_active = False
        self._size_heatmap_brushes = {}

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

"""XML editor widget with syntax highlighting, line numbers, and search."""

import re
import xml.dom.minidom
from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt, Signal, QRect, QSize
from PySide6.QtGui import (
    QColor,
    QFont,
    QSyntaxHighlighter,
    QTextCharFormat,
    QTextDocument,
    QKeySequence,
    QShortcut,
    QPainter,
    QTextFormat,
    QTextCursor,
)
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPlainTextEdit,
    QPushButton,
    QLabel,
    QMessageBox,
    QLineEdit,
    QTextEdit,
)

from .icons import icon, icon_label, icon_button
from .styles import SYNTAX_COLORS, LINE_NUMBER_STYLE, COLORS, APP_STYLESHEET


class XmlHighlighter(QSyntaxHighlighter):
    """Simple and fast syntax highlighter for XML content."""

    # Maximum line length to process (longer lines skip highlighting for performance)
    MAX_LINE_LENGTH = 5000

    def __init__(self, document: QTextDocument):
        super().__init__(document)
        self._enabled = True
        self._init_rules()

    def _init_rules(self):
        """Initialize highlighting rules with pre-compiled patterns."""
        self._rules = []

        # Tag name format (modern blue)
        tag_format = QTextCharFormat()
        tag_format.setForeground(QColor(SYNTAX_COLORS['tag']))
        tag_format.setFontWeight(QFont.Weight.Bold)

        # Attribute value format (modern green)
        value_format = QTextCharFormat()
        value_format.setForeground(QColor(SYNTAX_COLORS['value']))

        # Attribute name format (amber)
        attr_format = QTextCharFormat()
        attr_format.setForeground(QColor(SYNTAX_COLORS['attribute']))

        # Comment format (gray)
        comment_format = QTextCharFormat()
        comment_format.setForeground(QColor(SYNTAX_COLORS['comment']))

        # Simple rules - order matters!
        self._rules.append((re.compile(r'<!--.*?-->'), comment_format))
        self._rules.append((re.compile(r'"[^"]*"'), value_format))
        self._rules.append((re.compile(r"'[^']*'"), value_format))
        self._rules.append((re.compile(r'</?[\w:]+'), tag_format))
        self._rules.append((re.compile(r'\b[\w:]+(?=\s*=)'), attr_format))

    def set_enabled(self, enabled: bool):
        """Enable or disable highlighting."""
        self._enabled = enabled
        self.rehighlight()

    def highlightBlock(self, text: str):
        """Highlight a block of text."""
        if not self._enabled:
            return

        # Skip highlighting for very long lines (performance optimization)
        if len(text) > self.MAX_LINE_LENGTH:
            return

        for pattern, fmt in self._rules:
            for match in pattern.finditer(text):
                self.setFormat(match.start(), match.end() - match.start(), fmt)


class LineNumberArea(QWidget):
    """Widget for displaying line numbers."""

    def __init__(self, editor: 'CodeEditor'):
        super().__init__(editor)
        self.editor = editor

    def sizeHint(self) -> QSize:
        return QSize(self.editor.line_number_area_width(), 0)

    def paintEvent(self, event):
        self.editor.line_number_area_paint_event(event)


class CodeEditor(QPlainTextEdit):
    """Plain text editor with line numbers and current line highlighting."""

    # Font size limits
    MIN_FONT_SIZE = 6
    MAX_FONT_SIZE = 72
    DEFAULT_FONT_SIZE = 10

    # Signal emitted when zoom level changes
    zoom_changed = Signal(int)  # Emits new font size

    def __init__(self, parent=None):
        super().__init__(parent)
        self.line_number_area = LineNumberArea(self)
        self._font_size = self.DEFAULT_FONT_SIZE

        # Connect signals for line number updates
        self.blockCountChanged.connect(self.update_line_number_area_width)
        self.updateRequest.connect(self.update_line_number_area)
        self.cursorPositionChanged.connect(self.highlight_current_line)

        self.update_line_number_area_width(0)
        self.highlight_current_line()

        # Set monospace font
        font = QFont("Consolas", self._font_size)
        font.setStyleHint(QFont.StyleHint.Monospace)
        self.setFont(font)

        # Set tab width
        self.setTabStopDistance(40)

        # No line wrap for code
        self.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)

    def line_number_area_width(self) -> int:
        """Calculate width needed for line number area."""
        digits = 1
        max_num = max(1, self.blockCount())
        while max_num >= 10:
            max_num //= 10
            digits += 1

        space = 10 + self.fontMetrics().horizontalAdvance('9') * digits
        return space

    def update_line_number_area_width(self, _):
        """Update the viewport margins to accommodate line numbers."""
        self.setViewportMargins(self.line_number_area_width(), 0, 0, 0)

    def update_line_number_area(self, rect, dy):
        """Update the line number area when scrolling."""
        if dy:
            self.line_number_area.scroll(0, dy)
        else:
            self.line_number_area.update(0, rect.y(), self.line_number_area.width(), rect.height())

        if rect.contains(self.viewport().rect()):
            self.update_line_number_area_width(0)

    def resizeEvent(self, event):
        """Handle resize to update line number area."""
        super().resizeEvent(event)
        cr = self.contentsRect()
        self.line_number_area.setGeometry(QRect(cr.left(), cr.top(),
                                                 self.line_number_area_width(), cr.height()))

    def highlight_current_line(self):
        """Highlight the current line."""
        extra_selections = []

        if not self.isReadOnly():
            selection = QTextEdit.ExtraSelection()
            line_color = QColor(LINE_NUMBER_STYLE['current_line'])
            selection.format.setBackground(line_color)
            selection.format.setProperty(QTextFormat.Property.FullWidthSelection, True)
            selection.cursor = self.textCursor()
            selection.cursor.clearSelection()
            extra_selections.append(selection)

        self.setExtraSelections(extra_selections)

    def line_number_area_paint_event(self, event):
        """Paint the line numbers."""
        painter = QPainter(self.line_number_area)
        painter.fillRect(event.rect(), QColor(LINE_NUMBER_STYLE['background']))

        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        top = int(self.blockBoundingGeometry(block).translated(self.contentOffset()).top())
        bottom = top + int(self.blockBoundingRect(block).height())

        # Current line number
        current_line = self.textCursor().blockNumber()

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(block_number + 1)

                # Highlight current line number
                if block_number == current_line:
                    painter.setPen(QColor(LINE_NUMBER_STYLE['text_current']))
                    font = painter.font()
                    font.setBold(True)
                    painter.setFont(font)
                else:
                    painter.setPen(QColor(LINE_NUMBER_STYLE['text']))
                    font = painter.font()
                    font.setBold(False)
                    painter.setFont(font)

                painter.drawText(0, top, self.line_number_area.width() - 5,
                               self.fontMetrics().height(),
                               Qt.AlignmentFlag.AlignRight, number)

            block = block.next()
            top = bottom
            bottom = top + int(self.blockBoundingRect(block).height())
            block_number += 1

    def goto_line(self, line_number: int):
        """Go to a specific line number."""
        block = self.document().findBlockByLineNumber(line_number - 1)
        if block.isValid():
            cursor = self.textCursor()
            cursor.setPosition(block.position())
            self.setTextCursor(cursor)
            self.centerCursor()

    def wheelEvent(self, event):
        """Handle mouse wheel events for zooming with Ctrl."""
        if event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            delta = event.angleDelta().y()
            if delta > 0:
                self.zoom_in()
            elif delta < 0:
                self.zoom_out()
            event.accept()
        else:
            super().wheelEvent(event)

    def zoom_in(self, increment: int = 1):
        """Increase font size."""
        new_size = min(self._font_size + increment, self.MAX_FONT_SIZE)
        if new_size != self._font_size:
            self._set_font_size(new_size)

    def zoom_out(self, decrement: int = 1):
        """Decrease font size."""
        new_size = max(self._font_size - decrement, self.MIN_FONT_SIZE)
        if new_size != self._font_size:
            self._set_font_size(new_size)

    def zoom_reset(self):
        """Reset font size to default."""
        self._set_font_size(self.DEFAULT_FONT_SIZE)

    def _set_font_size(self, size: int):
        """Set the font size."""
        self._font_size = size
        font = QFont("Consolas", size)
        font.setStyleHint(QFont.StyleHint.Monospace)
        self.setFont(font)
        # Also update document's default font
        self.document().setDefaultFont(font)
        # Update line number area
        self.update_line_number_area_width(0)
        # Emit signal
        self.zoom_changed.emit(size)

    def get_font_size(self) -> int:
        """Get current font size."""
        return self._font_size


class XmlEditorWidget(QWidget):
    """XML editor widget with syntax highlighting and save functionality."""

    content_modified = Signal()
    file_saved = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_file: Optional[Path] = None
        self._original_content: str = ""
        self._is_modified: bool = False
        self._search_matches: list = []
        self._current_match_index: int = -1
        self._is_searching: bool = False  # Prevent recursive search

        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        """Set up the editor UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)

        # Apply stylesheet
        self.setStyleSheet(APP_STYLESHEET)

        # Compact button style for editor toolbar
        toolbar_btn_style = """
            QPushButton {
                padding: 4px 10px;
                min-height: 26px;
                font-size: 12px;
            }
        """

        # Toggle button style (for highlight/wrap)
        toggle_btn_style = """
            QPushButton {
                padding: 4px 8px;
                min-height: 26px;
                font-size: 12px;
                background-color: #F1F5F9;
                border: 1px solid #E2E8F0;
            }
            QPushButton:checked {
                background-color: #DBEAFE;
                border-color: #2563EB;
                color: #2563EB;
            }
            QPushButton:hover {
                background-color: #E2E8F0;
            }
            QPushButton:checked:hover {
                background-color: #BFDBFE;
            }
        """

        # Primary button style for save
        save_btn_style = """
            QPushButton {
                background-color: #2563EB;
                color: white;
                border: none;
                padding: 4px 12px;
                min-height: 26px;
                font-size: 12px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #1D4ED8;
            }
            QPushButton:disabled {
                background-color: #93C5FD;
            }
        """

        # Header with file info and buttons
        header = QHBoxLayout()
        header.setSpacing(6)

        self.file_label = QLabel("ファイルが選択されていません")
        self.file_label.setStyleSheet("font-weight: bold; color: #1E293B;")
        header.addWidget(self.file_label)

        header.addStretch()

        # Syntax highlight toggle (as button)
        self.btn_highlight = QPushButton("色付け")
        self.btn_highlight.setIcon(icon("highlighter"))
        self.btn_highlight.setCheckable(True)
        self.btn_highlight.setChecked(True)
        self.btn_highlight.setStyleSheet(toggle_btn_style)
        self.btn_highlight.setToolTip("シンタックスハイライトの ON/OFF")
        self.btn_highlight.toggled.connect(self._on_highlight_toggled)
        header.addWidget(self.btn_highlight)

        # Word wrap toggle (as button)
        self.btn_wrap = QPushButton("折返し")
        self.btn_wrap.setIcon(icon("wrap-text"))
        self.btn_wrap.setCheckable(True)
        self.btn_wrap.setChecked(False)
        self.btn_wrap.setStyleSheet(toggle_btn_style)
        self.btn_wrap.setToolTip("行の折り返し ON/OFF")
        self.btn_wrap.toggled.connect(self._on_wrap_toggled)
        header.addWidget(self.btn_wrap)

        # Separator
        sep = QLabel("|")
        sep.setStyleSheet("color: #CBD5E1;")
        header.addWidget(sep)

        # Format XML button
        self.btn_format = QPushButton("整形")
        self.btn_format.setIcon(icon("code"))
        self.btn_format.setToolTip("XMLを整形して見やすくする")
        self.btn_format.setStyleSheet(toolbar_btn_style)
        self.btn_format.clicked.connect(self.format_xml)
        header.addWidget(self.btn_format)

        # Search button
        self.btn_search = QPushButton("検索")
        self.btn_search.setIcon(icon("search"))
        self.btn_search.setToolTip("Ctrl+F")
        self.btn_search.setStyleSheet(toolbar_btn_style)
        self.btn_search.clicked.connect(self.toggle_search_bar)
        header.addWidget(self.btn_search)

        # Separator
        sep2 = QLabel("|")
        sep2.setStyleSheet("color: #CBD5E1;")
        header.addWidget(sep2)

        # Zoom buttons
        self.btn_zoom_out = QPushButton("A-")
        self.btn_zoom_out.setToolTip("縮小 (Ctrl+-)")
        self.btn_zoom_out.setStyleSheet(toolbar_btn_style)
        self.btn_zoom_out.setFixedWidth(44)
        self.btn_zoom_out.clicked.connect(self._zoom_out)
        header.addWidget(self.btn_zoom_out)

        self.zoom_label = QLabel("100%")
        self.zoom_label.setFixedWidth(45)
        self.zoom_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.zoom_label.setStyleSheet("color: #64748B; font-size: 11px;")
        self.zoom_label.setToolTip("フォントサイズ (Ctrl+0 でリセット)")
        header.addWidget(self.zoom_label)

        self.btn_zoom_in = QPushButton("A+")
        self.btn_zoom_in.setToolTip("拡大 (Ctrl++)")
        self.btn_zoom_in.setStyleSheet(toolbar_btn_style)
        self.btn_zoom_in.setFixedWidth(44)
        self.btn_zoom_in.clicked.connect(self._zoom_in)
        header.addWidget(self.btn_zoom_in)

        # Separator
        sep3 = QLabel("|")
        sep3.setStyleSheet("color: #CBD5E1;")
        header.addWidget(sep3)

        self.btn_save = QPushButton("保存")
        self.btn_save.setIcon(icon("save", "#FFFFFF", "#DBEAFE"))
        self.btn_save.setToolTip("Ctrl+S")
        self.btn_save.setStyleSheet(save_btn_style)
        self.btn_save.setEnabled(False)
        self.btn_save.clicked.connect(self.save_file)
        header.addWidget(self.btn_save)

        layout.addLayout(header)

        # Search bar (hidden by default)
        self.search_bar = QWidget()
        self.search_bar.setObjectName("searchBar")
        # Scope to the bar itself so child widgets (icon label, buttons) don't inherit the padding
        self.search_bar.setStyleSheet("QWidget#searchBar { background-color: #F1F5F9; border-radius: 6px; padding: 4px; }")
        search_layout = QHBoxLayout(self.search_bar)
        search_layout.setContentsMargins(8, 4, 8, 4)

        search_layout.addWidget(icon_label("search", 16))

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("検索文字列を入力...")
        self.search_input.returnPressed.connect(self.find_next)
        self.search_input.textChanged.connect(self._on_search_text_changed)
        search_layout.addWidget(self.search_input)

        self.search_result_label = QLabel("")
        self.search_result_label.setStyleSheet("background: transparent; color: #64748B;")
        search_layout.addWidget(self.search_result_label)

        self.btn_find_prev = QPushButton("前へ")
        self.btn_find_prev.setIcon(icon("chevron-left"))
        self.btn_find_prev.setStyleSheet(toolbar_btn_style)
        self.btn_find_prev.clicked.connect(self.find_previous)
        search_layout.addWidget(self.btn_find_prev)

        self.btn_find_next = QPushButton("次へ")
        self.btn_find_next.setIcon(icon("chevron-right"))
        self.btn_find_next.setStyleSheet(toolbar_btn_style)
        self.btn_find_next.clicked.connect(self.find_next)
        search_layout.addWidget(self.btn_find_next)

        self.btn_close_search = icon_button("x", "検索バーを閉じる (Esc)")
        self.btn_close_search.clicked.connect(self.hide_search_bar)
        search_layout.addWidget(self.btn_close_search)

        self.search_bar.hide()
        layout.addWidget(self.search_bar)

        # Text editor with line numbers
        self.editor = CodeEditor()
        layout.addWidget(self.editor)

        # Syntax highlighter
        self.highlighter = XmlHighlighter(self.editor.document())
        self.highlighter.set_enabled(True)

        # Keyboard shortcuts
        save_shortcut = QShortcut(QKeySequence.StandardKey.Save, self)
        save_shortcut.activated.connect(self.save_file)

        search_shortcut = QShortcut(QKeySequence.StandardKey.Find, self)
        search_shortcut.activated.connect(self.show_search_bar)

        find_next_shortcut = QShortcut(QKeySequence("F3"), self)
        find_next_shortcut.activated.connect(self.find_next)

        find_prev_shortcut = QShortcut(QKeySequence("Shift+F3"), self)
        find_prev_shortcut.activated.connect(self.find_previous)

        escape_shortcut = QShortcut(QKeySequence("Escape"), self)
        escape_shortcut.activated.connect(self.hide_search_bar)

        # Zoom shortcuts
        zoom_in_shortcut = QShortcut(QKeySequence("Ctrl++"), self)
        zoom_in_shortcut.activated.connect(self._zoom_in)

        zoom_in_shortcut2 = QShortcut(QKeySequence("Ctrl+="), self)
        zoom_in_shortcut2.activated.connect(self._zoom_in)

        zoom_out_shortcut = QShortcut(QKeySequence("Ctrl+-"), self)
        zoom_out_shortcut.activated.connect(self._zoom_out)

        zoom_reset_shortcut = QShortcut(QKeySequence("Ctrl+0"), self)
        zoom_reset_shortcut.activated.connect(self._zoom_reset)

        # Status bar
        status_layout = QHBoxLayout()
        self.line_col_label = QLabel("行: 1, 列: 1")
        status_layout.addWidget(self.line_col_label)
        status_layout.addStretch()
        layout.addLayout(status_layout)

        # Update line/col on cursor move
        self.editor.cursorPositionChanged.connect(self._update_cursor_position)

    def _connect_signals(self):
        """Connect internal signals."""
        self.editor.textChanged.connect(self._on_text_changed)
        self.editor.zoom_changed.connect(self._update_zoom_label)

    # ========== Zoom functionality ==========

    def _zoom_in(self):
        """Zoom in (increase font size)."""
        self.editor.zoom_in()
        self._update_zoom_label()

    def _zoom_out(self):
        """Zoom out (decrease font size)."""
        self.editor.zoom_out()
        self._update_zoom_label()

    def _zoom_reset(self):
        """Reset zoom to default."""
        self.editor.zoom_reset()
        self._update_zoom_label()

    def _update_zoom_label(self, font_size: int = None):
        """Update the zoom percentage label."""
        current_size = font_size if font_size is not None else self.editor.get_font_size()
        default_size = CodeEditor.DEFAULT_FONT_SIZE
        percentage = int(current_size / default_size * 100)
        self.zoom_label.setText(f"{percentage}%")

    def _update_cursor_position(self):
        """Update the line and column display."""
        cursor = self.editor.textCursor()
        line = cursor.blockNumber() + 1
        col = cursor.columnNumber() + 1
        self.line_col_label.setText(f"行: {line}, 列: {col}")

    def _on_highlight_toggled(self, enabled: bool):
        """Handle highlight checkbox toggle."""
        self.highlighter.set_enabled(enabled)

    def _on_wrap_toggled(self, enabled: bool):
        """Handle word wrap checkbox toggle."""
        if enabled:
            self.editor.setLineWrapMode(QPlainTextEdit.LineWrapMode.WidgetWidth)
        else:
            self.editor.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)

    def _on_text_changed(self):
        """Handle text change in the editor."""
        if self._current_file:
            current_content = self.editor.toPlainText()
            self._is_modified = current_content != self._original_content
            self._update_modified_indicator()
            if self._is_modified:
                self.content_modified.emit()

        # Clear search results when text changes (positions become invalid)
        if self._search_matches and not self._is_searching:
            self._search_matches = []
            self._current_match_index = -1

    def _update_modified_indicator(self):
        """Update the modified indicator in the UI."""
        if self._current_file:
            name = self._current_file.name
            if self._is_modified:
                self.file_label.setText(f"{name}  [M]")
                self.file_label.setStyleSheet("font-weight: bold; color: #D97706;")  # Amber for modified
                self.btn_save.setEnabled(True)
            else:
                self.file_label.setText(name)
                self.file_label.setStyleSheet("font-weight: bold; color: #1E293B;")
                self.btn_save.setEnabled(False)
        else:
            self.btn_save.setEnabled(False)

    # ========== Search functionality ==========

    def toggle_search_bar(self):
        """Toggle search bar visibility."""
        # isHidden() reflects the bar's own state even before the editor is shown
        if not self.search_bar.isHidden():
            self.hide_search_bar()
        else:
            self.show_search_bar()

    def show_search_bar(self):
        """Show the search bar and focus input."""
        self.search_bar.show()
        self.search_input.setFocus()
        self.search_input.selectAll()

    def hide_search_bar(self):
        """Hide the search bar."""
        self.search_bar.hide()
        self.editor.setFocus()
        self._clear_search_highlights()

    def _on_search_text_changed(self, text: str):
        """Handle search text changes for live search."""
        # When search text changes, search from current cursor position
        self._find_all(text, from_cursor=True)

    def _find_all(self, text: str, from_cursor: bool = False):
        """Find all occurrences of text.

        Args:
            text: The text to search for.
            from_cursor: If True, start from cursor position. If False, start from beginning.
        """
        self._is_searching = True
        try:
            self._search_matches = []
            self._current_match_index = -1
            self._clear_search_highlights()

            if not text:
                self.search_result_label.setText("")
                return

            content = self.editor.toPlainText()
            start = 0
            while True:
                pos = content.find(text, start)
                if pos == -1:
                    break
                self._search_matches.append(pos)
                start = pos + 1

            if self._search_matches:
                self.search_result_label.setText(f"{len(self._search_matches)} 件")
                self._highlight_search_matches(text)

                # Find the match closest to or after cursor position
                cursor_pos = self.editor.textCursor().position()
                self._current_match_index = 0

                if from_cursor:
                    for i, match_pos in enumerate(self._search_matches):
                        if match_pos >= cursor_pos:
                            self._current_match_index = i
                            break
                    else:
                        # If no match found after cursor, wrap to first match
                        self._current_match_index = 0

                self._goto_match(self._current_match_index)
            else:
                self.search_result_label.setText("0 件")
        finally:
            self._is_searching = False

    def _highlight_search_matches(self, text: str):
        """Highlight all search matches."""
        extra_selections = list(self.editor.extraSelections())

        cursor = self.editor.textCursor()
        highlight_format = QTextCharFormat()
        highlight_format.setBackground(QColor(COLORS['primary_light']))

        for pos in self._search_matches:
            cursor.setPosition(pos)
            cursor.setPosition(pos + len(text), QTextCursor.MoveMode.KeepAnchor)
            selection = QTextEdit.ExtraSelection()
            selection.cursor = cursor
            selection.format = highlight_format
            extra_selections.append(selection)

        self.editor.setExtraSelections(extra_selections)

    def _clear_search_highlights(self):
        """Clear search highlights but keep current line highlight."""
        self.editor.highlight_current_line()

    def _goto_match(self, index: int):
        """Go to a specific match index."""
        if not self._search_matches or index < 0 or index >= len(self._search_matches):
            return

        pos = self._search_matches[index]
        cursor = self.editor.textCursor()
        cursor.setPosition(pos)
        text = self.search_input.text()
        cursor.setPosition(pos + len(text), QTextCursor.MoveMode.KeepAnchor)
        self.editor.setTextCursor(cursor)
        self.editor.centerCursor()

        self.search_result_label.setText(f"{index + 1}/{len(self._search_matches)} 件")

    def find_next(self):
        """Find next occurrence from cursor position."""
        search_text = self.search_input.text()
        if not search_text:
            return

        if not self._search_matches:
            # Initial search - start from cursor position
            self._find_all(search_text, from_cursor=True)
            return

        # Use selection start as the pivot so that the currently-selected match
        # (whose anchor is the match start) is skipped on the next press.
        pivot = self.editor.textCursor().selectionStart()

        for i, match_pos in enumerate(self._search_matches):
            if match_pos > pivot:
                self._current_match_index = i
                self._goto_match(self._current_match_index)
                return

        # Wrap around to beginning
        self._current_match_index = 0
        self._goto_match(self._current_match_index)

    def find_previous(self):
        """Find previous occurrence from cursor position."""
        search_text = self.search_input.text()
        if not search_text:
            return

        if not self._search_matches:
            # Initial search - start from cursor position
            self._find_all(search_text, from_cursor=True)
            return

        # Use selection start as the pivot. After selecting a match, the cursor's
        # position is at the end of the selection, so the previous-match search
        # would otherwise see the current match's start (< end) and stay put.
        pivot = self.editor.textCursor().selectionStart()

        for i in range(len(self._search_matches) - 1, -1, -1):
            if self._search_matches[i] < pivot:
                self._current_match_index = i
                self._goto_match(self._current_match_index)
                return

        # Wrap around to end
        self._current_match_index = len(self._search_matches) - 1
        self._goto_match(self._current_match_index)

    # ========== XML Formatting ==========

    def format_xml(self):
        """Format/pretty-print the XML content."""
        content = self.editor.toPlainText()
        if not content.strip():
            return

        try:
            # Parse the XML
            dom = xml.dom.minidom.parseString(content.encode('utf-8'))

            # Remove existing whitespace-only text nodes to avoid double formatting
            self._remove_whitespace_nodes(dom)

            # Pretty print
            pretty = dom.toprettyxml(indent="  ")

            # Remove extra blank lines and XML declaration if it was added
            lines = pretty.split('\n')
            # Remove XML declaration if original didn't have it
            if not content.strip().startswith('<?xml'):
                if lines and lines[0].startswith('<?xml'):
                    lines = lines[1:]

            # Remove excessive blank lines
            result_lines = []
            prev_blank = False
            for line in lines:
                is_blank = not line.strip()
                if is_blank and prev_blank:
                    continue
                result_lines.append(line)
                prev_blank = is_blank

            formatted = '\n'.join(result_lines).strip()

            # Update editor
            cursor = self.editor.textCursor()
            cursor.select(QTextCursor.SelectionType.Document)
            cursor.insertText(formatted)

        except Exception as e:
            QMessageBox.warning(
                self,
                "整形エラー",
                f"XMLの整形に失敗しました。構文エラーがある可能性があります。\n\n{e}"
            )

    def _remove_whitespace_nodes(self, node):
        """Remove whitespace-only text nodes from the DOM tree."""
        remove_list = []
        for child in node.childNodes:
            if child.nodeType == xml.dom.minidom.Node.TEXT_NODE:
                if not child.data.strip():
                    remove_list.append(child)
            elif child.hasChildNodes():
                self._remove_whitespace_nodes(child)

        for child in remove_list:
            node.removeChild(child)

    def _show_format_suggestion(self):
        """Show a suggestion to format the XML for better performance."""
        from PySide6.QtCore import QTimer

        def show_dialog():
            result = QMessageBox.question(
                self,
                "整形の提案",
                "このファイルは非常に長い行を含んでいます。\n"
                "XMLを整形すると表示が軽くなり、編集しやすくなります。\n\n"
                "今すぐ整形しますか？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes,
            )
            if result == QMessageBox.StandardButton.Yes:
                self.format_xml()

        # Show dialog after a short delay to let the UI settle
        QTimer.singleShot(100, show_dialog)

    # ========== File operations ==========

    def load_file(self, file_path: Path) -> bool:
        """Load a file into the editor."""
        if not file_path.exists():
            return False

        try:
            content = None
            for encoding in ['utf-8', 'utf-8-sig', 'cp932', 'shift_jis', 'latin-1']:
                try:
                    content = file_path.read_text(encoding=encoding)
                    break
                except UnicodeDecodeError:
                    continue

            if content is None:
                return False

            self._current_file = file_path
            self._original_content = content
            self._is_modified = False

            # Check for very long lines (unformatted XML)
            max_line_len = max((len(line) for line in content.split('\n')), default=0)
            has_long_lines = max_line_len > 10000

            # Disable highlighter for large files or files with very long lines
            is_large = len(content) > 100000
            if is_large or has_long_lines:
                self.highlighter.set_enabled(False)
                self.btn_highlight.setChecked(False)

            # Block signals while setting text
            self.editor.blockSignals(True)
            self.highlighter.blockSignals(True)
            self.editor.setPlainText(content)
            self.highlighter.blockSignals(False)
            self.editor.blockSignals(False)

            self.file_label.setText(file_path.name)
            self._update_modified_indicator()

            # Move cursor to beginning
            cursor = self.editor.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.Start)
            self.editor.setTextCursor(cursor)

            # Show suggestion to format if file has very long lines
            if has_long_lines:
                self._show_format_suggestion()

            return True

        except Exception as e:
            print(f"Error loading file: {e}")
            return False

    def save_file(self) -> bool:
        """Save the current file."""
        if not self._current_file:
            return False

        try:
            content = self.editor.toPlainText()
            self._current_file.write_text(content, encoding='utf-8')
            self._original_content = content
            self._is_modified = False
            self._update_modified_indicator()
            self.file_saved.emit(str(self._current_file))
            return True

        except Exception as e:
            QMessageBox.critical(
                self,
                "保存エラー",
                f"ファイルを保存できませんでした:\n{e}"
            )
            return False

    def reload_file(self):
        """Reload the current file from disk."""
        if not self._current_file:
            return

        if self._is_modified:
            result = QMessageBox.question(
                self,
                "確認",
                "変更が失われます。再読み込みしますか？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if result != QMessageBox.StandardButton.Yes:
                return

        self.load_file(self._current_file)

    def clear(self):
        """Clear the editor."""
        self._current_file = None
        self._original_content = ""
        self._is_modified = False
        self.editor.blockSignals(True)
        self.editor.clear()
        self.editor.blockSignals(False)
        self.file_label.setText("ファイルが選択されていません")
        self.file_label.setStyleSheet("font-weight: bold; color: #1E293B;")
        self.btn_save.setEnabled(False)
        self.hide_search_bar()

    def has_unsaved_changes(self) -> bool:
        """Check if there are unsaved changes."""
        return self._is_modified

    def get_current_file(self) -> Optional[Path]:
        """Get the current file path."""
        return self._current_file

    def confirm_discard_changes(self) -> bool:
        """Ask user to confirm discarding unsaved changes."""
        if not self._is_modified:
            return True

        result = QMessageBox.question(
            self,
            "確認",
            f"{self._current_file.name} への変更が保存されていません。\n変更を破棄しますか？",
            QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Discard | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Cancel,
        )

        if result == QMessageBox.StandardButton.Save:
            return self.save_file()
        elif result == QMessageBox.StandardButton.Discard:
            return True
        else:
            return False

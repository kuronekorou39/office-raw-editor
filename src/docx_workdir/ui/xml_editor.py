"""XML editor widget with syntax highlighting, line numbers, and search."""

import re
import xml.dom.minidom
from pathlib import Path
from typing import Optional

from PyQt6.QtCore import Qt, pyqtSignal, QRect, QSize
from PyQt6.QtGui import (
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
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPlainTextEdit,
    QPushButton,
    QLabel,
    QMessageBox,
    QCheckBox,
    QLineEdit,
    QTextEdit,
)


class XmlHighlighter(QSyntaxHighlighter):
    """Simple and fast syntax highlighter for XML content."""

    def __init__(self, document: QTextDocument):
        super().__init__(document)
        self._enabled = True
        self._init_rules()

    def _init_rules(self):
        """Initialize highlighting rules with pre-compiled patterns."""
        self._rules = []

        # Tag name format (blue, bold)
        tag_format = QTextCharFormat()
        tag_format.setForeground(QColor("#0000FF"))
        tag_format.setFontWeight(QFont.Weight.Bold)

        # Attribute value format (green)
        value_format = QTextCharFormat()
        value_format.setForeground(QColor("#008000"))

        # Attribute name format (red)
        attr_format = QTextCharFormat()
        attr_format.setForeground(QColor("#FF0000"))

        # Comment format (gray)
        comment_format = QTextCharFormat()
        comment_format.setForeground(QColor("#808080"))

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

    def __init__(self, parent=None):
        super().__init__(parent)
        self.line_number_area = LineNumberArea(self)

        # Connect signals for line number updates
        self.blockCountChanged.connect(self.update_line_number_area_width)
        self.updateRequest.connect(self.update_line_number_area)
        self.cursorPositionChanged.connect(self.highlight_current_line)

        self.update_line_number_area_width(0)
        self.highlight_current_line()

        # Set monospace font
        font = QFont("Consolas", 10)
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
            line_color = QColor("#FFFACD")  # Light yellow
            selection.format.setBackground(line_color)
            selection.format.setProperty(QTextFormat.Property.FullWidthSelection, True)
            selection.cursor = self.textCursor()
            selection.cursor.clearSelection()
            extra_selections.append(selection)

        self.setExtraSelections(extra_selections)

    def line_number_area_paint_event(self, event):
        """Paint the line numbers."""
        painter = QPainter(self.line_number_area)
        painter.fillRect(event.rect(), QColor("#F0F0F0"))

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
                    painter.setPen(QColor("#000000"))
                    font = painter.font()
                    font.setBold(True)
                    painter.setFont(font)
                else:
                    painter.setPen(QColor("#808080"))
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


class XmlEditorWidget(QWidget):
    """XML editor widget with syntax highlighting and save functionality."""

    content_modified = pyqtSignal()
    file_saved = pyqtSignal(str)

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

        # Header with file info and buttons
        header = QHBoxLayout()

        self.file_label = QLabel("ファイルが選択されていません")
        self.file_label.setStyleSheet("font-weight: bold;")
        header.addWidget(self.file_label)

        header.addStretch()

        self.modified_label = QLabel("")
        self.modified_label.setStyleSheet("color: orange;")
        header.addWidget(self.modified_label)

        # Syntax highlight toggle
        self.chk_highlight = QCheckBox("色付け")
        self.chk_highlight.setChecked(True)
        self.chk_highlight.toggled.connect(self._on_highlight_toggled)
        header.addWidget(self.chk_highlight)

        # Format XML button
        self.btn_format = QPushButton("整形")
        self.btn_format.setToolTip("XMLを整形して見やすくする")
        self.btn_format.clicked.connect(self.format_xml)
        header.addWidget(self.btn_format)

        # Search button
        self.btn_search = QPushButton("検索")
        self.btn_search.setToolTip("Ctrl+F")
        self.btn_search.clicked.connect(self.toggle_search_bar)
        header.addWidget(self.btn_search)

        self.btn_save = QPushButton("保存")
        self.btn_save.setToolTip("Ctrl+S")
        self.btn_save.setEnabled(False)
        self.btn_save.clicked.connect(self.save_file)
        header.addWidget(self.btn_save)

        self.btn_reload = QPushButton("再読込")
        self.btn_reload.setEnabled(False)
        self.btn_reload.clicked.connect(self.reload_file)
        header.addWidget(self.btn_reload)

        layout.addLayout(header)

        # Search bar (hidden by default)
        self.search_bar = QWidget()
        search_layout = QHBoxLayout(self.search_bar)
        search_layout.setContentsMargins(0, 0, 0, 0)

        search_layout.addWidget(QLabel("検索:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("検索文字列を入力...")
        self.search_input.returnPressed.connect(self.find_next)
        self.search_input.textChanged.connect(self._on_search_text_changed)
        search_layout.addWidget(self.search_input)

        self.search_result_label = QLabel("")
        search_layout.addWidget(self.search_result_label)

        self.btn_find_prev = QPushButton("前へ")
        self.btn_find_prev.clicked.connect(self.find_previous)
        search_layout.addWidget(self.btn_find_prev)

        self.btn_find_next = QPushButton("次へ")
        self.btn_find_next.clicked.connect(self.find_next)
        search_layout.addWidget(self.btn_find_next)

        self.btn_close_search = QPushButton("×")
        self.btn_close_search.setFixedWidth(30)
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

    def _update_cursor_position(self):
        """Update the line and column display."""
        cursor = self.editor.textCursor()
        line = cursor.blockNumber() + 1
        col = cursor.columnNumber() + 1
        self.line_col_label.setText(f"行: {line}, 列: {col}")

    def _on_highlight_toggled(self, enabled: bool):
        """Handle highlight checkbox toggle."""
        self.highlighter.set_enabled(enabled)

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
        if self._is_modified:
            self.modified_label.setText("変更あり")
            self.btn_save.setEnabled(True)
        else:
            self.modified_label.setText("")
            self.btn_save.setEnabled(False)

    # ========== Search functionality ==========

    def toggle_search_bar(self):
        """Toggle search bar visibility."""
        if self.search_bar.isVisible():
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
        self._find_all(text)

    def _find_all(self, text: str):
        """Find all occurrences of text."""
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
                self._current_match_index = 0
                self._goto_match(0)
            else:
                self.search_result_label.setText("0 件")
        finally:
            self._is_searching = False

    def _highlight_search_matches(self, text: str):
        """Highlight all search matches."""
        extra_selections = list(self.editor.extraSelections())

        cursor = self.editor.textCursor()
        highlight_format = QTextCharFormat()
        highlight_format.setBackground(QColor("#FFFF00"))  # Yellow

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
        """Find next occurrence."""
        if not self._search_matches:
            self._find_all(self.search_input.text())
            return

        if self._search_matches:
            self._current_match_index = (self._current_match_index + 1) % len(self._search_matches)
            self._goto_match(self._current_match_index)

    def find_previous(self):
        """Find previous occurrence."""
        if not self._search_matches:
            self._find_all(self.search_input.text())
            return

        if self._search_matches:
            self._current_match_index = (self._current_match_index - 1) % len(self._search_matches)
            self._goto_match(self._current_match_index)

    # ========== XML Formatting ==========

    def format_xml(self):
        """Format/pretty-print the XML content."""
        content = self.editor.toPlainText()
        if not content.strip():
            return

        try:
            # Parse and pretty print
            dom = xml.dom.minidom.parseString(content.encode('utf-8'))
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

            self._set_status("XMLを整形しました")

        except Exception as e:
            QMessageBox.warning(
                self,
                "整形エラー",
                f"XMLの整形に失敗しました。構文エラーがある可能性があります。\n\n{e}"
            )

    def _set_status(self, message: str):
        """Set a temporary status message."""
        # Could be expanded to show in status bar
        pass

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

            # Disable highlighter for large files
            is_large = len(content) > 100000
            if is_large:
                self.highlighter.set_enabled(False)
                self.chk_highlight.setChecked(False)

            # Block signals while setting text
            self.editor.blockSignals(True)
            self.highlighter.blockSignals(True)
            self.editor.setPlainText(content)
            self.highlighter.blockSignals(False)
            self.editor.blockSignals(False)

            self.file_label.setText(file_path.name)
            self.btn_reload.setEnabled(True)
            self._update_modified_indicator()

            # Move cursor to beginning
            cursor = self.editor.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.Start)
            self.editor.setTextCursor(cursor)

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
        self.btn_save.setEnabled(False)
        self.btn_reload.setEnabled(False)
        self.modified_label.setText("")
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

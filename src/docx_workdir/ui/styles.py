"""Modern styles for docx-workdir application."""

# Color palette
COLORS = {
    'primary': '#2563EB',        # Blue
    'primary_hover': '#1D4ED8',
    'primary_light': '#DBEAFE',
    'success': '#10B981',        # Green
    'warning': '#F59E0B',        # Orange
    'danger': '#EF4444',         # Red
    'background': '#FFFFFF',
    'surface': '#F8FAFC',
    'border': '#E2E8F0',
    'text': '#1E293B',
    'text_secondary': '#64748B',
    'text_muted': '#94A3B8',
}

# Main application stylesheet
APP_STYLESHEET = """
/* ===== Global ===== */
QMainWindow {
    background-color: #F8FAFC;
}

QWidget {
    font-family: "Segoe UI", "Yu Gothic UI", "Meiryo", sans-serif;
    font-size: 13px;
    color: #1E293B;
}

/* ===== Menu Bar ===== */
QMenuBar {
    background-color: #FFFFFF;
    border-bottom: 1px solid #E2E8F0;
    padding: 4px 8px;
}

QMenuBar::item {
    padding: 6px 12px;
    border-radius: 4px;
    margin: 2px;
}

QMenuBar::item:selected {
    background-color: #DBEAFE;
}

QMenu {
    background-color: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 8px;
    padding: 4px;
}

QMenu::item {
    padding: 8px 32px 8px 16px;
    border-radius: 4px;
    margin: 2px;
}

QMenu::item:selected {
    background-color: #DBEAFE;
}

QMenu::separator {
    height: 1px;
    background-color: #E2E8F0;
    margin: 4px 8px;
}

/* ===== Tool Bar ===== */
QToolBar {
    background-color: #FFFFFF;
    border-bottom: 1px solid #E2E8F0;
    padding: 8px 12px;
    spacing: 8px;
}

QToolBar::separator {
    width: 1px;
    background-color: #E2E8F0;
    margin: 4px 8px;
}

/* ===== Buttons ===== */
QPushButton {
    background-color: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 6px;
    padding: 8px 16px;
    font-weight: 500;
    min-height: 20px;
}

QPushButton:hover {
    background-color: #F1F5F9;
    border-color: #CBD5E1;
}

QPushButton:pressed {
    background-color: #E2E8F0;
}

QPushButton:disabled {
    background-color: #F8FAFC;
    color: #94A3B8;
    border-color: #E2E8F0;
}

/* Primary button style */
QPushButton[primary="true"] {
    background-color: #2563EB;
    color: white;
    border: none;
}

QPushButton[primary="true"]:hover {
    background-color: #1D4ED8;
}

QPushButton[primary="true"]:pressed {
    background-color: #1E40AF;
}

/* ===== Tree View ===== */
QTreeWidget, QTreeView {
    background-color: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 8px;
    padding: 4px;
    outline: none;
}

QTreeWidget::item, QTreeView::item {
    padding: 6px 8px;
    border-radius: 4px;
    margin: 1px 0;
}

QTreeWidget::item:hover, QTreeView::item:hover {
    background-color: #F1F5F9;
}

QTreeWidget::item:selected, QTreeView::item:selected {
    background-color: #DBEAFE;
    color: #1E293B;
}

QTreeWidget::branch:has-children:!has-siblings:closed,
QTreeWidget::branch:closed:has-children:has-siblings {
    image: url(none);
    border-image: none;
}

QHeaderView::section {
    background-color: #F8FAFC;
    border: none;
    border-bottom: 1px solid #E2E8F0;
    padding: 8px 12px;
    font-weight: 600;
    color: #64748B;
}

/* ===== Tab Widget ===== */
QTabWidget::pane {
    border: 1px solid #E2E8F0;
    border-radius: 8px;
    background-color: #FFFFFF;
    top: -1px;
}

QTabBar::tab {
    background-color: #F8FAFC;
    border: 1px solid #E2E8F0;
    border-bottom: none;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    padding: 10px 20px;
    margin-right: 2px;
    font-weight: 500;
}

QTabBar::tab:selected {
    background-color: #FFFFFF;
    border-bottom: 2px solid #2563EB;
    color: #2563EB;
}

QTabBar::tab:hover:!selected {
    background-color: #F1F5F9;
}

/* ===== Text Edit / Plain Text Edit ===== */
QPlainTextEdit, QTextEdit {
    background-color: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 8px;
    padding: 8px;
    selection-background-color: #DBEAFE;
    selection-color: #1E293B;
}

QPlainTextEdit:focus, QTextEdit:focus {
    border-color: #2563EB;
}

/* ===== Line Edit ===== */
QLineEdit {
    background-color: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 6px;
    padding: 8px 12px;
    selection-background-color: #DBEAFE;
}

QLineEdit:focus {
    border-color: #2563EB;
}

QLineEdit:disabled {
    background-color: #F8FAFC;
    color: #94A3B8;
}

/* ===== Check Box ===== */
QCheckBox {
    spacing: 8px;
}

QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border-radius: 4px;
    border: 2px solid #CBD5E1;
    background-color: #FFFFFF;
}

QCheckBox::indicator:hover {
    border-color: #2563EB;
}

QCheckBox::indicator:checked {
    background-color: #2563EB;
    border-color: #2563EB;
}

/* ===== Scroll Bar ===== */
QScrollBar:vertical {
    background-color: #F8FAFC;
    width: 12px;
    border-radius: 6px;
    margin: 0;
}

QScrollBar::handle:vertical {
    background-color: #CBD5E1;
    border-radius: 6px;
    min-height: 30px;
    margin: 2px;
}

QScrollBar::handle:vertical:hover {
    background-color: #94A3B8;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}

QScrollBar:horizontal {
    background-color: #F8FAFC;
    height: 12px;
    border-radius: 6px;
    margin: 0;
}

QScrollBar::handle:horizontal {
    background-color: #CBD5E1;
    border-radius: 6px;
    min-width: 30px;
    margin: 2px;
}

QScrollBar::handle:horizontal:hover {
    background-color: #94A3B8;
}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0;
}

/* ===== Status Bar ===== */
QStatusBar {
    background-color: #F8FAFC;
    border-top: 1px solid #E2E8F0;
    padding: 4px 12px;
}

QStatusBar::item {
    border: none;
}

/* ===== Splitter ===== */
QSplitter::handle {
    background-color: #E2E8F0;
}

QSplitter::handle:horizontal {
    width: 2px;
}

QSplitter::handle:vertical {
    height: 2px;
}

QSplitter::handle:hover {
    background-color: #2563EB;
}

/* ===== Group Box ===== */
QGroupBox {
    font-weight: 600;
    border: 1px solid #E2E8F0;
    border-radius: 8px;
    margin-top: 12px;
    padding-top: 12px;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 8px;
    color: #64748B;
}

/* ===== Dialog ===== */
QDialog {
    background-color: #FFFFFF;
}

QDialogButtonBox QPushButton {
    min-width: 80px;
}

/* ===== Message Box ===== */
QMessageBox {
    background-color: #FFFFFF;
}

/* ===== Labels ===== */
QLabel {
    color: #1E293B;
}

QLabel[heading="true"] {
    font-size: 16px;
    font-weight: 600;
}

QLabel[subheading="true"] {
    color: #64748B;
    font-size: 12px;
}

QLabel[muted="true"] {
    color: #94A3B8;
}
"""

# Toolbar button specific style
TOOLBAR_BUTTON_STYLE = """
QPushButton {
    background-color: transparent;
    border: none;
    border-radius: 6px;
    padding: 8px 12px;
    font-weight: 500;
}

QPushButton:hover {
    background-color: #F1F5F9;
}

QPushButton:pressed {
    background-color: #E2E8F0;
}

QPushButton:disabled {
    color: #94A3B8;
}
"""

# Primary action button style
PRIMARY_BUTTON_STYLE = """
QPushButton {
    background-color: #2563EB;
    color: white;
    border: none;
    border-radius: 6px;
    padding: 8px 16px;
    font-weight: 600;
}

QPushButton:hover {
    background-color: #1D4ED8;
}

QPushButton:pressed {
    background-color: #1E40AF;
}

QPushButton:disabled {
    background-color: #93C5FD;
}
"""

# Danger button style (for delete, etc.)
DANGER_BUTTON_STYLE = """
QPushButton {
    background-color: #FEE2E2;
    color: #DC2626;
    border: 1px solid #FECACA;
    border-radius: 6px;
    padding: 8px 16px;
    font-weight: 500;
}

QPushButton:hover {
    background-color: #FCA5A5;
    color: #FFFFFF;
    border-color: #F87171;
}
"""

# Search bar style
SEARCH_BAR_STYLE = """
QWidget {
    background-color: #F1F5F9;
    border-radius: 6px;
    padding: 4px;
}

QLineEdit {
    background-color: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 4px;
    padding: 6px 10px;
}

QLineEdit:focus {
    border-color: #2563EB;
}

QPushButton {
    background-color: transparent;
    border: none;
    padding: 6px 10px;
    border-radius: 4px;
}

QPushButton:hover {
    background-color: #E2E8F0;
}
"""

# Editor line number area style
LINE_NUMBER_STYLE = {
    'background': '#F8FAFC',
    'text': '#94A3B8',
    'text_current': '#1E293B',
    'current_line': '#FEF3C7',  # Light yellow for current line
}

# Syntax highlighting colors (more modern)
SYNTAX_COLORS = {
    'tag': '#2563EB',           # Blue
    'attribute': '#D97706',      # Amber
    'value': '#059669',          # Green
    'comment': '#94A3B8',        # Gray
    'text': '#1E293B',           # Dark
}

"""Constants for office-raw-editor application."""

import re
from pathlib import Path

# Application info
APP_NAME = "office-raw-editor"
APP_VERSION = "0.2.0"
APP_TITLE = f"{APP_NAME} v{APP_VERSION}"

# File extensions - Office Open XML formats
DOCX_EXTENSION = ".docx"
XLSX_EXTENSION = ".xlsx"
PPTX_EXTENSION = ".pptx"

# All supported extensions
SUPPORTED_EXTENSIONS = {
    # Word
    ".docx",  # Word文書
    ".docm",  # Wordマクロ有効文書
    ".dotx",  # Wordテンプレート
    ".dotm",  # Wordマクロ有効テンプレート
    # Excel
    ".xlsx",  # Excelワークブック
    ".xlsm",  # Excelマクロ有効ワークブック
    ".xltx",  # Excelテンプレート
    ".xltm",  # Excelマクロ有効テンプレート
    # PowerPoint
    ".pptx",  # PowerPointプレゼンテーション
    ".pptm",  # PowerPointマクロ有効プレゼンテーション
    ".potx",  # PowerPointテンプレート
    ".potm",  # PowerPointマクロ有効テンプレート
    ".ppsx",  # PowerPointスライドショー
    ".ppsm",  # PowerPointマクロ有効スライドショー
}

BACKUP_SUFFIX = ".backup"

# Workspace settings
WORKDIR_PREFIX = "workdir_"
TEMP_PREFIX = "temp_"

# Important Office Open XML internal files
CONTENT_TYPES_XML = "[Content_Types].xml"
RELS_DIR = "_rels"

# Format-specific main content directories
WORD_DIR = "word"
EXCEL_DIR = "xl"
POWERPOINT_DIR = "ppt"

# File types for tree icons
FOLDER_ICON = "folder"
XML_ICON = "xml"
RELS_ICON = "rels"
IMAGE_ICON = "image"
BINARY_ICON = "binary"
UNKNOWN_ICON = "unknown"

# File type mappings
FILE_TYPE_MAP = {
    ".xml": XML_ICON,
    ".rels": RELS_ICON,
    ".png": IMAGE_ICON,
    ".jpg": IMAGE_ICON,
    ".jpeg": IMAGE_ICON,
    ".gif": IMAGE_ICON,
    ".bmp": IMAGE_ICON,
    ".emf": IMAGE_ICON,
    ".wmf": IMAGE_ICON,
}

# Image file extensions (for preview)
IMAGE_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.ico'}

# Window settings
DEFAULT_WINDOW_WIDTH = 800
DEFAULT_WINDOW_HEIGHT = 600
MIN_WINDOW_WIDTH = 400
MIN_WINDOW_HEIGHT = 300

# Tree view settings
TREE_COLUMN_NAME = "Name"
TREE_COLUMN_SIZE = "Size"
TREE_COLUMN_TYPE = "Type"

# Messages
MSG_CONFIRM_OVERWRITE = "ファイルが既に存在します。上書きしますか？"
MSG_CONFIRM_EXIT = "未保存の変更があります。終了しますか？"
MSG_BACKUP_CREATED = "バックアップを作成しました: {}"
MSG_EXTRACT_SUCCESS = "ファイルを展開しました: {}"
MSG_REPACKAGE_SUCCESS = "再パッケージしました: {}"
MSG_ERROR_OPEN = "ファイルを開けませんでした: {}"
MSG_ERROR_SAVE = "保存に失敗しました: {}"
MSG_ERROR_EXTRACT = "展開に失敗しました: {}"
MSG_ERROR_REPACKAGE = "再パッケージに失敗しました: {}"

# Dialog titles
DIALOG_TITLE_OPEN = "ファイルを開く"
DIALOG_TITLE_SAVE = "名前を付けて保存"
DIALOG_TITLE_CONFIRM = "確認"
DIALOG_TITLE_ERROR = "エラー"
DIALOG_TITLE_WARNING = "警告"

# File filters
FILE_FILTER_DOCX = "Word (*.docx *.docm *.dotx *.dotm)"
FILE_FILTER_XLSX = "Excel (*.xlsx *.xlsm *.xltx *.xltm)"
FILE_FILTER_PPTX = "PowerPoint (*.pptx *.pptm *.potx *.potm *.ppsx *.ppsm)"
FILE_FILTER_OFFICE = "Office Files (*.docx *.docm *.dotx *.dotm *.xlsx *.xlsm *.xltx *.xltm *.pptx *.pptm *.potx *.potm *.ppsx *.ppsm)"
FILE_FILTER_ALL = "All Files (*.*)"


# Utility functions
# Main content files in Office Open XML packages.
# These are the files users most frequently edit (the actual document body).
_MAIN_CONTENT_PATTERNS = (
    re.compile(r'^word/document\d*\.xml$'),
    re.compile(r'^xl/workbook\.xml$'),
    re.compile(r'^xl/worksheets/sheet\d+\.xml$'),
    re.compile(r'^ppt/presentation\.xml$'),
    re.compile(r'^ppt/slides/slide\d+\.xml$'),
)

# Marker prefix prepended to main content file names in the tree
MAIN_CONTENT_MARKER = "📌 "


def is_main_content_file(rel_path: str) -> bool:
    """Return True if the relative path is a 'main content' file.

    Accepts both forward-slash and backslash separators.
    """
    normalized = rel_path.replace('\\', '/').lower()
    return any(p.match(normalized) for p in _MAIN_CONTENT_PATTERNS)


def format_file_size(size: int) -> str:
    """Format file size for display.

    Args:
        size: File size in bytes.

    Returns:
        Formatted size string (e.g., "1.5 KB", "2.3 MB").
    """
    if size < 1024:
        return f"{size} B"
    elif size < 1024 * 1024:
        return f"{size / 1024:.1f} KB"
    else:
        return f"{size / (1024 * 1024):.1f} MB"

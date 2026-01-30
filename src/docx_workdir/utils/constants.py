"""Constants for docx-workdir application."""

from pathlib import Path

# Application info
APP_NAME = "docx-workdir"
APP_VERSION = "0.1.0"
APP_TITLE = f"{APP_NAME} v{APP_VERSION}"

# File extensions
DOCX_EXTENSION = ".docx"
XLSX_EXTENSION = ".xlsx"
SUPPORTED_EXTENSIONS = {".docx", ".xlsx"}
BACKUP_SUFFIX = ".backup"

# Workspace settings
WORKDIR_PREFIX = "workdir_"
TEMP_PREFIX = "temp_"

# Important Office Open XML internal files
CONTENT_TYPES_XML = "[Content_Types].xml"

# DOCX specific
DOCX_CONTENT_TYPES = "[Content_Types].xml"
DOCX_RELS_DIR = "_rels"
DOCX_WORD_DIR = "word"
DOCX_DOCUMENT_XML = "word/document.xml"

# XLSX specific
XLSX_RELS_DIR = "_rels"
XLSX_XL_DIR = "xl"
XLSX_WORKBOOK_XML = "xl/workbook.xml"
XLSX_WORKSHEETS_DIR = "xl/worksheets"

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
FILE_FILTER_DOCX = "Word Documents (*.docx)"
FILE_FILTER_XLSX = "Excel Workbooks (*.xlsx)"
FILE_FILTER_OFFICE = "Office Files (*.docx *.xlsx)"
FILE_FILTER_ALL = "All Files (*.*)"


# Utility functions
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

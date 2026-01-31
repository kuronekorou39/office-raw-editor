"""Core functionality for office-raw-editor."""

from .docx_handler import OfficeFileHandler
from .backup import BackupManager
from .workspace import WorkspaceManager

__all__ = ["OfficeFileHandler", "BackupManager", "WorkspaceManager"]

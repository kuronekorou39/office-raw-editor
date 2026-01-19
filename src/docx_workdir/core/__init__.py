"""Core functionality for docx-workdir."""

from .docx_handler import DocxHandler
from .backup import BackupManager
from .workspace import WorkspaceManager

__all__ = ["DocxHandler", "BackupManager", "WorkspaceManager"]

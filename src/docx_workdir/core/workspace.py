"""Workspace management for Office Open XML file editing.

Supports Word (.docx), Excel (.xlsx), PowerPoint (.pptx) and their variants.
"""

import hashlib
import shutil
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Optional

from ..utils.constants import WORKDIR_PREFIX
from .docx_handler import OfficeFileHandler
from .backup import BackupManager


class WorkspaceManager:
    """Manages the workspace for editing Office Open XML files."""

    def __init__(self, base_dir: Optional[Path] = None):
        """Initialize the WorkspaceManager.

        Args:
            base_dir: Base directory for workspaces.
                     If None, uses the system temp directory.
        """
        if base_dir:
            self.base_dir = base_dir
        else:
            self.base_dir = Path(tempfile.gettempdir()) / "office_raw_editor"

        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.file_handler = OfficeFileHandler()
        self.backup_manager = BackupManager()

        self._current_workspace: Optional[Path] = None
        self._source_file: Optional[Path] = None
        self._is_modified: bool = False
        self._file_hashes: dict[str, str] = {}

    @property
    def current_workspace(self) -> Optional[Path]:
        """Get the current workspace directory."""
        return self._current_workspace

    @property
    def source_file(self) -> Optional[Path]:
        """Get the source file path."""
        return self._source_file

    # Alias for backward compatibility
    @property
    def source_docx(self) -> Optional[Path]:
        """Get the source file path (alias for source_file)."""
        return self._source_file

    @property
    def is_modified(self) -> bool:
        """Check if the workspace has been modified."""
        return self._is_modified

    @is_modified.setter
    def is_modified(self, value: bool):
        """Set the modified state."""
        self._is_modified = value

    def _generate_workspace_name(self, file_path: Path) -> str:
        """Generate a unique workspace name based on the file.

        Args:
            file_path: Path to the file.

        Returns:
            Unique workspace directory name.
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{WORKDIR_PREFIX}{file_path.stem}_{timestamp}"

    def _compute_file_hash(self, file_path: Path) -> str:
        """Compute MD5 hash of a file.

        Args:
            file_path: Path to the file.

        Returns:
            MD5 hash string.
        """
        hasher = hashlib.md5()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                hasher.update(chunk)
        return hasher.hexdigest()

    def _snapshot_hashes(self) -> dict[str, str]:
        """Create a snapshot of file hashes in the workspace.

        Returns:
            Dictionary mapping relative paths to their hashes.
        """
        if not self._current_workspace:
            return {}

        hashes = {}
        for file_path in self._current_workspace.rglob('*'):
            if file_path.is_file():
                rel_path = str(file_path.relative_to(self._current_workspace))
                hashes[rel_path] = self._compute_file_hash(file_path)
        return hashes

    def check_modifications(self) -> bool:
        """Check if any files have been modified since extraction.

        Returns:
            True if modifications are detected.
        """
        if not self._current_workspace:
            return False

        current_hashes = self._snapshot_hashes()

        # Check for modified or new files
        for path, hash_val in current_hashes.items():
            if path not in self._file_hashes or self._file_hashes[path] != hash_val:
                self._is_modified = True
                return True

        # Check for deleted files
        for path in self._file_hashes:
            if path not in current_hashes:
                self._is_modified = True
                return True

        return False

    def get_file_statuses(self) -> dict[str, str]:
        """Get the status of each file in the workspace.

        Returns:
            Dictionary mapping relative paths to status:
            - 'M': Modified
            - 'A': Added (new file)
            - 'D': Deleted
            - '': Unchanged
        """
        if not self._current_workspace:
            return {}

        statuses = {}
        current_hashes = self._snapshot_hashes()

        # Check for modified or added files
        for path, hash_val in current_hashes.items():
            if path not in self._file_hashes:
                statuses[path] = 'A'
            elif self._file_hashes[path] != hash_val:
                statuses[path] = 'M'

        # Check for deleted files
        for path in self._file_hashes:
            if path not in current_hashes:
                statuses[path] = 'D'

        return statuses

    def open_file(self, file_path: Path, create_backup: bool = True) -> Path:
        """Open an Office file and extract it to a workspace.

        Args:
            file_path: Path to the Office file.
            create_backup: If True, create a backup before extraction.

        Returns:
            Path to the workspace directory.

        Raises:
            FileNotFoundError: If the file doesn't exist.
            ValueError: If the file is not a valid Office file.
        """
        file_path = file_path.resolve()

        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        if not OfficeFileHandler.is_valid_file(file_path):
            raise ValueError(f"Invalid Office file: {file_path}")

        # Close any existing workspace
        if self._current_workspace:
            self.close()

        # Create backup
        if create_backup:
            self.backup_manager.create_backup(file_path)

        # Create workspace
        workspace_name = self._generate_workspace_name(file_path)
        workspace_path = self.base_dir / workspace_name
        workspace_path.mkdir(parents=True, exist_ok=True)

        # Extract file
        OfficeFileHandler.extract(file_path, workspace_path)

        self._current_workspace = workspace_path
        self._source_file = file_path
        self._is_modified = False
        self._file_hashes = self._snapshot_hashes()

        return workspace_path

    # Alias for backward compatibility
    def open_docx(self, file_path: Path, create_backup: bool = True) -> Path:
        """Open an Office file (alias for open_file)."""
        return self.open_file(file_path, create_backup)

    def save_as(self, output_path: Path, overwrite: bool = False) -> Path:
        """Save the workspace as a new file.

        Args:
            output_path: Path for the output file.
            overwrite: If True, allow overwriting existing files.

        Returns:
            Path to the saved file.

        Raises:
            RuntimeError: If no workspace is open.
            FileExistsError: If file exists and overwrite is False.
        """
        if not self._current_workspace:
            raise RuntimeError("No workspace is open")

        output_path = output_path.resolve()

        if output_path.exists() and not overwrite:
            raise FileExistsError(f"File already exists: {output_path}")

        OfficeFileHandler.repackage(self._current_workspace, output_path)
        self._is_modified = False
        self._file_hashes = self._snapshot_hashes()

        return output_path

    def save(self) -> Path:
        """Save changes back to the original file.

        Returns:
            Path to the saved file.

        Raises:
            RuntimeError: If no workspace is open or no source file.
        """
        if not self._source_file:
            raise RuntimeError("No source file to save to")

        return self.save_as(self._source_file, overwrite=True)

    def close(self) -> None:
        """Close the current workspace and clean up."""
        if self._current_workspace and self._current_workspace.exists():
            try:
                shutil.rmtree(self._current_workspace)
            except (PermissionError, OSError):
                pass

        self._current_workspace = None
        self._source_file = None
        self._is_modified = False
        self._file_hashes = {}

    def get_file_tree(self) -> list[dict]:
        """Get the file tree structure of the workspace.

        Returns:
            List of file/directory entries with path, name, type, and size.
        """
        if not self._current_workspace:
            return []

        entries = []
        for path in sorted(self._current_workspace.rglob('*')):
            rel_path = path.relative_to(self._current_workspace)
            entry = {
                'path': str(rel_path),
                'name': path.name,
                'is_dir': path.is_dir(),
                'size': path.stat().st_size if path.is_file() else 0,
            }
            entries.append(entry)

        return entries

    def get_absolute_path(self, relative_path: str) -> Optional[Path]:
        """Convert a relative path to absolute path in the workspace.

        Args:
            relative_path: Path relative to workspace root.

        Returns:
            Absolute path, or None if workspace is not open.
        """
        if not self._current_workspace:
            return None
        return self._current_workspace / relative_path

    def revert_file(self, relative_path: str) -> bool:
        """Revert a file to its original state from the source file.

        Args:
            relative_path: Path relative to workspace root.

        Returns:
            True if revert was successful.

        Raises:
            RuntimeError: If no workspace or source file is open.
            ValueError: If the file cannot be reverted.
        """
        if not self._current_workspace or not self._source_file:
            raise RuntimeError("No workspace or source file is open")

        # Normalize path separators for zip (always use forward slash)
        zip_path = relative_path.replace('\\', '/')
        abs_path = self._current_workspace / relative_path

        status = self.get_file_statuses().get(relative_path, '')

        if status == 'A':
            # Added file - just delete it
            if abs_path.exists():
                abs_path.unlink()
            return True

        elif status in ('M', 'D'):
            # Modified or Deleted - restore from original file
            try:
                content = OfficeFileHandler.read_file(self._source_file, zip_path)
                abs_path.parent.mkdir(parents=True, exist_ok=True)
                abs_path.write_bytes(content)
                return True
            except KeyError:
                raise ValueError(f"File not found in original: {relative_path}")

        return False

    def can_revert_file(self, relative_path: str) -> bool:
        """Check if a file can be reverted.

        Args:
            relative_path: Path relative to workspace root.

        Returns:
            True if the file has changes that can be reverted.
        """
        status = self.get_file_statuses().get(relative_path, '')
        return status in ('M', 'A', 'D')

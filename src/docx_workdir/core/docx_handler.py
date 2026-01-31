"""Handler for Office Open XML file operations (ZIP extraction and repackaging).

Supports Word (.docx), Excel (.xlsx), PowerPoint (.pptx) and their variants.
"""

import zipfile
from pathlib import Path

from ..utils.constants import SUPPORTED_EXTENSIONS


class OfficeFileHandler:
    """Handles extraction and repackaging of Office Open XML files."""

    @staticmethod
    def is_supported_extension(file_path: Path) -> bool:
        """Check if a file has a supported extension.

        Args:
            file_path: Path to the file to check.

        Returns:
            True if the file extension is supported.
        """
        return file_path.suffix.lower() in SUPPORTED_EXTENSIONS

    @staticmethod
    def is_valid_file(file_path: Path) -> bool:
        """Check if a file is a valid Office Open XML file.

        Supports Word (.docx, .docm, .dotx, .dotm),
        Excel (.xlsx, .xlsm, .xltx, .xltm),
        PowerPoint (.pptx, .pptm, .potx, .potm, .ppsx, .ppsm).

        Args:
            file_path: Path to the file to check.

        Returns:
            True if the file is a valid Office Open XML file.
        """
        if not file_path.exists():
            return False

        suffix = file_path.suffix.lower()
        if suffix not in SUPPORTED_EXTENSIONS:
            return False

        try:
            with zipfile.ZipFile(file_path, 'r') as zf:
                # All Office Open XML files must have [Content_Types].xml
                return "[Content_Types].xml" in zf.namelist()
        except (zipfile.BadZipFile, Exception):
            return False

    @staticmethod
    def extract(file_path: Path, output_dir: Path) -> bool:
        """Extract an Office file to a directory.

        Args:
            file_path: Path to the Office file.
            output_dir: Directory to extract contents to.

        Returns:
            True if extraction was successful.

        Raises:
            FileNotFoundError: If the file doesn't exist.
            zipfile.BadZipFile: If the file is not a valid ZIP.
            PermissionError: If permission denied.
        """
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        output_dir.mkdir(parents=True, exist_ok=True)

        with zipfile.ZipFile(file_path, 'r') as zf:
            zf.extractall(output_dir)

        return True

    @staticmethod
    def repackage(source_dir: Path, output_path: Path) -> bool:
        """Repackage a directory into an Office file.

        Args:
            source_dir: Directory containing the extracted contents.
            output_path: Path for the output file.

        Returns:
            True if repackaging was successful.

        Raises:
            FileNotFoundError: If the source directory doesn't exist.
            ValueError: If the source directory doesn't contain valid structure.
            PermissionError: If permission denied.
        """
        if not source_dir.exists():
            raise FileNotFoundError(f"Directory not found: {source_dir}")

        # Verify essential files exist
        content_types = source_dir / "[Content_Types].xml"
        if not content_types.exists():
            raise ValueError("Invalid Office file structure: missing [Content_Types].xml")

        # Create parent directory if needed
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            for file_path in source_dir.rglob('*'):
                if file_path.is_file():
                    arcname = file_path.relative_to(source_dir)
                    zf.write(file_path, arcname)

        return True

    @staticmethod
    def get_file_list(file_path: Path) -> list[str]:
        """Get a list of files in an Office archive.

        Args:
            file_path: Path to the Office file.

        Returns:
            List of file paths within the archive.
        """
        with zipfile.ZipFile(file_path, 'r') as zf:
            return zf.namelist()

    @staticmethod
    def read_file(file_path: Path, internal_path: str) -> bytes:
        """Read a specific file from within an Office archive.

        Args:
            file_path: Path to the Office file.
            internal_path: Path of the file within the archive.

        Returns:
            Contents of the file as bytes.
        """
        with zipfile.ZipFile(file_path, 'r') as zf:
            return zf.read(internal_path)


# Alias for backward compatibility
DocxHandler = OfficeFileHandler

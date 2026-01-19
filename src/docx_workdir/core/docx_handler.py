"""Handler for .docx file operations (ZIP extraction and repackaging)."""

import zipfile
from pathlib import Path
from typing import Optional


class DocxHandler:
    """Handles extraction and repackaging of .docx files."""

    def __init__(self):
        """Initialize the DocxHandler."""
        pass

    @staticmethod
    def is_valid_docx(file_path: Path) -> bool:
        """Check if a file is a valid .docx file.

        Args:
            file_path: Path to the file to check.

        Returns:
            True if the file is a valid .docx (ZIP) file.
        """
        if not file_path.exists():
            return False
        if file_path.suffix.lower() != ".docx":
            return False
        try:
            with zipfile.ZipFile(file_path, 'r') as zf:
                # Check for essential docx files
                namelist = zf.namelist()
                return "[Content_Types].xml" in namelist
        except (zipfile.BadZipFile, Exception):
            return False

    @staticmethod
    def extract(docx_path: Path, output_dir: Path) -> bool:
        """Extract a .docx file to a directory.

        Args:
            docx_path: Path to the .docx file.
            output_dir: Directory to extract contents to.

        Returns:
            True if extraction was successful.

        Raises:
            FileNotFoundError: If the docx file doesn't exist.
            zipfile.BadZipFile: If the file is not a valid ZIP.
            PermissionError: If permission denied.
        """
        if not docx_path.exists():
            raise FileNotFoundError(f"File not found: {docx_path}")

        output_dir.mkdir(parents=True, exist_ok=True)

        with zipfile.ZipFile(docx_path, 'r') as zf:
            zf.extractall(output_dir)

        return True

    @staticmethod
    def repackage(source_dir: Path, output_path: Path) -> bool:
        """Repackage a directory into a .docx file.

        Args:
            source_dir: Directory containing the extracted docx contents.
            output_path: Path for the output .docx file.

        Returns:
            True if repackaging was successful.

        Raises:
            FileNotFoundError: If the source directory doesn't exist.
            ValueError: If the source directory doesn't contain valid docx structure.
            PermissionError: If permission denied.
        """
        if not source_dir.exists():
            raise FileNotFoundError(f"Directory not found: {source_dir}")

        # Verify essential docx files exist
        content_types = source_dir / "[Content_Types].xml"
        if not content_types.exists():
            raise ValueError(f"Invalid docx structure: missing [Content_Types].xml")

        # Create parent directory if needed
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            for file_path in source_dir.rglob('*'):
                if file_path.is_file():
                    arcname = file_path.relative_to(source_dir)
                    zf.write(file_path, arcname)

        return True

    @staticmethod
    def get_file_list(docx_path: Path) -> list[str]:
        """Get a list of files in a .docx archive.

        Args:
            docx_path: Path to the .docx file.

        Returns:
            List of file paths within the archive.
        """
        with zipfile.ZipFile(docx_path, 'r') as zf:
            return zf.namelist()

    @staticmethod
    def read_file(docx_path: Path, internal_path: str) -> bytes:
        """Read a specific file from within a .docx archive.

        Args:
            docx_path: Path to the .docx file.
            internal_path: Path of the file within the archive.

        Returns:
            Contents of the file as bytes.
        """
        with zipfile.ZipFile(docx_path, 'r') as zf:
            return zf.read(internal_path)

"""Dialog components for office-raw-editor application."""

from typing import Optional

from PySide6.QtWidgets import (
    QDialog,
    QMessageBox,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFileDialog,
)
from PySide6.QtCore import Qt

from ..utils.constants import (
    DIALOG_TITLE_CONFIRM,
    DIALOG_TITLE_ERROR,
    DIALOG_TITLE_WARNING,
    DIALOG_TITLE_OPEN,
    DIALOG_TITLE_SAVE,
    FILE_FILTER_DOCX,
    FILE_FILTER_XLSX,
    FILE_FILTER_PPTX,
    FILE_FILTER_OFFICE,
    FILE_FILTER_ALL,
    MSG_CONFIRM_OVERWRITE,
    MSG_CONFIRM_EXIT,
)


class ConfirmDialog:
    """Utility class for confirmation dialogs."""

    @staticmethod
    def ask_yes_no(parent, title: str, message: str) -> bool:
        """Show a yes/no confirmation dialog.

        Args:
            parent: Parent widget.
            title: Dialog title.
            message: Dialog message.

        Returns:
            True if user clicked Yes.
        """
        result = QMessageBox.question(
            parent,
            title,
            message,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        return result == QMessageBox.StandardButton.Yes

    @staticmethod
    def ask_yes_no_cancel(parent, title: str, message: str) -> Optional[bool]:
        """Show a yes/no/cancel confirmation dialog.

        Args:
            parent: Parent widget.
            title: Dialog title.
            message: Dialog message.

        Returns:
            True if Yes, False if No, None if Cancel.
        """
        result = QMessageBox.question(
            parent,
            title,
            message,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Cancel,
        )
        if result == QMessageBox.StandardButton.Yes:
            return True
        elif result == QMessageBox.StandardButton.No:
            return False
        return None

    @staticmethod
    def confirm(parent, title: str, message: str) -> bool:
        """Show a simple confirmation dialog.

        Args:
            parent: Parent widget.
            title: Dialog title.
            message: Dialog message.

        Returns:
            True if user confirmed.
        """
        return ConfirmDialog.ask_yes_no(parent, title, message)

    @staticmethod
    def confirm_overwrite(parent, file_path: str) -> bool:
        """Confirm overwriting an existing file.

        Args:
            parent: Parent widget.
            file_path: Path to the file that will be overwritten.

        Returns:
            True if user confirmed overwrite.
        """
        return ConfirmDialog.ask_yes_no(
            parent,
            DIALOG_TITLE_CONFIRM,
            f"{MSG_CONFIRM_OVERWRITE}\n\n{file_path}",
        )

    @staticmethod
    def confirm_exit_with_changes(parent) -> Optional[bool]:
        """Confirm exit when there are unsaved changes.

        Args:
            parent: Parent widget.

        Returns:
            True to save and exit, False to exit without saving, None to cancel.
        """
        result = QMessageBox.question(
            parent,
            DIALOG_TITLE_WARNING,
            f"{MSG_CONFIRM_EXIT}\n\n保存しますか？",
            QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Discard | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Cancel,
        )
        if result == QMessageBox.StandardButton.Save:
            return True
        elif result == QMessageBox.StandardButton.Discard:
            return False
        return None


class ErrorDialog:
    """Utility class for error dialogs."""

    @staticmethod
    def show_error(parent, title: str, message: str):
        """Show an error dialog.

        Args:
            parent: Parent widget.
            title: Dialog title.
            message: Error message.
        """
        QMessageBox.critical(parent, title, message)

    @staticmethod
    def show_warning(parent, title: str, message: str):
        """Show a warning dialog.

        Args:
            parent: Parent widget.
            title: Dialog title.
            message: Warning message.
        """
        QMessageBox.warning(parent, title, message)

    @staticmethod
    def show_info(parent, title: str, message: str):
        """Show an info dialog.

        Args:
            parent: Parent widget.
            title: Dialog title.
            message: Info message.
        """
        QMessageBox.information(parent, title, message)


class FileDialogs:
    """Utility class for file dialogs."""

    @staticmethod
    def open_docx(parent, initial_dir: str = "") -> Optional[str]:
        """Show dialog to open an Office file.

        Supports Word, Excel, PowerPoint and their variants.

        Args:
            parent: Parent widget.
            initial_dir: Initial directory to show.

        Returns:
            Selected file path, or None if cancelled.
        """
        file_path, _ = QFileDialog.getOpenFileName(
            parent,
            DIALOG_TITLE_OPEN,
            initial_dir,
            f"{FILE_FILTER_OFFICE};;{FILE_FILTER_DOCX};;{FILE_FILTER_XLSX};;{FILE_FILTER_PPTX};;{FILE_FILTER_ALL}",
        )
        return file_path if file_path else None

    @staticmethod
    def save_docx(parent, initial_dir: str = "", suggested_name: str = "", file_type: str = ".docx") -> Optional[str]:
        """Show dialog to save an Office file.

        Args:
            parent: Parent widget.
            initial_dir: Initial directory to show.
            suggested_name: Suggested file name.
            file_type: File extension (.docx, .xlsx, .pptx, etc.).

        Returns:
            Selected file path, or None if cancelled.
        """
        initial_path = initial_dir
        if suggested_name:
            from pathlib import Path
            initial_path = str(Path(initial_dir) / suggested_name) if initial_dir else suggested_name

        # Choose filter based on file type
        file_type_lower = file_type.lower()
        if file_type_lower in {".xlsx", ".xlsm", ".xltx", ".xltm"}:
            filter_str = f"{FILE_FILTER_XLSX};;{FILE_FILTER_ALL}"
        elif file_type_lower in {".pptx", ".pptm", ".potx", ".potm", ".ppsx", ".ppsm"}:
            filter_str = f"{FILE_FILTER_PPTX};;{FILE_FILTER_ALL}"
        else:
            filter_str = f"{FILE_FILTER_DOCX};;{FILE_FILTER_ALL}"

        file_path, _ = QFileDialog.getSaveFileName(
            parent,
            DIALOG_TITLE_SAVE,
            initial_path,
            filter_str,
        )
        return file_path if file_path else None

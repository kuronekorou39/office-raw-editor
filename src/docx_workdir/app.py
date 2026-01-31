"""Main application class for office-raw-editor."""

import sys
from pathlib import Path
from typing import Optional

from PyQt6.QtWidgets import QApplication

from .ui.main_window import MainWindow
from .ui.styles import APP_STYLESHEET
from .utils.constants import APP_NAME, SUPPORTED_EXTENSIONS


class OfficeRawEditorApp:
    """Main application class for editing Office Open XML files."""

    def __init__(self, argv: Optional[list[str]] = None):
        """Initialize the application.

        Args:
            argv: Command line arguments. If None, uses sys.argv.
        """
        if argv is None:
            argv = sys.argv

        self.app = QApplication(argv)
        self.app.setApplicationName(APP_NAME)
        self.app.setOrganizationName("office-raw-editor")

        # Set application style
        self.app.setStyle("Fusion")
        self.app.setStyleSheet(APP_STYLESHEET)

        self.main_window: Optional[MainWindow] = None
        self._initial_file: Optional[Path] = None

        # Parse command line arguments
        self._parse_args(argv[1:])

    def _parse_args(self, args: list[str]):
        """Parse command line arguments.

        Args:
            args: List of command line arguments (without program name).
        """
        for arg in args:
            if not arg.startswith("-"):
                path = Path(arg)
                if path.exists() and path.suffix.lower() in SUPPORTED_EXTENSIONS:
                    self._initial_file = path
                break

    def run(self) -> int:
        """Run the application.

        Returns:
            Exit code.
        """
        self.main_window = MainWindow()
        self.main_window.show()

        # Open initial file if provided
        if self._initial_file:
            self.main_window._load_docx(self._initial_file)

        return self.app.exec()


def main():
    """Main entry point."""
    app = OfficeRawEditorApp()
    sys.exit(app.run())


if __name__ == "__main__":
    main()

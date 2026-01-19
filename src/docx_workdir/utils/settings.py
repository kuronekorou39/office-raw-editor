"""Settings management for docx-workdir application."""

import json
from pathlib import Path
from typing import Optional

from PyQt6.QtCore import QSettings

from .constants import APP_NAME


class Settings:
    """Application settings manager using QSettings."""

    # Setting keys
    KEY_EXTERNAL_EDITOR = "external_editor/path"
    KEY_USE_EXTERNAL_EDITOR = "external_editor/use_external"
    KEY_WINDOW_GEOMETRY = "window/geometry"
    KEY_WINDOW_STATE = "window/state"
    KEY_SPLITTER_STATE = "window/splitter_state"
    KEY_LAST_OPEN_DIR = "files/last_open_dir"
    KEY_LAST_SAVE_DIR = "files/last_save_dir"

    def __init__(self):
        """Initialize the settings manager."""
        self._settings = QSettings(APP_NAME, APP_NAME)

    def get_external_editor(self) -> str:
        """Get the external editor path.

        Returns:
            Path to the external editor, or empty string if not set.
        """
        return self._settings.value(self.KEY_EXTERNAL_EDITOR, "", str)

    def set_external_editor(self, path: str):
        """Set the external editor path.

        Args:
            path: Path to the external editor.
        """
        self._settings.setValue(self.KEY_EXTERNAL_EDITOR, path)

    def get_use_external_editor(self) -> bool:
        """Get whether to use external editor by default.

        Returns:
            True if external editor should be used by default.
        """
        return self._settings.value(self.KEY_USE_EXTERNAL_EDITOR, False, bool)

    def set_use_external_editor(self, use: bool):
        """Set whether to use external editor by default.

        Args:
            use: True to use external editor by default.
        """
        self._settings.setValue(self.KEY_USE_EXTERNAL_EDITOR, use)

    def get_window_geometry(self) -> Optional[bytes]:
        """Get the saved window geometry.

        Returns:
            Window geometry bytes, or None if not saved.
        """
        return self._settings.value(self.KEY_WINDOW_GEOMETRY)

    def set_window_geometry(self, geometry: bytes):
        """Save the window geometry.

        Args:
            geometry: Window geometry bytes.
        """
        self._settings.setValue(self.KEY_WINDOW_GEOMETRY, geometry)

    def get_window_state(self) -> Optional[bytes]:
        """Get the saved window state.

        Returns:
            Window state bytes, or None if not saved.
        """
        return self._settings.value(self.KEY_WINDOW_STATE)

    def set_window_state(self, state: bytes):
        """Save the window state.

        Args:
            state: Window state bytes.
        """
        self._settings.setValue(self.KEY_WINDOW_STATE, state)

    def get_splitter_state(self) -> Optional[bytes]:
        """Get the saved splitter state.

        Returns:
            Splitter state bytes, or None if not saved.
        """
        return self._settings.value(self.KEY_SPLITTER_STATE)

    def set_splitter_state(self, state: bytes):
        """Save the splitter state.

        Args:
            state: Splitter state bytes.
        """
        self._settings.setValue(self.KEY_SPLITTER_STATE, state)

    def get_last_open_dir(self) -> str:
        """Get the last directory used for opening files.

        Returns:
            Last open directory path, or empty string.
        """
        return self._settings.value(self.KEY_LAST_OPEN_DIR, "", str)

    def set_last_open_dir(self, path: str):
        """Set the last directory used for opening files.

        Args:
            path: Directory path.
        """
        self._settings.setValue(self.KEY_LAST_OPEN_DIR, path)

    def get_last_save_dir(self) -> str:
        """Get the last directory used for saving files.

        Returns:
            Last save directory path, or empty string.
        """
        return self._settings.value(self.KEY_LAST_SAVE_DIR, "", str)

    def set_last_save_dir(self, path: str):
        """Set the last directory used for saving files.

        Args:
            path: Directory path.
        """
        self._settings.setValue(self.KEY_LAST_SAVE_DIR, path)

    def sync(self):
        """Force sync settings to storage."""
        self._settings.sync()


# Global settings instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get the global settings instance.

    Returns:
        The global Settings instance.
    """
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings

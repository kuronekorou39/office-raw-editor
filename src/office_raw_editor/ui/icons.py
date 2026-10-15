"""Monochrome vector icons for the UI.

Icons are inline SVG (24x24 stroke paths, based on the ISC-licensed Lucide set)
rendered on demand through a QIconEngine, so they stay crisp at any size and
DPI and can be tinted to any color without extra image files or fonts.
"""

from typing import Optional

from PyQt6.QtCore import QRect, QSize, Qt, QByteArray
from PyQt6.QtGui import QColor, QIcon, QIconEngine, QPainter, QPixmap, QGuiApplication
from PyQt6.QtSvg import QSvgRenderer
from PyQt6.QtWidgets import QLabel, QPushButton

from .styles import COLORS, ICON_BUTTON_STYLE

# SVG path data per icon name (viewBox 0 0 24 24, stroke only)
_PATHS: dict[str, str] = {
    "folder": (
        "M20 20a2 2 0 0 0 2-2V8a2 2 0 0 0-2-2h-7.9a2 2 0 0 1-1.69-.9L9.6 3.9"
        "A2 2 0 0 0 7.93 3H4a2 2 0 0 0-2 2v13a2 2 0 0 0 2 2Z"
    ),
    "folder-open": (
        "M6 14l1.5-2.9A2 2 0 0 1 9.24 10H20a2 2 0 0 1 1.94 2.5l-1.54 6a2 2 0 0 1-1.95 1.5H4"
        "a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h3.9a2 2 0 0 1 1.69.9l.81 1.2a2 2 0 0 0 1.67.9H18"
        "a2 2 0 0 1 2 2v2"
    ),
    "folder-plus": (
        "M20 20a2 2 0 0 0 2-2V8a2 2 0 0 0-2-2h-7.9a2 2 0 0 1-1.69-.9L9.6 3.9"
        "A2 2 0 0 0 7.93 3H4a2 2 0 0 0-2 2v13a2 2 0 0 0 2 2Z M12 10v6 M9 13h6"
    ),
    "file": "M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z M14 2v4a2 2 0 0 0 2 2h4",
    "file-text": (
        "M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z M14 2v4a2 2 0 0 0 2 2h4"
        " M10 9H8 M16 13H8 M16 17H8"
    ),
    "file-plus": (
        "M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z M14 2v4a2 2 0 0 0 2 2h4"
        " M9 15h6 M12 18v-6"
    ),
    "file-input": (
        "M4 22h14a2 2 0 0 0 2-2V7l-5-5H6a2 2 0 0 0-2 2v4 M14 2v4a2 2 0 0 0 2 2h4"
        " M2 15h10 M9 18l3-3-3-3"
    ),
    "image": (
        "M5 3h14a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2Z"
        " M9 7a2 2 0 1 0 0 4 2 2 0 0 0 0-4Z M21 15l-3.1-3.1a2 2 0 0 0-2.8 0L6 21"
    ),
    "save": (
        "M15.2 3a2 2 0 0 1 1.4.6l3.8 3.8a2 2 0 0 1 .6 1.4V19a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5"
        "a2 2 0 0 1 2-2z M17 21v-7a1 1 0 0 0-1-1H8a1 1 0 0 0-1 1v7 M7 3v4a1 1 0 0 0 1 1h7"
    ),
    "save-as": (
        "M10 2v3a1 1 0 0 0 1 1h5 M18 18v-6a1 1 0 0 0-1-1h-6a1 1 0 0 0-1 1v6"
        " M18 22H4a2 2 0 0 1-2-2V6 M8 18a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9.172"
        "a2 2 0 0 1 1.414.586l2.828 2.828A2 2 0 0 1 22 6.828V16a2 2 0 0 1-2.01 2z"
    ),
    "refresh": "M21 12a9 9 0 1 1-9-9c2.52 0 4.93 1 6.74 2.74L21 8 M21 3v5h-5",
    "undo": "M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8 M3 3v5h5",
    "settings": (
        "M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08"
        "a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51"
        "a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08"
        "a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18"
        "a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39"
        "a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09"
        "a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25"
        "a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z M12 9a3 3 0 1 0 0 6 3 3 0 0 0 0-6Z"
    ),
    "x": "M18 6L6 18 M6 6l12 12",
    "check": "M20 6 9 17l-5-5",
    "search": "M11 3a8 8 0 1 0 0 16 8 8 0 0 0 0-16Z M21 21l-4.3-4.3",
    "info": "M12 2a10 10 0 1 0 0 20 10 10 0 0 0 0-20Z M12 16v-4 M12 8h.01",
    "lock": "M5 11h14a2 2 0 0 1 2 2v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2Z M7 11V7a5 5 0 0 1 10 0v4",
    "lightbulb": (
        "M15 14c.2-1 .7-1.7 1.5-2.5 1-.9 1.5-2.2 1.5-3.5A6 6 0 0 0 6 8c0 1 .2 2.2 1.5 3.5"
        ".7.7 1.3 1.5 1.5 2.5 M9 18h6 M10 22h4"
    ),
    "highlighter": "m9 11-6 6v3h9l3-3 M22 12l-4.6 4.6a2 2 0 0 1-2.8 0l-5.2-5.2a2 2 0 0 1 0-2.8L14 4",
    "wrap-text": "M3 6h18 M3 12h15a3 3 0 1 1 0 6h-4 M16 16l-2 2 2 2 M3 18h7",
    "code": "m16 18 6-6-6-6 M8 6l-6 6 6 6",
    "chevron-left": "m15 18-6-6 6-6",
    "chevron-right": "m9 18 6-6-6-6",
    "trash": "M3 6h18 M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6 M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2",
    "pin": (
        "M12 17v5 M9 10.76a2 2 0 0 1-1.11 1.79l-1.78.9A2 2 0 0 0 5 15.24V16a1 1 0 0 0 1 1h12"
        "a1 1 0 0 0 1-1v-.76a2 2 0 0 0-1.11-1.79l-1.78-.9A2 2 0 0 1 15 10.76V7a1 1 0 0 1 1-1"
        " 2 2 0 0 0 0-4H8a2 2 0 0 0 0 4 1 1 0 0 1 1 1z"
    ),
}

DEFAULT_ICON_COLOR = COLORS['text_secondary']
DISABLED_ICON_COLOR = COLORS['text_muted']

_SVG_TEMPLATE = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" '
    'stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
    '<path d="{path}"/></svg>'
)


def _svg_bytes(name: str, color: str) -> QByteArray:
    return QByteArray(_SVG_TEMPLATE.format(color=color, path=_PATHS[name]).encode("utf-8"))


class _SvgIconEngine(QIconEngine):
    """Renders a tinted SVG path at whatever size and DPI the widget asks for."""

    def __init__(self, name: str, color: str, disabled_color: str):
        super().__init__()
        self._name = name
        self._color = color
        self._disabled_color = disabled_color
        self._renderers: dict[str, QSvgRenderer] = {}

    def _renderer(self, mode: QIcon.Mode) -> QSvgRenderer:
        color = self._disabled_color if mode == QIcon.Mode.Disabled else self._color
        renderer = self._renderers.get(color)
        if renderer is None:
            renderer = QSvgRenderer(_svg_bytes(self._name, color))
            self._renderers[color] = renderer
        return renderer

    def paint(self, painter: QPainter, rect: QRect, mode: QIcon.Mode, state: QIcon.State):
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        self._renderer(mode).render(painter, rect.toRectF())

    def pixmap(self, size: QSize, mode: QIcon.Mode, state: QIcon.State) -> QPixmap:
        return self.scaledPixmap(size, mode, state, 1.0)

    def scaledPixmap(self, size: QSize, mode: QIcon.Mode, state: QIcon.State, scale: float) -> QPixmap:
        pixmap = QPixmap(int(size.width() * scale), int(size.height() * scale))
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        self._renderer(mode).render(painter)
        painter.end()
        pixmap.setDevicePixelRatio(scale)
        return pixmap

    def clone(self) -> QIconEngine:
        return _SvgIconEngine(self._name, self._color, self._disabled_color)

    def iconName(self) -> str:
        return self._name


def icon(name: str, color: Optional[str] = None, disabled_color: Optional[str] = None) -> QIcon:
    """Return a tinted vector icon by name.

    Args:
        name: Key of ``_PATHS``.
        color: Stroke color (CSS hex). Defaults to the secondary text color.
        disabled_color: Stroke color used in the Disabled icon mode.
    """
    if name not in _PATHS:
        raise KeyError(f"unknown icon: {name}")
    return QIcon(_SvgIconEngine(name, color or DEFAULT_ICON_COLOR, disabled_color or DISABLED_ICON_COLOR))


def icon_pixmap(name: str, size: int, color: Optional[str] = None) -> QPixmap:
    """Render an icon to a pixmap suited to the primary screen's DPI."""
    screen = QGuiApplication.primaryScreen()
    dpr = screen.devicePixelRatio() if screen else 1.0
    return icon(name, color).pixmap(QSize(size, size), dpr)


def icon_label(name: str, size: int = 16, color: Optional[str] = None, parent=None) -> QLabel:
    """Create a QLabel that shows only an icon (for headers, banners, etc.)."""
    label = QLabel(parent)
    label.setPixmap(icon_pixmap(name, size, color))
    label.setFixedSize(size, size)
    label.setStyleSheet("background: transparent;")
    return label


def icon_button(name: str, tooltip: str = "", size: int = 28, icon_size: int = 16,
                color: Optional[str] = None, parent=None) -> QPushButton:
    """Create a square, icon-only button that never clips its content."""
    btn = QPushButton(parent)
    btn.setIcon(icon(name, color))
    btn.setIconSize(QSize(icon_size, icon_size))
    btn.setFixedSize(size, size)
    btn.setStyleSheet(ICON_BUTTON_STYLE)
    btn.setCursor(Qt.CursorShape.PointingHandCursor)
    if tooltip:
        btn.setToolTip(tooltip)
    return btn

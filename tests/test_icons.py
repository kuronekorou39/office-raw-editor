"""Tests for the vector icon module."""

import pytest
from PySide6.QtCore import QSize
from PySide6.QtGui import QColor, QIcon, QImage

from office_raw_editor.ui import icons


def _opaque_pixels(image: QImage) -> set[tuple[int, int, int]]:
    """Return the distinct opaque RGB colors in an image."""
    colors = set()
    for y in range(image.height()):
        for x in range(image.width()):
            c = image.pixelColor(x, y)
            if c.alpha() > 200:
                colors.add((c.red(), c.green(), c.blue()))
    return colors


@pytest.mark.parametrize("name", sorted(icons._PATHS))
def test_every_icon_renders_something(qapp, name):
    image = icons.icon(name).pixmap(QSize(24, 24)).toImage()
    assert not image.isNull()
    assert _opaque_pixels(image), f"icon {name!r} rendered fully transparent"


def test_unknown_icon_name_raises(qapp):
    with pytest.raises(KeyError):
        icons.icon("does-not-exist")


def test_icon_uses_requested_color(qapp):
    image = icons.icon("x", "#FF0000").pixmap(QSize(32, 32)).toImage()
    assert (255, 0, 0) in _opaque_pixels(image)


def test_disabled_mode_uses_disabled_color(qapp):
    ic = icons.icon("save", "#000000", "#00FF00")
    normal = _opaque_pixels(ic.pixmap(QSize(32, 32), QIcon.Mode.Normal).toImage())
    disabled = _opaque_pixels(ic.pixmap(QSize(32, 32), QIcon.Mode.Disabled).toImage())
    assert (0, 0, 0) in normal
    assert (0, 255, 0) in disabled
    assert (0, 0, 0) not in disabled


def test_high_dpi_pixmap_is_scaled(qapp):
    pixmap = icons.icon("folder").pixmap(QSize(16, 16), 2.0)
    assert pixmap.width() == 32
    assert pixmap.devicePixelRatio() == 2.0


def test_icon_pixmap_matches_requested_size(qapp):
    pixmap = icons.icon_pixmap("info", 20)
    assert pixmap.width() / pixmap.devicePixelRatio() == 20


def test_icon_label_and_button_have_fixed_geometry(qtbot):
    label = icons.icon_label("lock", 14)
    qtbot.addWidget(label)
    assert label.size() == QSize(14, 14)
    assert not label.pixmap().isNull()

    button = icons.icon_button("search", "tooltip text", size=30, icon_size=18)
    qtbot.addWidget(button)
    assert button.size() == QSize(30, 30)
    assert button.iconSize() == QSize(18, 18)
    assert button.toolTip() == "tooltip text"
    assert not button.icon().isNull()

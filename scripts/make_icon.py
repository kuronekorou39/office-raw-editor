"""ウィンドウ・タスクバー・exe 用のアイコンを作る。

    python scripts/make_icon.py

ui/icons.py の "file-text" を、角丸の青い四角に白で描く。
src/office_raw_editor/ui/assets/app_icon.png(256px)と app.ico(16..256 の PNG 入り)を書き出す。
Pillow を増やさず PySide6 だけで済ませる。ICO は PNG をそのまま格納できる形式なので、ヘッダを手で書く。
"""

import os
import struct
import sys
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QBuffer, QIODevice, QRectF, Qt  # noqa: E402
from PySide6.QtGui import QColor, QGuiApplication, QImage, QPainter, QPainterPath  # noqa: E402
from PySide6.QtSvg import QSvgRenderer  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from office_raw_editor.ui.icons import _svg_bytes  # noqa: E402
from office_raw_editor.ui.styles import COLORS  # noqa: E402

ASSETS = ROOT / "src" / "office_raw_editor" / "ui" / "assets"
ICO_SIZES = (16, 24, 32, 48, 64, 128, 256)
GLYPH = "file-text"


def render(size: int) -> QImage:
    """角丸の青地に白いグリフ。小さいサイズでも読めるよう、グリフは枠の 62% にする。"""
    image = QImage(size, size, QImage.Format.Format_ARGB32)
    image.fill(Qt.GlobalColor.transparent)
    painter = QPainter(image)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    radius = size * 0.22
    path = QPainterPath()
    path.addRoundedRect(QRectF(0, 0, size, size), radius, radius)
    painter.fillPath(path, QColor(COLORS["primary"]))

    glyph = size * 0.62
    margin = (size - glyph) / 2
    QSvgRenderer(_svg_bytes(GLYPH, "#FFFFFF")).render(painter, QRectF(margin, margin, glyph, glyph))
    painter.end()
    return image


def png_bytes(image: QImage) -> bytes:
    buffer = QBuffer()
    buffer.open(QIODevice.OpenModeFlag.WriteOnly)
    image.save(buffer, "PNG")
    return bytes(buffer.data())


def write_ico(path: Path, images: dict[int, bytes]) -> None:
    """PNG 入りの ICO を書く。"""
    header = struct.pack("<HHH", 0, 1, len(images))
    entries = b""
    offset = len(header) + 16 * len(images)
    for size, blob in images.items():
        dimension = 0 if size >= 256 else size  # 256 は 0 と書く決まり
        entries += struct.pack("<BBBBHHII", dimension, dimension, 0, 0, 1, 32, len(blob), offset)
        offset += len(blob)
    path.write_bytes(header + entries + b"".join(images.values()))


def main() -> None:
    QGuiApplication([])
    ASSETS.mkdir(parents=True, exist_ok=True)
    render(256).save(str(ASSETS / "app_icon.png"))
    write_ico(ASSETS / "app.ico", {size: png_bytes(render(size)) for size in ICO_SIZES})
    print("saved:", ASSETS / "app_icon.png")
    print("saved:", ASSETS / "app.ico")


if __name__ == "__main__":
    main()

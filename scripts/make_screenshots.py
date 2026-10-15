"""README 用のスクリーンショットを撮る。

    python scripts/make_screenshots.py

架空のサンプル文書(sample_template.docx)をその場で作って開き、
docs/images/ に welcome.png / tree.png / editor.png を書き出す。
実在のファイルを写さないため、撮影には必ずこのスクリプトを使う。
画面は出さない(offscreen)。日本語が豆腐にならないよう Windows のフォントを読ませる。
"""

import os
import sys
import tempfile
import zipfile
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("QT_QPA_FONTDIR", str(Path(os.environ.get("WINDIR", r"C:\Windows")) / "Fonts"))

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
OUT = ROOT / "docs" / "images"
WINDOW_SIZE = (1000, 700)

from PySide6.QtWidgets import QApplication  # noqa: E402

from office_raw_editor.core.workspace import WorkspaceManager  # noqa: E402
from office_raw_editor.ui.editor_window import EditorWindow  # noqa: E402
from office_raw_editor.ui.main_window import MainWindow  # noqa: E402
from office_raw_editor.ui.styles import APP_STYLESHEET  # noqa: E402

W = 'xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"'
PARAGRAPHS = [
    ("Title", "{{title}}"),
    (None, "作成日: {{date}}"),
    (None, "担当: {{author}}"),
    ("Heading1", "1. 概要"),
    (None, "本書は {{project}} の月次報告です。"),
    ("Heading1", "2. 進捗"),
    (None, "今月の完了タスクは {{done_count}} 件、残りは {{todo_count}} 件です。"),
    ("Heading1", "3. 次月の予定"),
    (None, "{{next_plan}}"),
]


def _paragraph(style, text):
    ppr = f'<w:pPr><w:pStyle w:val="{style}"/></w:pPr>' if style else ""
    return f"<w:p>{ppr}<w:r><w:t>{text}</w:t></w:r></w:p>"


def build_sample(path: Path) -> Path:
    """架空のテンプレート文書を作る(Word で開ける最小構成+よくある部品)。"""
    body = "".join(_paragraph(s, t) for s, t in PARAGRAPHS)
    files = {
        "[Content_Types].xml": (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
            '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
            '<Default Extension="xml" ContentType="application/xml"/>'
            '<Default Extension="png" ContentType="image/png"/>'
            '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
            '<Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>'
            '<Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>'
            '<Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>'
            '</Types>'
        ),
        "_rels/.rels": (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>'
            '<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/>'
            '<Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties" Target="docProps/app.xml"/>'
            '</Relationships>'
        ),
        "docProps/app.xml": '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties"><Application>Microsoft Office Word</Application></Properties>',
        "docProps/core.xml": '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" xmlns:dc="http://purl.org/dc/elements/1.1/"><dc:title>{{title}}</dc:title></cp:coreProperties>',
        "word/document.xml": f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:document {W}><w:body>{body}<w:sectPr/></w:body></w:document>',
        "word/styles.xml": f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:styles {W}><w:style w:type="paragraph" w:styleId="Title"><w:name w:val="Title"/></w:style><w:style w:type="paragraph" w:styleId="Heading1"><w:name w:val="heading 1"/></w:style></w:styles>',
        "word/settings.xml": f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:settings {W}><w:zoom w:percent="100"/></w:settings>',
        "word/fontTable.xml": f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:fonts {W}><w:font w:name="Yu Gothic"/></w:fonts>',
        "word/theme/theme1.xml": '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><a:theme xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" name="Office Theme"/>',
        "word/_rels/document.xml.rels": (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>'
            '<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="media/image1.png"/>'
            '</Relationships>'
        ),
        "word/media/image1.png": _logo_png(),
    }
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zf:
        for name, content in files.items():
            zf.writestr(name, content)
    return path


def _logo_png() -> bytes:
    """文書に入っている体の画像。アプリアイコンを流用する。"""
    return (ROOT / "src" / "office_raw_editor" / "ui" / "assets" / "app_icon.png").read_bytes()


def main() -> None:
    app = QApplication([])
    app.setStyle("Fusion")
    app.setStyleSheet(APP_STYLESHEET)
    OUT.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        sample = build_sample(tmp_path / "sample_template.docx")

        window = MainWindow()
        window._modification_timer.stop()
        window.workspace = WorkspaceManager(base_dir=tmp_path / "workspaces")
        window.resize(*WINDOW_SIZE)
        window.show()
        app.processEvents()
        window.grab().save(str(OUT / "welcome.png"))

        # 展開 → 1 ファイルを編集済みにし、内容検索をかけた状態
        window.workspace.backup_manager.backup_dir = tmp_path / "backups"
        window._load_docx(sample)
        workspace = window.workspace.current_workspace
        settings_xml = workspace / "word" / "settings.xml"
        settings_xml.write_text(settings_xml.read_text(encoding="utf-8").replace('"100"', '"120"'), encoding="utf-8")
        window._check_modifications()
        window.content_search_input.setText("{{")
        window._run_content_search()
        doc_item = window.file_tree._items_map[str(Path("word") / "document.xml")]
        window.file_tree.setCurrentItem(doc_item)
        app.processEvents()
        window.grab().save(str(OUT / "tree.png"))

        # 内蔵エディタ: 整形して検索バーを開いた状態
        window._open_in_internal_editor(workspace / "word" / "document.xml")
        editor_window = EditorWindow._instance
        editor_window.resize(*WINDOW_SIZE)
        editor = next(iter(editor_window._editors.values()))
        editor.format_xml()
        editor.show_search_bar()
        editor.search_input.setText("{{project}}")
        app.processEvents()
        editor_window.grab().save(str(OUT / "editor.png"))

        editor_window._editors.clear()
        editor_window.tab_widget.clear()
        editor_window.close()
        window.workspace.close()
        window.close()

    for name in ("welcome.png", "tree.png", "editor.png"):
        print("saved:", OUT / name)


if __name__ == "__main__":
    main()

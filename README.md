# office-raw-editor

<p align="center">
  <img src="docs/images/tree.png" width="720" alt="office-raw-editor">
</p>

Office ファイル (Word/Excel/PowerPoint) の内部構造を編集するためのGUIツール

## 概要

Office文書 (.docx, .xlsx, .pptx など) はZIPアーカイブであり、内部にXMLファイルを含んでいます。このツールはOfficeファイルを展開し、内部のXMLファイルを編集して再パッケージすることができます。

## 対応形式

| 種類 | 拡張子 |
|------|--------|
| Word | .docx .docm .dotx .dotm |
| Excel | .xlsx .xlsm .xltx .xltm |
| PowerPoint | .pptx .pptm .potx .potm .ppsx .ppsm |

## 機能

- Officeファイルの展開・再パッケージ
- ファイルツリー表示
- 内蔵XMLエディタ（シンタックスハイライト付き）
- 外部エディタ連携（VSCode, Notepad++等）
- 自動バックアップ
- フォントサイズ変更（Ctrl+ホイール）
- カーソル位置からの検索
- ファイル内容を含むファイルの検索（ツリーをハイライト/絞り込み）

## インストール

```bash
# リポジトリをクローン
git clone https://github.com/kuronekorou39/office-raw-editor.git
cd office-raw-editor

# 仮想環境を作成
python -m venv venv

# 仮想環境を有効化 (Windows)
venv\Scripts\activate

# 依存関係をインストール
pip install -r requirements.txt

# 開発モードでインストール
pip install -e .
```

## 起動方法

### Windows (コマンドプロンプト)

```cmd
cd C:\projects\office-raw-editor
venv\Scripts\activate
python -m office_raw_editor
```

### Windows (PowerShell)

```powershell
cd C:\projects\office-raw-editor
.\venv\Scripts\Activate.ps1
python -m office_raw_editor
```

### ファイルを指定して起動

```cmd
python -m office_raw_editor path\to\file.docx
python -m office_raw_editor path\to\file.xlsx
python -m office_raw_editor path\to\file.pptx
```

## 使い方

1. **ファイルを開く**: 「開く」ボタンまたは Ctrl+O でOfficeファイルを選択（ドラッグ＆ドロップも可）
2. **ファイルを編集**:
   - ダブルクリック → エディタ選択ダイアログ
   - 内蔵エディタまたは外部エディタで編集
3. **保存**: 内蔵エディタで Ctrl+S で個別ファイルを保存
4. **再パッケージ**: 「保存」または「名前を付けて保存」で元の形式として出力

## キーボードショートカット

| キー | 機能 |
|------|------|
| Ctrl+O | ファイルを開く |
| Ctrl+S | 保存 |
| Ctrl+Shift+S | 名前を付けて保存 |
| Ctrl+F | 検索 |
| Ctrl+Shift+F | ファイル内容検索（ツリー） |
| F3 / Shift+F3 | 次/前を検索 |
| Ctrl++ / Ctrl+- | フォント拡大/縮小 |
| Ctrl+0 | フォントサイズリセット |
| F5 | ツリー更新 |

## 設定

**ツール → 設定** から外部エディタを設定できます。

- VS Code
- Notepad++
- サクラエディタ
- メモ帳

など、インストール済みのエディタが自動検出されます。

## 注意事項

- 編集前に自動でバックアップが作成されます（元ファイルと同じフォルダに `.backup` 付きで保存）
- 大きなXMLファイルは内蔵エディタの「色付け」をOFFにすると軽くなります
- Officeファイルの構造を壊すとアプリケーションで開けなくなる可能性があります

## テスト

```bash
pip install -e .[dev]
pytest
```

pytest-qt を使い、オフスクリーン描画で GUI もテストします(ディスプレイ不要)。
テスト中の設定は一時ファイルに隔離され、実際のレジストリ設定には影響しません。

## 動作環境

- Python 3.10以上
- PySide6 6.6.0以上

## ライセンス

MIT License

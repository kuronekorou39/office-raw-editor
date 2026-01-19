# docx-workdir

.docxファイルの内部構造を編集するためのGUIツール

## 概要

Word文書(.docx)はZIPアーカイブであり、内部にXMLファイルを含んでいます。このツールは.docxを展開し、内部のXMLファイルを編集して再パッケージすることができます。

## 機能

- .docxファイルの展開・再パッケージ
- ファイルツリー表示
- 内蔵XMLエディタ（シンタックスハイライト付き）
- 外部エディタ連携（VSCode, Notepad++等）
- 自動バックアップ

## インストール

```bash
# リポジトリをクローン
git clone <repository-url>
cd docx-raw-editor

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
cd C:\projects\docx-raw-editor
venv\Scripts\activate
python -m docx_workdir
```

### Windows (PowerShell)

```powershell
cd C:\projects\docx-raw-editor
.\venv\Scripts\Activate.ps1
python -m docx_workdir
```

### ファイルを指定して起動

```cmd
python -m docx_workdir path\to\file.docx
```

## 使い方

1. **ファイルを開く**: 「開く」ボタンまたは Ctrl+O で.docxファイルを選択
2. **ファイルを編集**:
   - ダブルクリック → 内蔵エディタで開く
   - Ctrl+I → 内蔵エディタで開く
   - Ctrl+E → 外部エディタで開く
3. **保存**: 内蔵エディタで Ctrl+S で個別ファイルを保存
4. **再パッケージ**: 「保存」または「名前を付けて保存」で.docxとして出力

## キーボードショートカット

| キー | 機能 |
|------|------|
| Ctrl+O | ファイルを開く |
| Ctrl+S | 保存 |
| Ctrl+Shift+S | 名前を付けて保存 |
| Ctrl+I | 内蔵エディタで開く |
| Ctrl+E | 外部エディタで開く |
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
- .docxの構造を壊すとWordで開けなくなる可能性があります

## 動作環境

- Python 3.10以上
- PyQt6 6.5.0以上

## ライセンス

MIT License

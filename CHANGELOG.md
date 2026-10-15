# 変更履歴

形式は [Keep a Changelog](https://keepachangelog.com/ja/1.1.0/) に、版は [セマンティック バージョニング](https://semver.org/lang/ja/) に従う。

## [Unreleased]

### 変更

- GUI フレームワークを PyQt6 (GPL) から PySide6 (LGPL) に移行
- パッケージ名を `docx_workdir` から `office_raw_editor` に変更。起動は `python -m office_raw_editor`
- 画面の絵文字を単色のベクターアイコンに置き換え。ツリーのアイコンはファイル種別ごとに色分け
- 検索ヒット数の表示を「(n件)」に変更
- 仕様書を `docs/spec.md` に移動

### 追加

- exe ビルド(`scripts/build_exe.ps1`、`docs/build-exe.md`)とアプリアイコン
- コンソール無し exe 用の起点。起動に失敗したら `~\.office-raw-editor\startup-error.log` に記録
- テストスイート(core / UI)と GitHub Actions での自動テスト
- `LICENSE`、`THIRD_PARTY_NOTICES.md`、`licenses/`(LGPL/GPL 本文)

### 修正

- アイコンだけのボタン(検索・クリア・閉じる)と `A-` / `A+` のラベルが表示されない
- ツリーを閉じても内部の項目一覧が残る
- 検索バーの表示切替が、エディタ表示前だと効かない

## [0.2.0] - 2026-04-29

### 追加

- Excel (.xlsx 系) と PowerPoint (.pptx 系) に対応し、アプリ名を office-raw-editor に変更
- ファイル内容検索(Ctrl+Shift+F)。ツリーのハイライトと絞り込み
- ツリーのサイズ列のヒートマップ、メインコンテンツファイルの強調表示

### 修正

- エディタの「前へ」検索が現在の一致から動かない

## [0.1.0] - 2026-01-20

### 追加

- docx を展開して内部 XML を編集し、再パッケージする GUI
- 内蔵 XML エディタ(行番号、シンタックスハイライト、検索、整形、ズーム)
- 外部エディタ連携、自動バックアップ、ファイルの追加・差し替え・削除・元に戻す

[Unreleased]: https://github.com/kuronekorou39/office-raw-editor/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/kuronekorou39/office-raw-editor/releases/tag/v0.2.0
[0.1.0]: https://github.com/kuronekorou39/office-raw-editor/releases/tag/v0.1.0

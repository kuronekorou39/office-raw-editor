# exe にして配る

Python の入っていない PC でも動くように、PyInstaller で `dist\office-raw-editor\` にまとめ、
zip にする手順と、配るときの注意。

---

## 1. ビルドする

必要なもの: Windows 64bit、Python 3.10 以上。exe はビルド機と同じ構成になるので、
配布先も 64bit の Windows 10 / 11 に限られる。

```powershell
git clone <このリポジトリ>
cd office-raw-editor
python -m venv venv
venv\Scripts\pip install -r requirements-dev.txt   # pyinstaller もここで入る
.\scripts\build_exe.ps1
```

`dist\` に次が出る。

| 出力 | 中身 |
|---|---|
| `office-raw-editor\office-raw-editor.exe` | 画面を開く。コンソール無し。ダブルクリック用 |
| `office-raw-editor\_internal\` | Python 本体、Qt、依存ライブラリ。**exe と必ず一緒に置く** |
| `office-raw-editor\README.md`、`LICENSE` | 使い方とライセンス |
| `office-raw-editor\THIRD_PARTY_NOTICES.md`、`licenses\` | 同梱物(Qt/PySide6、Python、アイコン)の著作権表示とライセンス本文 |
| `office-raw-editor-<版>.zip` | 上のフォルダを丸ごと固めたもの。これを配る |

版は `src/office_raw_editor/__init__.py` の `__version__`。exe のプロパティの「詳細」にも出る
(`office-raw-editor.spec` が埋め込む)。
アイコンは `scripts/make_icon.py` が `ui/icons.py` の線画から生成する(`src/office_raw_editor/ui/assets/app.ico`)。
onefile にはしない。起動が速く、ウイルス対策にも引っかかりにくいため。
`dist\` と `build\` は git 管理外なので、ビルド機ごとに作り直す。

## 2. 配る

zip を渡し、任意の場所に展開して `office-raw-editor\office-raw-editor.exe` を起動してもらう。
共有フォルダに展開して、そこから直接起動させてもよい。
`office-raw-editor.exe` 単体を持ち出すと `_internal` が無くて起きない。

### 注意

- **SmartScreen**。署名の無い exe は初回起動で「発行元不明」の警告が出る。
  ダウンロード経由だとブロックされることもあるので、共有フォルダから直接起動させる方が通りやすい
- **ランタイムは同梱済み**。`VCRUNTIME140` と `MSVCP140` が入っているので、
  配布先で Visual C++ 再頒布パッケージを入れる必要はない
- **設定はユーザーごと**。外部エディタのパス等はレジストリ(`HKCU\Software\office-raw-editor`)に入る
- **作業フォルダ**。展開した中身は `%TEMP%\office_raw_editor\` に置かれ、閉じると消える。
  バックアップは元ファイルと同じフォルダに `.backup` 付きで残る
- **起動に失敗したとき**。コンソールが無いので、代わりに `~\.office-raw-editor\startup-error.log` に
  内容を書き、メッセージボックスで場所を知らせる(`office_raw_editor/gui.py`)

### ライセンス

社内配布は問題ない。PySide6 は LGPL だが、Qt を DLL のまま同梱していて静的リンクではないので
条件を満たす。PyInstaller 自体は GPL だが生成物には適用されない。
社外に配る場合に必要な LGPL の表示(ライセンス本文の添付)は、ビルドスクリプトが
`THIRD_PARTY_NOTICES.md` と `licenses\` を同梱することで満たしている。
依存やアイコンを足したときは `THIRD_PARTY_NOTICES.md` も更新する。

# exe をビルドして zip にする。
#   .\scripts\build_exe.ps1
# 出力: dist\office-raw-editor\(office-raw-editor.exe、_internal\、README.md、LICENSE、THIRD_PARTY_NOTICES.md、licenses\)と dist\office-raw-editor-<版>.zip
# venv が無ければ先に作る(python -m venv venv; pip install -r requirements-dev.txt)。
$ErrorActionPreference = "Continue"  # PyInstaller はログを標準エラーに出す。失敗は終了コードで見る
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

$python = Join-Path $root "venv\Scripts\python.exe"
if (-not (Test-Path $python)) {
    throw "venv が見つかりません: $python"
}

$env:PYTHONUTF8 = "1"
& $python -m PyInstaller --version *> $null
if ($LASTEXITCODE -ne 0) {
    & $python -m pip install pyinstaller
    if ($LASTEXITCODE -ne 0) { throw "PyInstaller を入れられませんでした" }
}

# アイコンが無ければ作る(src/office_raw_editor/ui/assets/app.ico)
$icon = Join-Path $root "src\office_raw_editor\ui\assets\app.ico"
if (-not (Test-Path $icon)) {
    & $python scripts\make_icon.py
    if ($LASTEXITCODE -ne 0) { throw "アイコンを作れませんでした" }
}

& $python -m PyInstaller office-raw-editor.spec --noconfirm --clean
if ($LASTEXITCODE -ne 0) { throw "ビルドに失敗しました" }

$folder = Join-Path $root "dist\office-raw-editor"
Copy-Item (Join-Path $root "README.md") $folder
Copy-Item (Join-Path $root "LICENSE") $folder
Copy-Item (Join-Path $root "THIRD_PARTY_NOTICES.md") $folder
# LGPL/GPL の本文と、exe に入る Python 本体のライセンス
$licenses = Join-Path $folder "licenses"
Copy-Item (Join-Path $root "licenses") $licenses -Recurse
$pythonBase = & $python -c "import sys; print(sys.base_prefix)"
Copy-Item (Join-Path $pythonBase "LICENSE.txt") (Join-Path $licenses "Python-LICENSE.txt")

$version = & $python -c "import office_raw_editor; print(office_raw_editor.__version__)"
$zip = Join-Path $root "dist\office-raw-editor-$version.zip"
# 古い zip が残っていると Compress-Archive が追記してしまうので、作り直す
Compress-Archive -Path $folder -DestinationPath $zip -CompressionLevel Optimal -Force
$size = [math]::Round((Get-Item $zip).Length / 1MB)

Write-Host ""
Write-Host "出力: $folder"
Write-Host "zip:  $zip ($size MB)"

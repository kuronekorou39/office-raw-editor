"""PyInstaller の入口。パッケージ内の相対 import を使うため、スクリプトはこの 1 行だけ。"""

import sys

from office_raw_editor.gui import main

if __name__ == "__main__":
    sys.exit(main())

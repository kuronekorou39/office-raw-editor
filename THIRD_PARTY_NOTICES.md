# Third-party notices

office-raw-editor itself is licensed under the MIT License (see `LICENSE`).
It contains or redistributes the following third-party components.

---

## Lucide icons (ISC) / Feather icons (MIT)

The SVG path data in `src/office_raw_editor/ui/icons.py` (and the application icon generated
from it) is derived from Lucide, some of which originates from Feather.

- https://lucide.dev / https://github.com/lucide-icons/lucide
- https://github.com/feathericons/feather

```
ISC License

Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2022 as part of Feather (MIT).
All other copyright (c) for Lucide are held by Lucide Contributors 2022.

Permission to use, copy, modify, and/or distribute this software for any
purpose with or without fee is hereby granted, provided that the above
copyright notice and this permission notice appear in all copies.

THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
```

```
The MIT License (MIT)

Copyright (c) 2013-2023 Cole Bemis

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

## Qt for Python (PySide6, Shiboken6) and Qt (LGPL-3.0)

The application uses Qt for Python and the Qt libraries, used under the
GNU Lesser General Public License v3.0 (`licenses/LGPL-3.0.txt`), which incorporates
the GNU General Public License v3.0 (`licenses/GPL-3.0.txt`).

- Copyright (C) The Qt Company Ltd. and other contributors.
- Source code: https://code.qt.io/cgit/pyside/pyside-setup.git/ and https://code.qt.io/cgit/qt/
- Version: the exact version is recorded in the distribution's `_internal` folder
  (`PySide6` / `shiboken6`) and in `requirements.txt`.

The Windows executable bundles the Qt libraries as separate, unmodified DLLs
(not statically linked). You may replace them with a compatible modified version,
as permitted by the LGPL.

---

## Python (PSF License) — Windows executable only

The Windows executable bundles the CPython runtime, distributed under the
Python Software Foundation License. The full text is included in the distribution as
`licenses/Python-LICENSE.txt`.

- Copyright (c) 2001 Python Software Foundation. All Rights Reserved.
- https://www.python.org/

The executable is built with PyInstaller, whose bootloader is distributed under the
GPL with a special exception that allows distribution of the resulting executable
under any license.

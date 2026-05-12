# -*- coding: utf-8 -*-

# Copyright (C) 2026 Asuka
#
# This file is part of PTZ-Cam-Tools.
#
# PTZ-Cam-Tools is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# PTZ-Cam-Tools is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with PTZ-Cam-Tools. If not, see <https://www.gnu.org/licenses/>.
# SPDX-License-Identifier: GPL-3.0-only

"""PyInstaller runtime hook: force UTF-8 mode for frozen builds.

On Windows, Python bundled by PyInstaller may default to the system's
locale encoding (e.g., GBK/cp936 on Chinese Windows) instead of UTF-8.
This hook ensures the frozen application uses UTF-8 for all I/O and
default string encoding, preventing garbled Chinese characters.
"""
import sys
import os
import io

# Force UTF-8 mode (PEP 540) — safe on all Python 3.7+
if sys.flags.utf8_mode != 1:
    # Reconfigure stdin/stdout/stderr to use UTF-8
    if hasattr(sys.stdin, 'reconfigure'):
        sys.stdin.reconfigure(encoding='utf-8', errors='replace')
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')

# Ensure filesystem encoding is UTF-8
os.environ.setdefault('PYTHONUTF8', '1')
os.environ.setdefault('PYTHONIOENCODING', 'utf-8')

# -*- coding: utf-8 -*-
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

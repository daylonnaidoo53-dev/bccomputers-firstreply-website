"""
capture.py — OS Clipboard & Selection Capture Layer for FirstReply PC.
Fetches selected or copied text and copies generated drafts back to clipboard.
Zero binary dependencies (uses native Windows Win32 API / PowerShell fallback).
Author: Daylon Naidoo · BCComputers & FirstReply PC
"""

from __future__ import annotations

import logging
import platform
import subprocess
from typing import Optional

logger = logging.getLogger(__name__)


class CaptureLayer:
    """Interfaces with OS clipboard and active window selection."""

    @staticmethod
    def get_clipboard_text() -> str:
        """Fetch current text from OS clipboard."""
        system = platform.system()

        # 1. Windows Native (Fast ctypes Win32 API)
        if system == "Windows":
            try:
                import ctypes
                from ctypes import wintypes

                user32 = ctypes.windll.user32
                kernel32 = ctypes.windll.kernel32

                CF_UNICODETEXT = 13

                if not user32.OpenClipboard(None):
                    raise RuntimeError("Failed to open clipboard")

                handle = user32.GetClipboardData(CF_UNICODETEXT)
                if not handle:
                    user32.CloseClipboard()
                    return ""

                p_data = kernel32.GlobalLock(handle)
                text = ctypes.c_wchar_p(p_data).value or ""
                kernel32.GlobalUnlock(handle)
                user32.CloseClipboard()
                return text.strip()
            except Exception as e:
                logger.debug(f"[Capture] ctypes clipboard read failed, falling back to powershell: {e}")
                # Fallback to powershell Get-Clipboard
                try:
                    res = subprocess.run(
                        ["powershell", "-NoProfile", "-Command", "Get-Clipboard"],
                        capture_output=True,
                        text=True,
                        timeout=2,
                    )
                    return res.stdout.strip()
                except Exception:
                    return ""

        # 2. macOS
        elif system == "Darwin":
            try:
                res = subprocess.run(["pbpaste"], capture_output=True, text=True, timeout=2)
                return res.stdout.strip()
            except Exception:
                return ""

        # 3. Linux (xclip / xsel)
        else:
            for cmd in [["xclip", "-selection", "clipboard", "-o"], ["xsel", "--clipboard", "--output"]]:
                try:
                    res = subprocess.run(cmd, capture_output=True, text=True, timeout=2)
                    return res.stdout.strip()
                except Exception:
                    continue
            return ""

    @staticmethod
    def set_clipboard_text(text: str) -> bool:
        """Copy generated draft text directly to the OS clipboard."""
        system = platform.system()

        if system == "Windows":
            try:
                import ctypes

                user32 = ctypes.windll.user32
                kernel32 = ctypes.windll.kernel32

                GMEM_MOVEABLE = 0x0002
                CF_UNICODETEXT = 13

                data = text.encode("utf-16le") + b"\x00\x00"

                if not user32.OpenClipboard(None):
                    return False
                user32.EmptyClipboard()

                h_mem = kernel32.GlobalAlloc(GMEM_MOVEABLE, len(data))
                if not h_mem:
                    user32.CloseClipboard()
                    return False

                p_mem = kernel32.GlobalLock(h_mem)
                ctypes.memmove(p_mem, data, len(data))
                kernel32.GlobalUnlock(h_mem)

                user32.SetClipboardData(CF_UNICODETEXT, h_mem)
                user32.CloseClipboard()
                return True
            except Exception as e:
                logger.debug(f"[Capture] ctypes clipboard write failed: {e}")
                try:
                    p = subprocess.Popen(["clip"], stdin=subprocess.PIPE, shell=True)
                    p.communicate(input=text.encode("utf-16"))
                    return True
                except Exception:
                    return False

        elif system == "Darwin":
            try:
                p = subprocess.Popen(["pbcopy"], stdin=subprocess.PIPE)
                p.communicate(input=text.encode("utf-8"))
                return True
            except Exception:
                return False

        else:
            try:
                p = subprocess.Popen(["xclip", "-selection", "clipboard"], stdin=subprocess.PIPE)
                p.communicate(input=text.encode("utf-8"))
                return True
            except Exception:
                return False

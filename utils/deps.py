"""
Dependency detection — checks that required external tools are installed
and accessible on PATH.
"""

import os
import shutil
import subprocess
import sys
from typing import Optional

from core.logger import get_logger

log = get_logger("deps")

# Map of tool -> common executable names per platform
_TOOL_EXECUTABLES: dict[str, list[str]] = {
    "ghostscript": ["gs", "gswin64c", "gswin32c"],
    "tesseract":   ["tesseract"],
    "libreoffice": ["libreoffice", "soffice"],
    "poppler":     ["pdftoppm", "pdfinfo"],   # poppler utils
}


def find_executable(name: str) -> Optional[str]:
    """Return the full path to *name* if found on PATH, else None."""
    return shutil.which(name)


def check_tool(tool_key: str) -> Optional[str]:
    """
    Check if *tool_key* (e.g. 'ghostscript') is available.

    Returns the resolved executable path, or None if not found.
    """
    candidates = _TOOL_EXECUTABLES.get(tool_key, [tool_key])
    for exe in candidates:
        path = find_executable(exe)
        if path:
            log.debug("Found %s → %s", tool_key, path)
            return path
    log.debug("%s not found on PATH", tool_key)
    return None


def require_tool(tool_key: str) -> str:
    """
    Like check_tool but raises RuntimeError if the tool is missing.

    Args:
        tool_key: Key from _TOOL_EXECUTABLES.

    Returns:
        Resolved executable path.

    Raises:
        RuntimeError: Tool is not installed / not on PATH.
    """
    path = check_tool(tool_key)
    if path is None:
        install_hints = {
            "ghostscript": "https://www.ghostscript.com/download.html",
            "tesseract":   "https://github.com/tesseract-ocr/tessdoc",
            "libreoffice": "https://www.libreoffice.org/download/",
            "poppler":     "https://poppler.freedesktop.org/",
        }
        hint = install_hints.get(tool_key, "")
        raise RuntimeError(
            f"Required tool '{tool_key}' is not installed or not on PATH.\n"
            + (f"Install from: {hint}" if hint else "")
        )
    return path


def check_python_package(package: str) -> bool:
    """Return True if *package* can be imported."""
    import importlib.util
    return importlib.util.find_spec(package) is not None


def require_python_package(package: str, install_name: Optional[str] = None) -> None:
    """
    Raise ImportError with a helpful message if *package* is missing.

    Args:
        package:      Import name, e.g. 'pdf2docx'.
        install_name: pip package name if different from *package*.
    """
    if not check_python_package(package):
        pip_name = install_name or package
        raise ImportError(
            f"Required Python package '{package}' is not installed.\n"
            f"Install with:  pip install {pip_name}"
        )


def summarise_dependencies() -> dict[str, str]:
    """
    Return a dictionary mapping each known tool to its status string.
    Useful for `pdf-tool --check-deps`.
    """
    results: dict[str, str] = {}
    for key in _TOOL_EXECUTABLES:
        path = check_tool(key)
        results[key] = path if path else "NOT FOUND"
    return results

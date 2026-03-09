"""
LibreOffice headless engine wrapper.

Used for:
- Word → PDF conversion
- PDF → Word (via Writer import)
- Any Office format → PDF
"""

import subprocess
import shutil
from pathlib import Path
from typing import Optional

from utils.deps import require_tool
from core.logger import get_logger

log = get_logger("engine.libreoffice")


def _lo_exe() -> str:
    return require_tool("libreoffice")


def convert_to_pdf(
    input_path: Path,
    output_dir: Path,
) -> Path:
    """
    Convert any LibreOffice-supported document to PDF.

    Args:
        input_path: Source document (docx, odt, pptx, xlsx, …).
        output_dir: Directory where the PDF will be written.

    Returns:
        Path to the generated PDF.

    Raises:
        RuntimeError: LibreOffice returned non-zero exit code.
        FileNotFoundError: Output PDF was not created.
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    cmd: list[str] = [
        _lo_exe(),
        "--headless",
        "--convert-to", "pdf",
        "--outdir", str(output_dir),
        str(input_path),
    ]

    log.debug("LibreOffice cmd: %s", " ".join(cmd))
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        raise RuntimeError(
            f"LibreOffice failed (exit {result.returncode}):\n{result.stderr}"
        )

    expected = output_dir / (input_path.stem + ".pdf")
    if not expected.exists():
        raise FileNotFoundError(
            f"LibreOffice did not produce expected output: {expected}"
        )

    return expected


def convert_to_docx(
    input_path: Path,
    output_dir: Path,
) -> Path:
    """
    Convert a document to DOCX using LibreOffice.

    Returns:
        Path to the generated DOCX.
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    cmd: list[str] = [
        _lo_exe(),
        "--headless",
        "--convert-to", "docx",
        "--outdir", str(output_dir),
        str(input_path),
    ]

    log.debug("LibreOffice cmd: %s", " ".join(cmd))
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        raise RuntimeError(
            f"LibreOffice failed (exit {result.returncode}):\n{result.stderr}"
        )

    expected = output_dir / (input_path.stem + ".docx")
    if not expected.exists():
        raise FileNotFoundError(
            f"LibreOffice did not produce expected output: {expected}"
        )

    return expected

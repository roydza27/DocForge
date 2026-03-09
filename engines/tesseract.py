"""
Tesseract OCR engine wrapper.

Used for extracting text from images and scanned PDFs.
"""

import subprocess
from pathlib import Path

from utils.deps import require_tool
from core.logger import get_logger

log = get_logger("engine.tesseract")


def _tess_exe() -> str:
    return require_tool("tesseract")


def image_to_text(
    image_path: Path,
    lang: str = "eng",
) -> str:
    """
    Run OCR on a single image and return the extracted text.

    Args:
        image_path: Path to the image file.
        lang:       Tesseract language code (default 'eng').

    Returns:
        Extracted text string.
    """
    tess = _tess_exe()
    cmd: list[str] = [
        tess,
        str(image_path),
        "stdout",
        "-l", lang,
        "--oem", "3",
        "--psm", "3",
    ]

    log.debug("Tesseract cmd: %s", " ".join(cmd))
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        raise RuntimeError(
            f"Tesseract failed (exit {result.returncode}):\n{result.stderr}"
        )

    return result.stdout


def image_to_pdf(
    image_path: Path,
    output_base: Path,
    lang: str = "eng",
) -> Path:
    """
    Convert an image to a searchable PDF using Tesseract.

    Args:
        image_path:  Source image.
        output_base: Output path without extension (tesseract appends .pdf).
        lang:        Tesseract language code.

    Returns:
        Path to the generated searchable PDF.
    """
    tess = _tess_exe()
    cmd: list[str] = [
        tess,
        str(image_path),
        str(output_base),
        "-l", lang,
        "pdf",
    ]

    log.debug("Tesseract PDF cmd: %s", " ".join(cmd))
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        raise RuntimeError(
            f"Tesseract PDF failed (exit {result.returncode}):\n{result.stderr}"
        )

    out = output_base.with_suffix(".pdf")
    if not out.exists():
        raise FileNotFoundError(f"Tesseract did not create: {out}")

    return out

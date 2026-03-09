"""
Ghostscript engine wrapper.

Provides Python-callable functions that invoke Ghostscript via subprocess,
with cross-platform executable detection.
"""

import subprocess
from pathlib import Path
from typing import Optional, Sequence

from utils.deps import require_tool
from core.logger import get_logger

log = get_logger("engine.ghostscript")

# Compression presets (gs -dPDFSETTINGS)
PRESETS = ("screen", "ebook", "printer", "prepress", "default")


def _gs_exe() -> str:
    """Resolve the Ghostscript executable for the current OS."""
    return require_tool("ghostscript")


def compress(
    input_path: Path,
    output_path: Path,
    preset: str = "ebook",
) -> Path:
    """
    Compress a PDF using Ghostscript.

    Args:
        input_path:  Source PDF.
        output_path: Destination PDF.
        preset:      One of screen | ebook | printer | prepress | default.

    Returns:
        Path to the compressed PDF.

    Raises:
        ValueError: Unknown preset.
        RuntimeError: Ghostscript returned non-zero exit code.
    """
    if preset not in PRESETS:
        raise ValueError(f"Unknown preset '{preset}'. Choose from: {PRESETS}")

    gs = _gs_exe()
    cmd: list[str] = [
        gs,
        "-sDEVICE=pdfwrite",
        "-dCompatibilityLevel=1.4",
        f"-dPDFSETTINGS=/{preset}",
        "-dNOPAUSE",
        "-dQUIET",
        "-dBATCH",
        f"-sOutputFile={output_path}",
        str(input_path),
    ]

    log.debug("Ghostscript cmd: %s", " ".join(cmd))

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(
            f"Ghostscript failed (exit {result.returncode}):\n{result.stderr}"
        )

    return output_path


def pdf_to_images(
    input_path: Path,
    output_dir: Path,
    dpi: int = 150,
    fmt: str = "png16m",
    prefix: str = "page",
) -> list[Path]:
    """
    Render PDF pages to image files using Ghostscript.

    Args:
        input_path: Source PDF.
        output_dir: Directory to write images into.
        dpi:        Resolution (dots per inch).
        fmt:        Ghostscript device name (png16m, jpeg, tiff24nc …).
        prefix:     Filename prefix for output images.

    Returns:
        Sorted list of generated image Paths.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    output_pattern = output_dir / f"{prefix}_%04d.png"

    gs = _gs_exe()
    cmd: list[str] = [
        gs,
        f"-sDEVICE={fmt}",
        f"-r{dpi}",
        "-dNOPAUSE",
        "-dQUIET",
        "-dBATCH",
        f"-sOutputFile={output_pattern}",
        str(input_path),
    ]

    log.debug("Ghostscript render cmd: %s", " ".join(cmd))

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(
            f"Ghostscript render failed (exit {result.returncode}):\n{result.stderr}"
        )

    images = sorted(output_dir.glob(f"{prefix}_*.png"))
    log.debug("Rendered %d page(s)", len(images))
    return images

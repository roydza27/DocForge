"""
PDF Compression module.

Engine: Ghostscript

Presets (quality vs. size):
  screen   — lowest quality, smallest size (72 dpi)
  ebook    — medium quality (150 dpi)  ← default
  printer  — high quality (300 dpi)
  prepress — highest quality (300+ dpi, colour-managed)

Usage::

    pdf-tool optimize compress report.pdf
    pdf-tool optimize compress report.pdf --preset screen
    pdf-tool optimize compress report.pdf --output report_small.pdf
"""

from pathlib import Path
from typing import Optional

from core.file_manager import (
    JobWorkspace,
    validate_input_file,
    build_output_path,
    safe_output_path,
)
from core.logger import get_logger
from core.task_manager import task_manager

log = get_logger("optimize.compress")

PRESETS = ("screen", "ebook", "printer", "prepress", "default")


def _run_compress(
    *,
    workspace: JobWorkspace,
    input_path: Path,
    output_path: Path,
    preset: str,
) -> Path:
    from engines.ghostscript import compress as gs_compress
    return gs_compress(input_path, output_path, preset=preset)


def compress(
    input_file: str | Path,
    output_file: Optional[str | Path] = None,
    output_dir: Optional[str | Path] = None,
    preset: str = "ebook",
) -> Optional[Path]:
    """
    Compress a PDF using Ghostscript.

    Args:
        input_file:  Source PDF.
        output_file: Explicit output path.
        output_dir:  Output directory.
        preset:      Ghostscript preset name.

    Returns:
        Path to the compressed PDF, or None on failure.
    """
    if preset not in PRESETS:
        print(f"ERROR: Invalid preset '{preset}'. Choose from: {PRESETS}")
        return None

    src = validate_input_file(input_file, expected_format="pdf")
    dst = (
        safe_output_path(Path(output_file))
        if output_file
        else safe_output_path(build_output_path(src, ".pdf", output_dir, "_compressed"))
    )

    original_size = src.stat().st_size
    log.info("compress: %s (%.1f MB) → %s preset=%s",
             src.name, original_size / 1024 / 1024, dst.name, preset)

    result = task_manager.run(
        fn=_run_compress,
        operation="compress",
        input_path=src,
        output_path=dst,
        preset=preset,
    )

    if result.success and result.output_path:
        new_size = result.output_path.stat().st_size
        saved = original_size - new_size
        pct = (saved / original_size * 100) if original_size > 0 else 0
        print(
            f"  Size: {original_size / 1024:.1f} KB → {new_size / 1024:.1f} KB  "
            f"({pct:.1f}% saved)"
        )

    print(result)
    return result.output_path if result.success else None

"""
PDF → Images conversion module.

Engines:
  1. pdf2image (Python wrapper around pdftoppm / Poppler)
  2. Ghostscript (fallback)

Usage::

    pdf-tool convert pdf2img report.pdf
    pdf-tool convert pdf2img report.pdf --dpi 200 --format jpeg
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

log = get_logger("convert.pdf2img")

SUPPORTED_FORMATS = {"png", "jpeg", "tiff"}


def _convert_with_pdf2image(
    input_path: Path,
    output_dir: Path,
    dpi: int,
    fmt: str,
) -> list[Path]:
    """Use the pdf2image library (requires poppler on PATH)."""
    from utils.deps import require_python_package
    require_python_package("pdf2image")

    from pdf2image import convert_from_path  # type: ignore

    log.info("Converting with pdf2image at %d DPI", dpi)
    images = convert_from_path(str(input_path), dpi=dpi, fmt=fmt)

    saved: list[Path] = []
    for i, img in enumerate(images):
        ext = "jpg" if fmt == "jpeg" else fmt
        out = output_dir / f"{input_path.stem}_page_{i + 1:04d}.{ext}"
        img.save(str(out))
        saved.append(out)
    return saved


def _convert_with_ghostscript(
    input_path: Path,
    output_dir: Path,
    dpi: int,
    fmt: str,
) -> list[Path]:
    from engines.ghostscript import pdf_to_images
    gs_fmt = "png16m" if fmt == "png" else ("jpeg" if fmt == "jpeg" else "tiff24nc")
    return pdf_to_images(input_path, output_dir, dpi=dpi, fmt=gs_fmt,
                         prefix=input_path.stem)


def _run_conversion(
    *,
    workspace: JobWorkspace,
    input_path: Path,
    output_dir: Path,
    dpi: int,
    fmt: str,
) -> Optional[Path]:
    try:
        pages = _convert_with_pdf2image(input_path, output_dir, dpi, fmt)
    except (ImportError, Exception) as err:
        log.warning("pdf2image failed (%s), trying Ghostscript…", err)
        pages = _convert_with_ghostscript(input_path, output_dir, dpi, fmt)

    if not pages:
        raise RuntimeError("No images were generated.")

    log.info("Generated %d image(s) in %s", len(pages), output_dir)
    # Return the directory so the result message is useful
    return output_dir


def convert(
    input_file: str | Path,
    output_dir: Optional[str | Path] = None,
    dpi: int = 150,
    fmt: str = "png",
) -> Optional[Path]:
    """
    Convert a PDF to individual page images.

    Args:
        input_file: Source PDF path.
        output_dir: Directory for output images (defaults to same dir as PDF).
        dpi:        Image resolution (dots per inch).
        fmt:        Output format: png | jpeg | tiff.

    Returns:
        Path to the output directory, or None on failure.
    """
    if fmt not in SUPPORTED_FORMATS:
        print(f"ERROR: Unsupported format '{fmt}'. Choose from: {SUPPORTED_FORMATS}")
        return None

    src = validate_input_file(input_file, expected_format="pdf")
    out_dir = Path(output_dir) if output_dir else src.parent / f"{src.stem}_images"
    out_dir.mkdir(parents=True, exist_ok=True)

    log.info("pdf2img: %s → %s (dpi=%d, fmt=%s)", src.name, out_dir, dpi, fmt)

    result = task_manager.run(
        fn=_run_conversion,
        operation="pdf2img",
        input_path=src,
        output_dir=out_dir,
        dpi=dpi,
        fmt=fmt,
    )

    print(result)
    return result.output_path if result.success else None

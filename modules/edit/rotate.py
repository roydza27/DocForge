"""
PDF page rotation module.

Usage::

    pdf-tool edit rotate document.pdf 90
    pdf-tool edit rotate document.pdf 180 --pages 1-3
"""

from pathlib import Path
from typing import Optional, Sequence

from core.file_manager import (
    JobWorkspace,
    validate_input_file,
    build_output_path,
    safe_output_path,
)
from core.logger import get_logger
from core.task_manager import task_manager
from modules.edit.split import parse_page_range

log = get_logger("edit.rotate")

VALID_ANGLES = {90, 180, 270}


def _run_rotate(
    *,
    workspace: JobWorkspace,
    input_path: Path,
    output_path: Path,
    angle: int,
    page_indices: Optional[list[int]],
) -> Path:
    from utils.deps import require_python_package
    require_python_package("pypdf")
    from pypdf import PdfReader, PdfWriter  # type: ignore

    reader = PdfReader(str(input_path))
    writer = PdfWriter()

    for i, page in enumerate(reader.pages):
        if page_indices is None or i in page_indices:
            page.rotate(angle)
        writer.add_page(page)

    with open(output_path, "wb") as fh:
        writer.write(fh)

    return output_path


def rotate(
    input_file: str | Path,
    angle: int,
    pages: Optional[str] = None,
    output_file: Optional[str | Path] = None,
    output_dir: Optional[str | Path] = None,
) -> Optional[Path]:
    """
    Rotate pages in a PDF.

    Args:
        input_file: Source PDF.
        angle:      Rotation in degrees: 90 | 180 | 270.
        pages:      Page range string (e.g. "1-3,5"). If None, rotates all pages.
        output_file: Explicit output path.
        output_dir:  Output directory.

    Returns:
        Path to the rotated PDF, or None on failure.
    """
    if angle not in VALID_ANGLES:
        print(f"ERROR: Angle must be one of {VALID_ANGLES}, got {angle}.")
        return None

    src = validate_input_file(input_file, expected_format="pdf")
    dst = (
        safe_output_path(Path(output_file))
        if output_file
        else safe_output_path(build_output_path(src, ".pdf", output_dir, "_rotated"))
    )

    # Parse page indices if specified
    page_indices: Optional[list[int]] = None
    if pages:
        from pypdf import PdfReader  # type: ignore
        total = len(PdfReader(str(src)).pages)
        page_indices = parse_page_range(pages, total)

    log.info("rotate: %s angle=%d pages=%s → %s", src.name, angle, pages, dst.name)

    result = task_manager.run(
        fn=_run_rotate,
        operation="rotate",
        input_path=src,
        output_path=dst,
        angle=angle,
        page_indices=page_indices,
    )

    print(result)
    return result.output_path if result.success else None

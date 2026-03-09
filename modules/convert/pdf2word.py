"""
PDF → Word (DOCX) conversion module.

Primary engine: pdf2docx (Python library)
Fallback engine: LibreOffice headless

Usage via CLI::

    pdf-tool convert pdf2word report.pdf
    pdf-tool convert pdf2word report.pdf --output /path/to/output.docx

Programmatic usage::

    from modules.convert.pdf2word import convert
    result = convert("report.pdf")
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

log = get_logger("convert.pdf2word")


# ── Primary engine: pdf2docx ──────────────────────────────────────────────────

def _convert_with_pdf2docx(
    input_path: Path,
    output_path: Path,
    workspace: JobWorkspace,
) -> Path:
    """
    Convert using the pdf2docx Python library.

    Raises ImportError if pdf2docx is not installed (triggers fallback).
    """
    from utils.deps import require_python_package
    require_python_package("pdf2docx")

    from pdf2docx import Converter  # type: ignore

    log.info("Converting with pdf2docx: %s", input_path.name)
    cv = Converter(str(input_path))
    cv.convert(str(output_path), start=0, end=None)
    cv.close()

    if not output_path.exists() or output_path.stat().st_size == 0:
        raise RuntimeError("pdf2docx produced no output.")

    return output_path


# ── Fallback engine: LibreOffice ──────────────────────────────────────────────

def _convert_with_libreoffice(
    input_path: Path,
    output_path: Path,
    workspace: JobWorkspace,
) -> Path:
    """
    Convert via LibreOffice headless as a fallback.
    """
    from engines.libreoffice import convert_to_docx

    log.info("Falling back to LibreOffice: %s", input_path.name)
    tmp_docx = convert_to_docx(input_path, workspace.path)

    # Move to the desired output path
    import shutil
    shutil.move(str(tmp_docx), str(output_path))
    return output_path


# ── Public API ────────────────────────────────────────────────────────────────

def _run_conversion(
    *,
    workspace: JobWorkspace,
    input_path: Path,
    output_path: Path,
) -> Path:
    """Internal task callable executed by TaskManager."""
    # Try pdf2docx first; fall back to LibreOffice
    try:
        return _convert_with_pdf2docx(input_path, output_path, workspace)
    except (ImportError, Exception) as primary_err:
        log.warning("pdf2docx failed (%s), trying LibreOffice…", primary_err)
        return _convert_with_libreoffice(input_path, output_path, workspace)


def convert(
    input_file: str | Path,
    output_file: Optional[str | Path] = None,
    output_dir: Optional[str | Path] = None,
) -> Optional[Path]:
    """
    Convert a PDF file to a Word document (.docx).

    Args:
        input_file:  Path to the source PDF.
        output_file: Explicit output file path. If omitted, derived automatically.
        output_dir:  Directory for the output file (ignored if output_file given).

    Returns:
        Path to the generated DOCX, or None on failure.
    """
    # 1 — Validate input
    src = validate_input_file(input_file, expected_format="pdf")

    # 2 — Determine output path
    if output_file:
        dst = safe_output_path(Path(output_file))
    else:
        dst = safe_output_path(build_output_path(src, ".docx", output_dir))

    log.info("pdf2word: %s → %s", src.name, dst.name)

    # 3 — Execute via TaskManager
    result = task_manager.run(
        fn=_run_conversion,
        operation="pdf2word",
        input_path=src,
        output_path=dst,
    )

    print(result)
    return result.output_path if result.success else None

"""
Word (DOCX/DOC) → PDF conversion module.

Engine: LibreOffice headless

Usage::

    pdf-tool convert word2pdf report.docx
    pdf-tool convert word2pdf report.docx --output /path/to/report.pdf
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

log = get_logger("convert.word2pdf")


def _run_conversion(
    *,
    workspace: JobWorkspace,
    input_path: Path,
    output_path: Path,
) -> Path:
    import shutil
    from engines.libreoffice import convert_to_pdf

    tmp_pdf = convert_to_pdf(input_path, workspace.path)
    shutil.move(str(tmp_pdf), str(output_path))
    return output_path


def convert(
    input_file: str | Path,
    output_file: Optional[str | Path] = None,
    output_dir: Optional[str | Path] = None,
) -> Optional[Path]:
    """
    Convert a Word document to PDF.

    Args:
        input_file:  Path to the source DOCX/DOC file.
        output_file: Explicit output path; auto-derived if omitted.
        output_dir:  Output directory (ignored if output_file given).

    Returns:
        Path to the generated PDF, or None on failure.
    """
    src = validate_input_file(input_file, expected_format="word")

    dst = (
        safe_output_path(Path(output_file))
        if output_file
        else safe_output_path(build_output_path(src, ".pdf", output_dir))
    )

    log.info("word2pdf: %s → %s", src.name, dst.name)

    result = task_manager.run(
        fn=_run_conversion,
        operation="word2pdf",
        input_path=src,
        output_path=dst,
    )

    print(result)
    return result.output_path if result.success else None

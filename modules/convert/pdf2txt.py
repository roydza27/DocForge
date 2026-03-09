"""
PDF → Text extraction module.

Engine: pdfminer.six (pure Python, no external tools required)

Usage::

    pdf-tool convert pdf2txt report.pdf
    pdf-tool convert pdf2txt report.pdf --output report.txt
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

log = get_logger("convert.pdf2txt")


def _run_extraction(
    *,
    workspace: JobWorkspace,
    input_path: Path,
    output_path: Path,
) -> Path:
    from utils.deps import require_python_package
    require_python_package("pdfminer", install_name="pdfminer.six")

    from pdfminer.high_level import extract_text  # type: ignore

    text = extract_text(str(input_path))
    output_path.write_text(text, encoding="utf-8")
    return output_path


def convert(
    input_file: str | Path,
    output_file: Optional[str | Path] = None,
    output_dir: Optional[str | Path] = None,
) -> Optional[Path]:
    """
    Extract text from a PDF and save as a .txt file.

    Args:
        input_file:  Source PDF.
        output_file: Explicit output path; auto-derived if omitted.
        output_dir:  Output directory.

    Returns:
        Path to the generated text file, or None on failure.
    """
    src = validate_input_file(input_file, expected_format="pdf")
    dst = (
        safe_output_path(Path(output_file))
        if output_file
        else safe_output_path(build_output_path(src, ".txt", output_dir))
    )

    log.info("pdf2txt: %s → %s", src.name, dst.name)

    result = task_manager.run(
        fn=_run_extraction,
        operation="pdf2txt",
        input_path=src,
        output_path=dst,
    )

    print(result)
    return result.output_path if result.success else None

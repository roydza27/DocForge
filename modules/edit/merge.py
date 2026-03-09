"""
PDF Merge module.

Combines two or more PDF files into a single PDF.

Usage::

    pdf-tool edit merge a.pdf b.pdf c.pdf
    pdf-tool edit merge *.pdf --output combined.pdf
"""

from pathlib import Path
from typing import Optional, Sequence

from core.file_manager import (
    JobWorkspace,
    validate_multiple_inputs,
    safe_output_path,
)
from core.logger import get_logger
from core.task_manager import task_manager

log = get_logger("edit.merge")


def _run_merge(
    *,
    workspace: JobWorkspace,
    input_paths: list[Path],
    output_path: Path,
) -> Path:
    from utils.deps import require_python_package
    require_python_package("pypdf")

    from pypdf import PdfWriter  # type: ignore

    writer = PdfWriter()
    for pdf_path in input_paths:
        writer.append(str(pdf_path))
        log.debug("Appended: %s", pdf_path.name)

    with open(output_path, "wb") as fh:
        writer.write(fh)

    if not output_path.exists() or output_path.stat().st_size == 0:
        raise RuntimeError("Merge produced no output.")

    return output_path


def merge(
    input_files: Sequence[str | Path],
    output_file: Optional[str | Path] = None,
    output_dir: Optional[str | Path] = None,
) -> Optional[Path]:
    """
    Merge multiple PDFs into one.

    Args:
        input_files: Two or more PDF paths.
        output_file: Explicit output path.
        output_dir:  Output directory (used when output_file is omitted).

    Returns:
        Path to the merged PDF, or None on failure.
    """
    if len(list(input_files)) < 2:
        print("ERROR: At least two input files are required for merging.")
        return None

    sources = validate_multiple_inputs(input_files, expected_format="pdf")

    if output_file:
        dst = safe_output_path(Path(output_file))
    else:
        out_dir = Path(output_dir) if output_dir else sources[0].parent
        dst = safe_output_path(out_dir / "merged.pdf")

    log.info("merge: %d PDFs → %s", len(sources), dst.name)

    result = task_manager.run(
        fn=_run_merge,
        operation="merge",
        input_paths=sources,
        output_path=dst,
    )

    print(result)
    return result.output_path if result.success else None

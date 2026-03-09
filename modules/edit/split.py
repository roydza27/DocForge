"""
PDF Split module.

Splits a PDF by page ranges.

Usage::

    pdf-tool edit split document.pdf 1-5
    pdf-tool edit split document.pdf 1-3 4-6 7-10
    pdf-tool edit split document.pdf --every 5        # every 5 pages
"""

import re
from pathlib import Path
from typing import Optional, Sequence

from core.file_manager import (
    JobWorkspace,
    validate_input_file,
    safe_output_path,
)
from core.logger import get_logger
from core.task_manager import task_manager

log = get_logger("edit.split")


def parse_page_range(spec: str, total_pages: int) -> list[int]:
    """
    Parse a page range specification into a list of 0-based page indices.

    Supports:
      - "3"       → [2]
      - "1-5"     → [0,1,2,3,4]
      - "3,7,9"   → [2,6,8]
      - "2-"      → page 2 to last
    """
    spec = spec.strip()
    pages: set[int] = set()

    for part in spec.split(","):
        part = part.strip()
        if not part:
            continue
        m_range = re.fullmatch(r"(\d+)-(\d*)", part)
        m_single = re.fullmatch(r"(\d+)", part)

        if m_range:
            start = int(m_range.group(1))
            end = int(m_range.group(2)) if m_range.group(2) else total_pages
            pages.update(range(start - 1, end))
        elif m_single:
            pages.add(int(m_single.group(1)) - 1)
        else:
            raise ValueError(f"Invalid page range: '{part}'")

    valid = sorted(p for p in pages if 0 <= p < total_pages)
    if not valid:
        raise ValueError(
            f"No valid pages in range '{spec}' (document has {total_pages} pages)."
        )
    return valid


def _run_split(
    *,
    workspace: JobWorkspace,
    input_path: Path,
    ranges: list[str],
    output_dir: Path,
) -> Path:
    from utils.deps import require_python_package
    require_python_package("pypdf")

    from pypdf import PdfReader, PdfWriter  # type: ignore

    reader = PdfReader(str(input_path))
    total = len(reader.pages)
    log.debug("Source PDF has %d pages", total)

    output_dir.mkdir(parents=True, exist_ok=True)
    created: list[Path] = []

    for i, spec in enumerate(ranges, start=1):
        page_indices = parse_page_range(spec, total)

        writer = PdfWriter()
        for idx in page_indices:
            writer.add_page(reader.pages[idx])

        out = safe_output_path(
            output_dir / f"{input_path.stem}_part{i:02d}.pdf"
        )
        with open(out, "wb") as fh:
            writer.write(fh)
        created.append(out)
        log.debug("Wrote %s (%d pages)", out.name, len(page_indices))

    log.info("Split into %d file(s) in %s", len(created), output_dir)
    return output_dir


def split(
    input_file: str | Path,
    ranges: Sequence[str],
    output_dir: Optional[str | Path] = None,
) -> Optional[Path]:
    """
    Split a PDF by page ranges.

    Args:
        input_file: Source PDF.
        ranges:     One or more range strings like "1-5", "3,7,9".
        output_dir: Directory for output files (defaults to input dir).

    Returns:
        Path to the output directory, or None on failure.
    """
    src = validate_input_file(input_file, expected_format="pdf")
    out_dir = Path(output_dir) if output_dir else src.parent
    range_list = list(ranges)

    if not range_list:
        print("ERROR: At least one page range is required.")
        return None

    log.info("split: %s → %d part(s)", src.name, len(range_list))

    result = task_manager.run(
        fn=_run_split,
        operation="split",
        input_path=src,
        ranges=range_list,
        output_dir=out_dir,
    )

    print(result)
    return result.output_path if result.success else None


def split_every(
    input_file: str | Path,
    every: int,
    output_dir: Optional[str | Path] = None,
) -> Optional[Path]:
    """
    Split a PDF every N pages.

    Args:
        input_file: Source PDF.
        every:      Number of pages per output chunk.
        output_dir: Directory for output files.
    """
    from utils.deps import require_python_package
    require_python_package("pypdf")
    from pypdf import PdfReader  # type: ignore

    src = validate_input_file(input_file, expected_format="pdf")
    total = len(PdfReader(str(src)).pages)

    ranges = [
        f"{start}-{min(start + every - 1, total)}"
        for start in range(1, total + 1, every)
    ]
    return split(src, ranges, output_dir)

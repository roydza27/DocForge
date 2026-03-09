"""
OCR module — convert scanned PDFs to searchable PDFs.

Workflow:
  1. Detect if PDF is scanned (text-only detection using pdfminer).
  2. Render each page to an image (Ghostscript).
  3. Run Tesseract OCR on each image → per-page PDF.
  4. Merge per-page PDFs into a single searchable PDF.

Usage::

    pdf-tool ocr scanned_report.pdf
    pdf-tool ocr scanned_report.pdf --lang deu
    pdf-tool ocr scanned_report.pdf --output searchable.pdf
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

log = get_logger("ocr")


def is_scanned_pdf(input_path: Path) -> bool:
    """
    Heuristic: if the PDF contains very little extractable text
    (< 100 chars per page on average) it is likely scanned.
    """
    try:
        from utils.deps import require_python_package
        require_python_package("pdfminer", install_name="pdfminer.six")
        from pdfminer.high_level import extract_text  # type: ignore

        text = extract_text(str(input_path))
        from pypdf import PdfReader  # type: ignore
        pages = len(PdfReader(str(input_path)).pages)
        avg_chars = len(text.strip()) / max(pages, 1)
        log.debug("Avg chars/page: %.1f", avg_chars)
        return avg_chars < 100
    except Exception:
        return True  # assume scanned if detection fails


def _run_ocr(
    *,
    workspace: JobWorkspace,
    input_path: Path,
    output_path: Path,
    lang: str,
) -> Path:
    from engines.ghostscript import pdf_to_images
    from engines.tesseract import image_to_pdf
    from utils.deps import require_python_package

    require_python_package("pypdf")
    from pypdf import PdfWriter  # type: ignore

    # Step 1 — Render pages to images
    images_dir = workspace.path / "pages"
    images = pdf_to_images(input_path, images_dir, dpi=300, prefix="page")

    if not images:
        raise RuntimeError("No pages rendered from PDF.")

    log.info("OCR: processing %d page(s) with lang='%s'", len(images), lang)

    # Step 2 — OCR each page image → per-page searchable PDF
    page_pdfs: list[Path] = []
    for img_path in images:
        base = workspace.path / img_path.stem
        page_pdf = image_to_pdf(img_path, base, lang=lang)
        page_pdfs.append(page_pdf)
        log.debug("OCR'd page: %s", page_pdf.name)

    # Step 3 — Merge all page PDFs into one
    writer = PdfWriter()
    for pp in page_pdfs:
        writer.append(str(pp))

    with open(output_path, "wb") as fh:
        writer.write(fh)

    return output_path


def ocr(
    input_file: str | Path,
    output_file: Optional[str | Path] = None,
    output_dir: Optional[str | Path] = None,
    lang: str = "eng",
    force: bool = False,
) -> Optional[Path]:
    """
    Convert a scanned PDF to a searchable PDF using OCR.

    Args:
        input_file:  Source PDF (ideally scanned).
        output_file: Explicit output path.
        output_dir:  Output directory.
        lang:        Tesseract language code (default 'eng').
        force:       Run OCR even if PDF appears to have text.

    Returns:
        Path to the searchable PDF, or None on failure.
    """
    src = validate_input_file(input_file, expected_format="pdf")

    if not force:
        scanned = is_scanned_pdf(src)
        if not scanned:
            print(
                f"  Note: '{src.name}' appears to already contain text. "
                "Use --force to run OCR anyway."
            )

    dst = (
        safe_output_path(Path(output_file))
        if output_file
        else safe_output_path(build_output_path(src, ".pdf", output_dir, "_ocr"))
    )

    log.info("ocr: %s (lang=%s) → %s", src.name, lang, dst.name)

    result = task_manager.run(
        fn=_run_ocr,
        operation="ocr",
        input_path=src,
        output_path=dst,
        lang=lang,
    )

    print(result)
    return result.output_path if result.success else None

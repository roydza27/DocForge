"""
Images → PDF conversion module.

Combines one or more images into a single PDF.
Engine: Pillow (pure-Python, no external tool required)

Usage::

    pdf-tool convert img2pdf photo1.png photo2.jpg
    pdf-tool convert img2pdf *.png --output album.pdf
"""

from pathlib import Path
from typing import Optional, Sequence

from core.file_manager import (
    JobWorkspace,
    validate_multiple_inputs,
    safe_output_path,
    build_output_path,
)
from core.logger import get_logger
from core.task_manager import task_manager

log = get_logger("convert.img2pdf")


def _run_conversion(
    *,
    workspace: JobWorkspace,
    image_paths: list[Path],
    output_path: Path,
) -> Path:
    from utils.deps import require_python_package
    require_python_package("PIL", install_name="Pillow")

    from PIL import Image  # type: ignore

    images = []
    for img_path in image_paths:
        img = Image.open(img_path).convert("RGB")
        images.append(img)

    if not images:
        raise RuntimeError("No valid images to combine.")

    first, rest = images[0], images[1:]
    first.save(
        output_path,
        save_all=True,
        append_images=rest,
        resolution=150,
    )

    if not output_path.exists() or output_path.stat().st_size == 0:
        raise RuntimeError("img2pdf produced no output.")

    return output_path


def convert(
    input_files: Sequence[str | Path],
    output_file: Optional[str | Path] = None,
    output_dir: Optional[str | Path] = None,
) -> Optional[Path]:
    """
    Combine images into a PDF.

    Args:
        input_files: One or more image file paths.
        output_file: Explicit output path; auto-derived if omitted.
        output_dir:  Output directory (ignored if output_file given).

    Returns:
        Path to the generated PDF, or None on failure.
    """
    sources = validate_multiple_inputs(input_files, expected_format="image")

    if output_file:
        dst = safe_output_path(Path(output_file))
    else:
        first = sources[0]
        dst = safe_output_path(build_output_path(first, ".pdf", output_dir,
                                                  "_combined" if len(sources) > 1 else ""))

    log.info("img2pdf: %d image(s) → %s", len(sources), dst.name)

    result = task_manager.run(
        fn=_run_conversion,
        operation="img2pdf",
        image_paths=sources,
        output_path=dst,
    )

    print(result)
    return result.output_path if result.success else None

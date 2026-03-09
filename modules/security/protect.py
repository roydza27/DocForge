"""
PDF Security modules — protect and unlock.

Usage::

    pdf-tool security protect document.pdf "my_password"
    pdf-tool security unlock document.pdf "my_password"
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

log = get_logger("security")


# ── Protect ───────────────────────────────────────────────────────────────────

def _run_protect(
    *,
    workspace: JobWorkspace,
    input_path: Path,
    output_path: Path,
    password: str,
) -> Path:
    from utils.deps import require_python_package
    require_python_package("pypdf")
    from pypdf import PdfReader, PdfWriter  # type: ignore

    reader = PdfReader(str(input_path))
    writer = PdfWriter()
    writer.append_pages_from_reader(reader)
    writer.encrypt(password)

    with open(output_path, "wb") as fh:
        writer.write(fh)

    return output_path


def protect(
    input_file: str | Path,
    password: str,
    output_file: Optional[str | Path] = None,
    output_dir: Optional[str | Path] = None,
) -> Optional[Path]:
    """
    Add password protection to a PDF.

    Args:
        input_file: Source PDF.
        password:   Password to apply.
        output_file: Explicit output path.
        output_dir:  Output directory.
    """
    if not password:
        print("ERROR: Password cannot be empty.")
        return None

    src = validate_input_file(input_file, expected_format="pdf")
    dst = (
        safe_output_path(Path(output_file))
        if output_file
        else safe_output_path(build_output_path(src, ".pdf", output_dir, "_protected"))
    )

    log.info("protect: %s → %s", src.name, dst.name)

    result = task_manager.run(
        fn=_run_protect,
        operation="protect",
        input_path=src,
        output_path=dst,
        password=password,
    )

    print(result)
    return result.output_path if result.success else None


# ── Unlock ────────────────────────────────────────────────────────────────────

def _run_unlock(
    *,
    workspace: JobWorkspace,
    input_path: Path,
    output_path: Path,
    password: str,
) -> Path:
    from utils.deps import require_python_package
    require_python_package("pypdf")
    from pypdf import PdfReader, PdfWriter  # type: ignore

    reader = PdfReader(str(input_path))
    if reader.is_encrypted:
        if not reader.decrypt(password):
            raise ValueError("Incorrect password — could not unlock PDF.")

    writer = PdfWriter()
    writer.append_pages_from_reader(reader)

    with open(output_path, "wb") as fh:
        writer.write(fh)

    return output_path


def unlock(
    input_file: str | Path,
    password: str,
    output_file: Optional[str | Path] = None,
    output_dir: Optional[str | Path] = None,
) -> Optional[Path]:
    """
    Remove password protection from a PDF.

    Args:
        input_file: Encrypted source PDF.
        password:   Password to decrypt with.
        output_file: Explicit output path.
        output_dir:  Output directory.
    """
    src = validate_input_file(input_file, expected_format="pdf")
    dst = (
        safe_output_path(Path(output_file))
        if output_file
        else safe_output_path(build_output_path(src, ".pdf", output_dir, "_unlocked"))
    )

    log.info("unlock: %s → %s", src.name, dst.name)

    result = task_manager.run(
        fn=_run_unlock,
        operation="unlock",
        input_path=src,
        output_path=dst,
        password=password,
    )

    print(result)
    return result.output_path if result.success else None

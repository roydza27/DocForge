"""
Cross-platform file management utilities.

Handles:
- Input validation
- Temporary workspace creation/cleanup
- Output path generation
- Job ID creation
"""

import os
import shutil
import tempfile
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional, Sequence

from core.config import CONFIG
from core.logger import get_logger

log = get_logger("file_manager")

# Supported input formats for basic validation
SUPPORTED_FORMATS: dict[str, set[str]] = {
    "pdf":   {".pdf"},
    "word":  {".doc", ".docx"},
    "image": {".png", ".jpg", ".jpeg", ".tiff", ".tif", ".bmp", ".gif", ".webp"},
    "text":  {".txt"},
    "any":   {".pdf", ".doc", ".docx", ".png", ".jpg", ".jpeg",
               ".tiff", ".tif", ".bmp", ".gif", ".webp", ".txt"},
}

MAX_FILE_SIZE_BYTES = 500 * 1024 * 1024  # 500 MB


# ── Job ID ────────────────────────────────────────────────────────────────────

def generate_job_id() -> str:
    """Generate a unique job identifier."""
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    uid = uuid.uuid4().hex[:6]
    return f"job_{ts}_{uid}"


# ── Validation ────────────────────────────────────────────────────────────────

def validate_input_file(
    path: str | Path,
    expected_format: str = "any",
) -> Path:
    """
    Validate that a file exists, is readable, is the right format,
    and does not exceed the size limit.

    Args:
        path: Path to the input file.
        expected_format: One of the keys in SUPPORTED_FORMATS.

    Returns:
        Resolved Path object.

    Raises:
        FileNotFoundError: File does not exist.
        ValueError: Format mismatch or file too large.
        PermissionError: File is not readable.
    """
    p = Path(path).resolve()

    if not p.exists():
        raise FileNotFoundError(f"Input file not found: {p}")

    if not p.is_file():
        raise ValueError(f"Path is not a file: {p}")

    if not os.access(p, os.R_OK):
        raise PermissionError(f"Cannot read file: {p}")

    size = p.stat().st_size
    if size == 0:
        raise ValueError(f"File is empty: {p}")
    if size > MAX_FILE_SIZE_BYTES:
        raise ValueError(
            f"File exceeds 500 MB limit ({size / 1024 / 1024:.1f} MB): {p}"
        )

    allowed_ext = SUPPORTED_FORMATS.get(expected_format, SUPPORTED_FORMATS["any"])
    if p.suffix.lower() not in allowed_ext:
        raise ValueError(
            f"Unsupported file format '{p.suffix}'. "
            f"Expected one of: {sorted(allowed_ext)}"
        )

    return p


def validate_multiple_inputs(
    paths: Sequence[str | Path],
    expected_format: str = "any",
) -> list[Path]:
    """Validate a list of input files and return resolved Paths."""
    return [validate_input_file(p, expected_format) for p in paths]


# ── Temp workspace ────────────────────────────────────────────────────────────

class JobWorkspace:
    """
    Context manager that creates and auto-cleans a temporary
    working directory for a single job.

    Usage::

        with JobWorkspace() as ws:
            ws.job_id   # unique ID string
            ws.path     # Path to temp dir
    """

    def __init__(self, job_id: Optional[str] = None) -> None:
        self.job_id = job_id or generate_job_id()
        self.path: Path = CONFIG["temp_dir"] / self.job_id
        self.path.mkdir(parents=True, exist_ok=True)
        log.debug("Created workspace: %s", self.path)

    def __enter__(self) -> "JobWorkspace":
        return self

    def __exit__(self, *_) -> None:
        self.cleanup()

    def cleanup(self) -> None:
        """Remove the temporary workspace directory."""
        if self.path.exists():
            shutil.rmtree(self.path, ignore_errors=True)
            log.debug("Cleaned workspace: %s", self.path)

    def temp_path(self, filename: str) -> Path:
        """Return a path inside the workspace."""
        return self.path / filename


# ── Output naming ─────────────────────────────────────────────────────────────

def build_output_path(
    input_path: str | Path,
    new_suffix: str,
    output_dir: Optional[str | Path] = None,
    suffix_label: str = "",
) -> Path:
    """
    Build a sensible output file path.

    Args:
        input_path:   Original input file path.
        new_suffix:   Target file extension, e.g. ".docx".
        output_dir:   Directory for output. Defaults to input file's directory.
        suffix_label: Optional label appended before extension, e.g. "_merged".

    Returns:
        Path for the output file.
    """
    inp = Path(input_path)
    stem = inp.stem + suffix_label
    out_dir = Path(output_dir) if output_dir else inp.parent
    out_dir.mkdir(parents=True, exist_ok=True)
    return out_dir / f"{stem}{new_suffix}"


def safe_output_path(path: Path) -> Path:
    """
    If *path* already exists, append a counter to avoid overwriting.

    E.g.  resume.docx → resume_1.docx → resume_2.docx
    """
    if not path.exists():
        return path
    counter = 1
    while True:
        candidate = path.parent / f"{path.stem}_{counter}{path.suffix}"
        if not candidate.exists():
            return candidate
        counter += 1

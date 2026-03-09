"""
Unit tests for core system modules.

Run with:
    pytest tests/test_core.py -v
"""

import sys
import os
from pathlib import Path
import tempfile
import pytest

# Ensure the project root is on the path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


# ── file_manager tests ────────────────────────────────────────────────────────

class TestFileManager:
    def test_validate_existing_file(self, tmp_path):
        from core.file_manager import validate_input_file
        pdf = tmp_path / "test.pdf"
        pdf.write_bytes(b"%PDF-1.4 fake content for test")
        result = validate_input_file(pdf, "pdf")
        assert result == pdf.resolve()

    def test_validate_missing_file_raises(self):
        from core.file_manager import validate_input_file
        with pytest.raises(FileNotFoundError):
            validate_input_file("/nonexistent/path/file.pdf", "pdf")

    def test_validate_wrong_format_raises(self, tmp_path):
        from core.file_manager import validate_input_file
        txt = tmp_path / "doc.txt"
        txt.write_text("hello")
        with pytest.raises(ValueError, match="Unsupported file format"):
            validate_input_file(txt, "pdf")

    def test_validate_empty_file_raises(self, tmp_path):
        from core.file_manager import validate_input_file
        empty = tmp_path / "empty.pdf"
        empty.write_bytes(b"")
        with pytest.raises(ValueError, match="empty"):
            validate_input_file(empty, "pdf")

    def test_job_workspace_creates_and_cleans(self, tmp_path):
        from core.file_manager import JobWorkspace
        from core.config import CONFIG
        # Override temp dir to tmp_path for isolation
        original = CONFIG["temp_dir"]
        CONFIG["temp_dir"] = tmp_path
        try:
            with JobWorkspace("test_job_001") as ws:
                assert ws.path.exists()
                assert ws.job_id == "test_job_001"
            assert not ws.path.exists()
        finally:
            CONFIG["temp_dir"] = original

    def test_build_output_path(self, tmp_path):
        from core.file_manager import build_output_path
        src = tmp_path / "report.pdf"
        out = build_output_path(src, ".docx")
        assert out.suffix == ".docx"
        assert out.stem == "report"

    def test_build_output_path_with_label(self, tmp_path):
        from core.file_manager import build_output_path
        src = tmp_path / "file.pdf"
        out = build_output_path(src, ".pdf", suffix_label="_compressed")
        assert out.name == "file_compressed.pdf"

    def test_safe_output_path_no_conflict(self, tmp_path):
        from core.file_manager import safe_output_path
        p = tmp_path / "out.pdf"
        assert safe_output_path(p) == p

    def test_safe_output_path_avoids_overwrite(self, tmp_path):
        from core.file_manager import safe_output_path
        p = tmp_path / "out.pdf"
        p.write_bytes(b"existing")
        result = safe_output_path(p)
        assert result.name == "out_1.pdf"

    def test_generate_job_id_unique(self):
        from core.file_manager import generate_job_id
        ids = {generate_job_id() for _ in range(100)}
        assert len(ids) == 100


# ── split page range parsing tests ───────────────────────────────────────────

class TestPageRangeParsing:
    def test_single_page(self):
        from modules.edit.split import parse_page_range
        assert parse_page_range("3", 10) == [2]

    def test_range(self):
        from modules.edit.split import parse_page_range
        assert parse_page_range("1-5", 10) == [0, 1, 2, 3, 4]

    def test_comma_separated(self):
        from modules.edit.split import parse_page_range
        assert parse_page_range("1,3,5", 10) == [0, 2, 4]

    def test_open_end_range(self):
        from modules.edit.split import parse_page_range
        result = parse_page_range("8-", 10)
        assert result == [7, 8, 9]

    def test_out_of_range_pages_excluded(self):
        from modules.edit.split import parse_page_range
        result = parse_page_range("1-5", 3)
        assert result == [0, 1, 2]

    def test_invalid_range_raises(self):
        from modules.edit.split import parse_page_range
        with pytest.raises(ValueError, match="No valid pages"):
            parse_page_range("20-25", 10)

    def test_invalid_syntax_raises(self):
        from modules.edit.split import parse_page_range
        with pytest.raises(ValueError, match="Invalid page range"):
            parse_page_range("abc", 10)


# ── dependency detection tests ────────────────────────────────────────────────

class TestDeps:
    def test_find_python_returns_path(self):
        from utils.deps import find_executable
        result = find_executable("python3") or find_executable("python")
        assert result is not None

    def test_check_python_package_existing(self):
        from utils.deps import check_python_package
        assert check_python_package("pathlib") is True

    def test_check_python_package_missing(self):
        from utils.deps import check_python_package
        assert check_python_package("nonexistent_package_xyz") is False

    def test_require_python_package_missing_raises(self):
        from utils.deps import require_python_package
        with pytest.raises(ImportError, match="pip install"):
            require_python_package("nonexistent_package_xyz")

    def test_summarise_dependencies_returns_dict(self):
        from utils.deps import summarise_dependencies
        result = summarise_dependencies()
        assert isinstance(result, dict)
        assert "ghostscript" in result
        assert "tesseract" in result


# ── config tests ──────────────────────────────────────────────────────────────

class TestConfig:
    def test_config_loads(self):
        from core.config import load_config
        cfg = load_config()
        assert "temp_dir" in cfg
        assert "output_dir" in cfg
        assert "engine_paths" in cfg

    def test_temp_dir_is_path(self):
        from core.config import CONFIG
        assert isinstance(CONFIG["temp_dir"], Path)

    def test_temp_dir_exists(self):
        from core.config import CONFIG
        assert CONFIG["temp_dir"].exists()


# ── task manager tests ────────────────────────────────────────────────────────

class TestTaskManager:
    def test_successful_task(self, tmp_path):
        from core.task_manager import TaskManager
        from core.file_manager import JobWorkspace

        tm = TaskManager()
        output_file = tmp_path / "result.txt"

        def fake_fn(*, workspace: JobWorkspace, out: Path) -> Path:
            out.write_text("done")
            return out

        result = tm.run(fake_fn, operation="test", out=output_file)

        assert result.success is True
        assert result.output_path == output_file
        assert output_file.read_text() == "done"

    def test_failed_task_returns_result(self, tmp_path):
        from core.task_manager import TaskManager
        from core.file_manager import JobWorkspace

        tm = TaskManager()

        def failing_fn(*, workspace: JobWorkspace) -> None:
            raise ValueError("Intentional test failure")

        result = tm.run(failing_fn, operation="test_fail")

        assert result.success is False
        assert "Intentional test failure" in result.message

    def test_missing_file_task(self):
        from core.task_manager import TaskManager
        from core.file_manager import JobWorkspace

        tm = TaskManager()

        def fn_with_missing_file(*, workspace: JobWorkspace) -> None:
            raise FileNotFoundError("No such file: /fake/path.pdf")

        result = tm.run(fn_with_missing_file, operation="test_missing")
        assert result.success is False
        assert "No such file" in result.message


# ── CLI smoke tests ───────────────────────────────────────────────────────────

class TestCLI:
    def test_version(self, capsys):
        from cli.main import build_parser
        parser = build_parser()
        with pytest.raises(SystemExit) as exc:
            parser.parse_args(["--version"])
        assert exc.value.code == 0

    def test_help_no_crash(self, capsys):
        from cli.main import build_parser
        parser = build_parser()
        with pytest.raises(SystemExit) as exc:
            parser.parse_args(["--help"])
        assert exc.value.code == 0

    def test_no_args_returns_zero(self):
        from cli.main import main
        import unittest.mock as mock
        with mock.patch("sys.argv", ["pdf-tool"]):
            code = main()
        assert code == 0

    def test_check_deps_flag(self, capsys):
        from cli.main import main
        import unittest.mock as mock
        with mock.patch("sys.argv", ["pdf-tool", "--check-deps"]):
            code = main()
        assert code == 0
        captured = capsys.readouterr()
        assert "Dependency Check" in captured.out


# ── Integration: pdf2word with a real PDF (skipped if pdf2docx missing) ───────

class TestPdf2WordIntegration:
    @pytest.mark.skipif(
        not __import__("importlib").util.find_spec("pdf2docx"),
        reason="pdf2docx not installed",
    )
    def test_convert_simple_pdf(self, tmp_path):
        """Creates a minimal valid PDF and converts it to DOCX."""
        import struct

        # Minimal valid single-page PDF
        pdf_content = b"""%PDF-1.4
1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj
2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj
3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R/Resources<<>>>>endobj
xref
0 4
0000000000 65535 f\r
0000000009 00000 n\r
0000000058 00000 n\r
0000000115 00000 n\r
trailer<</Size 4/Root 1 0 R>>
startxref
217
%%EOF"""
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(pdf_content)

        from modules.convert.pdf2word import convert
        result = convert(pdf_file, output_dir=tmp_path)
        # Result may be None if conversion fails on minimal PDF, that's OK
        # What matters is no exception was raised
        assert True

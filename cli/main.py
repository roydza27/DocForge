#!/usr/bin/env python3
"""
pdf-tool — Workspace PDF Toolkit
=================================

A cross-platform CLI for PDF conversion, editing, optimization, security,
and OCR operations.

Usage examples::

    pdf-tool convert pdf2word report.pdf
    pdf-tool convert word2pdf report.docx
    pdf-tool convert pdf2img report.pdf --dpi 200
    pdf-tool convert img2pdf photo1.png photo2.jpg --output album.pdf
    pdf-tool convert pdf2txt report.pdf

    pdf-tool edit merge a.pdf b.pdf c.pdf
    pdf-tool edit split document.pdf 1-5 6-10
    pdf-tool edit rotate document.pdf 90

    pdf-tool optimize compress report.pdf --preset ebook

    pdf-tool security protect document.pdf "secret"
    pdf-tool security unlock document.pdf "secret"

    pdf-tool ocr scanned.pdf --lang eng

    pdf-tool --check-deps
    pdf-tool --version
"""

import argparse
import sys
import os
from pathlib import Path

# Ensure project root is on PYTHONPATH when running as script
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

__version__ = "0.1.0"


# ── Helpers ───────────────────────────────────────────────────────────────────

def _print_dep_check() -> None:
    """Print status of all external tool dependencies."""
    from utils.deps import summarise_dependencies, check_python_package

    print("\n=== Dependency Check ===\n")
    print("External tools:")
    for tool, path in summarise_dependencies().items():
        status = "✓" if path != "NOT FOUND" else "✗"
        print(f"  {status}  {tool:15s}  {path}")

    print("\nPython packages:")
    pkgs = [
        ("pdf2docx",   "pdf2docx"),
        ("pypdf",      "pypdf"),
        ("pdfminer",   "pdfminer.six"),
        ("pdf2image",  "pdf2image"),
        ("PIL",        "Pillow"),
        ("pytesseract","pytesseract"),
        ("yaml",       "PyYAML"),
    ]
    for import_name, pip_name in pkgs:
        ok = check_python_package(import_name)
        status = "✓" if ok else "✗"
        print(f"  {status}  {import_name:15s}  {'installed' if ok else f'pip install {pip_name}'}")

    print()


# ── Sub-command handlers ──────────────────────────────────────────────────────

def cmd_convert(args: argparse.Namespace) -> int:
    op = args.operation.lower()

    if op == "pdf2word":
        from modules.convert.pdf2word import convert
        result = convert(
            args.input,
            output_file=getattr(args, "output", None),
            output_dir=getattr(args, "output_dir", None),
        )

    elif op == "word2pdf":
        from modules.convert.word2pdf import convert
        result = convert(
            args.input,
            output_file=getattr(args, "output", None),
            output_dir=getattr(args, "output_dir", None),
        )

    elif op == "pdf2img":
        from modules.convert.pdf2img import convert
        result = convert(
            args.input,
            output_dir=getattr(args, "output_dir", None) or getattr(args, "output", None),
            dpi=getattr(args, "dpi", 150),
            fmt=getattr(args, "format", "png"),
        )

    elif op == "img2pdf":
        from modules.convert.img2pdf import convert
        inputs = args.inputs
        result = convert(
            inputs,
            output_file=getattr(args, "output", None),
            output_dir=getattr(args, "output_dir", None),
        )

    elif op == "pdf2txt":
        from modules.convert.pdf2txt import convert
        result = convert(
            args.input,
            output_file=getattr(args, "output", None),
            output_dir=getattr(args, "output_dir", None),
        )

    else:
        print(f"ERROR: Unknown convert operation '{op}'.")
        print("Available: pdf2word, word2pdf, pdf2img, img2pdf, pdf2txt")
        return 1

    return 0 if result else 1


def cmd_edit(args: argparse.Namespace) -> int:
    op = args.operation.lower()

    if op == "merge":
        from modules.edit.merge import merge
        result = merge(
            args.inputs,
            output_file=getattr(args, "output", None),
            output_dir=getattr(args, "output_dir", None),
        )

    elif op == "split":
        from modules.edit.split import split, split_every
        if hasattr(args, "every") and args.every:
            result = split_every(
                args.input,
                every=args.every,
                output_dir=getattr(args, "output_dir", None),
            )
        else:
            result = split(
                args.input,
                ranges=args.ranges,
                output_dir=getattr(args, "output_dir", None),
            )

    elif op == "rotate":
        from modules.edit.rotate import rotate
        result = rotate(
            args.input,
            angle=args.angle,
            pages=getattr(args, "pages", None),
            output_file=getattr(args, "output", None),
            output_dir=getattr(args, "output_dir", None),
        )

    else:
        print(f"ERROR: Unknown edit operation '{op}'.")
        print("Available: merge, split, rotate")
        return 1

    return 0 if result else 1


def cmd_optimize(args: argparse.Namespace) -> int:
    op = args.operation.lower()

    if op == "compress":
        from modules.optimize.compress import compress
        result = compress(
            args.input,
            output_file=getattr(args, "output", None),
            output_dir=getattr(args, "output_dir", None),
            preset=getattr(args, "preset", "ebook"),
        )
    else:
        print(f"ERROR: Unknown optimize operation '{op}'.")
        return 1

    return 0 if result else 1


def cmd_security(args: argparse.Namespace) -> int:
    op = args.operation.lower()

    if op == "protect":
        from modules.security.protect import protect
        result = protect(
            args.input,
            password=args.password,
            output_file=getattr(args, "output", None),
            output_dir=getattr(args, "output_dir", None),
        )

    elif op == "unlock":
        from modules.security.protect import unlock
        result = unlock(
            args.input,
            password=args.password,
            output_file=getattr(args, "output", None),
            output_dir=getattr(args, "output_dir", None),
        )

    else:
        print(f"ERROR: Unknown security operation '{op}'.")
        print("Available: protect, unlock")
        return 1

    return 0 if result else 1


def cmd_ocr(args: argparse.Namespace) -> int:
    from modules.ocr.ocr import ocr
    result = ocr(
        args.input,
        output_file=getattr(args, "output", None),
        output_dir=getattr(args, "output_dir", None),
        lang=getattr(args, "lang", "eng"),
        force=getattr(args, "force", False),
    )
    return 0 if result else 1


# ── Argument parser ───────────────────────────────────────────────────────────

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="pdf-tool",
        description="Workspace PDF Toolkit — cross-platform document processing CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  pdf-tool convert pdf2word report.pdf
  pdf-tool convert pdf2img report.pdf --dpi 200 --format jpeg
  pdf-tool convert img2pdf photo1.png photo2.jpg --output album.pdf
  pdf-tool edit merge a.pdf b.pdf --output combined.pdf
  pdf-tool edit split document.pdf 1-5 6-10
  pdf-tool edit rotate document.pdf 90 --pages 1-3
  pdf-tool optimize compress report.pdf --preset screen
  pdf-tool security protect document.pdf "my_password"
  pdf-tool security unlock document.pdf "my_password"
  pdf-tool ocr scanned.pdf --lang eng
  pdf-tool --check-deps
""",
    )

    parser.add_argument(
        "--version", "-V",
        action="version",
        version=f"pdf-tool {__version__}",
    )
    parser.add_argument(
        "--check-deps",
        action="store_true",
        help="Check availability of all required external tools and Python packages.",
    )

    subparsers = parser.add_subparsers(dest="command", metavar="COMMAND")

    # ── convert ──────────────────────────────────────────────────────────────
    p_convert = subparsers.add_parser(
        "convert",
        help="Convert between document formats.",
        description=(
            "Convert documents.\n\n"
            "Operations: pdf2word, word2pdf, pdf2img, img2pdf, pdf2txt"
        ),
    )
    p_convert.add_argument("operation", help="Conversion type (e.g. pdf2word)")
    # Most convert ops take a single input; img2pdf takes multiple
    p_convert.add_argument(
        "input", nargs="?",
        help="Input file path (not used for img2pdf — use --inputs).",
    )
    p_convert.add_argument(
        "inputs", nargs="*",
        help="Input files (img2pdf only).",
    )
    p_convert.add_argument("--output", "-o", help="Output file path.")
    p_convert.add_argument("--output-dir", dest="output_dir", help="Output directory.")
    p_convert.add_argument("--dpi", type=int, default=150, help="DPI for pdf2img (default: 150).")
    p_convert.add_argument(
        "--format", "-f", default="png",
        choices=["png", "jpeg", "tiff"],
        help="Image format for pdf2img (default: png).",
    )
    p_convert.set_defaults(func=cmd_convert)

    # ── edit ─────────────────────────────────────────────────────────────────
    p_edit = subparsers.add_parser(
        "edit",
        help="Edit PDF files (merge, split, rotate).",
    )
    p_edit.add_argument("operation", help="Edit operation: merge | split | rotate")
    p_edit.add_argument(
        "input", nargs="?",
        help="Single input PDF (split / rotate).",
    )
    p_edit.add_argument(
        "inputs", nargs="*",
        help="Input PDFs (merge) or page ranges (split).",
    )
    p_edit.add_argument("--output", "-o", help="Output file path (merge / rotate).")
    p_edit.add_argument("--output-dir", dest="output_dir", help="Output directory.")
    # split-specific
    p_edit.add_argument("ranges", nargs="*", help="Page ranges for split (e.g. 1-5 6-10).")
    p_edit.add_argument("--every", type=int, help="Split every N pages.")
    # rotate-specific
    p_edit.add_argument("angle", nargs="?", type=int, help="Rotation angle: 90 | 180 | 270.")
    p_edit.add_argument("--pages", help="Page range to rotate (e.g. '1-3,5'). Default: all.")
    p_edit.set_defaults(func=cmd_edit)

    # ── optimize ─────────────────────────────────────────────────────────────
    p_opt = subparsers.add_parser(
        "optimize",
        help="Optimize PDFs (compression).",
    )
    p_opt.add_argument("operation", help="Optimize operation: compress")
    p_opt.add_argument("input", help="Input PDF path.")
    p_opt.add_argument("--output", "-o", help="Output file path.")
    p_opt.add_argument("--output-dir", dest="output_dir", help="Output directory.")
    p_opt.add_argument(
        "--preset", "-p",
        default="ebook",
        choices=["screen", "ebook", "printer", "prepress", "default"],
        help="Ghostscript compression preset (default: ebook).",
    )
    p_opt.set_defaults(func=cmd_optimize)

    # ── security ─────────────────────────────────────────────────────────────
    p_sec = subparsers.add_parser(
        "security",
        help="Encrypt/decrypt PDFs.",
    )
    p_sec.add_argument("operation", help="Security operation: protect | unlock")
    p_sec.add_argument("input", help="Input PDF path.")
    p_sec.add_argument("password", help="Password to apply or remove.")
    p_sec.add_argument("--output", "-o", help="Output file path.")
    p_sec.add_argument("--output-dir", dest="output_dir", help="Output directory.")
    p_sec.set_defaults(func=cmd_security)

    # ── ocr ──────────────────────────────────────────────────────────────────
    p_ocr = subparsers.add_parser(
        "ocr",
        help="Run OCR on scanned PDFs.",
    )
    p_ocr.add_argument("input", help="Scanned PDF path.")
    p_ocr.add_argument("--output", "-o", help="Output searchable PDF path.")
    p_ocr.add_argument("--output-dir", dest="output_dir", help="Output directory.")
    p_ocr.add_argument("--lang", default="eng", help="Tesseract language code (default: eng).")
    p_ocr.add_argument(
        "--force", action="store_true",
        help="Force OCR even if PDF already contains text.",
    )
    p_ocr.set_defaults(func=cmd_ocr)

    return parser


# ── Entry point ───────────────────────────────────────────────────────────────

def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.check_deps:
        _print_dep_check()
        return 0

    if not args.command:
        parser.print_help()
        return 0

    # Handle img2pdf: merge positional args
    if args.command == "convert" and args.operation == "img2pdf":
        # Collect all positional args as inputs
        all_inputs = []
        if args.input:
            all_inputs.append(args.input)
        if args.inputs:
            all_inputs.extend(args.inputs)
        args.inputs = all_inputs

    # Handle merge: all positionals go to inputs
    if args.command == "edit" and args.operation == "merge":
        all_inputs = []
        if args.input:
            all_inputs.append(args.input)
        if args.inputs:
            all_inputs.extend(args.inputs)
        args.inputs = all_inputs

    # Handle split: ranges come from positionals after input
    if args.command == "edit" and args.operation == "split":
        if not hasattr(args, "ranges") or not args.ranges:
            args.ranges = args.inputs or []

    # Handle rotate: angle comes as positional
    if args.command == "edit" and args.operation == "rotate":
        # angle is the first element of inputs if not set
        if not args.angle and args.inputs:
            try:
                args.angle = int(args.inputs[0])
            except (ValueError, IndexError):
                pass

    try:
        return args.func(args)
    except AttributeError:
        parser.print_help()
        return 0
    except KeyboardInterrupt:
        print("\nInterrupted.")
        return 130


if __name__ == "__main__":
    sys.exit(main())

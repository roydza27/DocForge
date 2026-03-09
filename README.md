# workspace-tools · pdf-tool

> A cross-platform CLI toolkit for PDF conversion, editing, optimization, security, and OCR — your self-hosted alternative to iLovePDF.

---

## Features

| Category     | Operations                                               |
|--------------|----------------------------------------------------------|
| **Convert**  | PDF→Word, Word→PDF, PDF→Images, Images→PDF, PDF→Text    |
| **Edit**     | Merge, Split, Rotate pages                               |
| **Optimize** | Compress (Ghostscript presets)                           |
| **Security** | Password-protect, Unlock encrypted PDFs                  |
| **OCR**      | Scanned PDF → searchable PDF (Tesseract)                 |

---

## Installation

### Prerequisites

Install Python 3.10+ and the following external tools (add to PATH):

| Tool         | Purpose            | Download                                     |
|--------------|--------------------|----------------------------------------------|
| Ghostscript  | Compression, images | <https://www.ghostscript.com/download.html>  |
| Tesseract    | OCR                | <https://github.com/tesseract-ocr/tessdoc>   |
| LibreOffice  | Word↔PDF           | <https://www.libreoffice.org/download/>      |
| Poppler      | PDF→Images (alt)   | <https://poppler.freedesktop.org/>           |

### Python package

```bash
# Clone the repository
git clone https://github.com/yourorg/workspace-tools.git
cd workspace-tools

# Install (editable mode recommended during development)
pip install -e .

# Or install with all optional extras
pip install -e ".[full]"
```

The `pdf-tool` command will now be available globally.

### Check dependencies

```bash
pdf-tool --check-deps
```

---

## Usage

### Convert

```bash
# PDF → Word
pdf-tool convert pdf2word report.pdf
pdf-tool convert pdf2word report.pdf --output report.docx

# Word → PDF
pdf-tool convert word2pdf report.docx
pdf-tool convert word2pdf report.docx --output report.pdf

# PDF → Images
pdf-tool convert pdf2img report.pdf
pdf-tool convert pdf2img report.pdf --dpi 200 --format jpeg

# Images → PDF
pdf-tool convert img2pdf photo1.png photo2.jpg
pdf-tool convert img2pdf *.png --output album.pdf

# PDF → Text
pdf-tool convert pdf2txt report.pdf
```

### Edit

```bash
# Merge PDFs
pdf-tool edit merge a.pdf b.pdf c.pdf
pdf-tool edit merge a.pdf b.pdf --output combined.pdf

# Split PDF
pdf-tool edit split document.pdf 1-5         # pages 1 to 5
pdf-tool edit split document.pdf 1-3 4-6     # two output files
pdf-tool edit split document.pdf --every 10  # every 10 pages

# Rotate pages
pdf-tool edit rotate document.pdf 90         # rotate all pages 90°
pdf-tool edit rotate document.pdf 180 --pages 1-3  # rotate pages 1-3
```

### Optimize

```bash
pdf-tool optimize compress report.pdf
pdf-tool optimize compress report.pdf --preset screen   # smallest size
pdf-tool optimize compress report.pdf --preset printer  # print quality
```

**Presets:** `screen` (72 dpi) → `ebook` (150 dpi) → `printer` (300 dpi) → `prepress`

### Security

```bash
# Password-protect a PDF
pdf-tool security protect document.pdf "my_secret_password"

# Remove password
pdf-tool security unlock document.pdf "my_secret_password"
```

### OCR

```bash
pdf-tool ocr scanned_report.pdf
pdf-tool ocr scanned_report.pdf --lang deu   # German
pdf-tool ocr scanned_report.pdf --output searchable.pdf
pdf-tool ocr report.pdf --force              # run OCR even on text PDFs
```

---

## Python API

Every feature is also callable as a Python function:

```python
from modules.convert.pdf2word import convert
from modules.edit.merge import merge
from modules.optimize.compress import compress

# Convert PDF to Word
output = convert("report.pdf")

# Merge PDFs
output = merge(["a.pdf", "b.pdf"], output_file="combined.pdf")

# Compress with screen preset
output = compress("report.pdf", preset="screen")
```

---

## Project Structure

```
workspace-tools/
├── cli/
│   └── main.py            ← pdf-tool entry point & argument parser
├── core/
│   ├── config.py          ← configuration loader
│   ├── file_manager.py    ← validation, temp workspace, output naming
│   ├── logger.py          ← rotating logger (console + file)
│   └── task_manager.py    ← job execution engine
├── modules/
│   ├── convert/           ← pdf2word, word2pdf, pdf2img, img2pdf, pdf2txt
│   ├── edit/              ← merge, split, rotate
│   ├── optimize/          ← compress
│   ├── security/          ← protect, unlock
│   └── ocr/               ← ocr
├── engines/
│   ├── ghostscript.py     ← Ghostscript wrapper
│   ├── libreoffice.py     ← LibreOffice wrapper
│   └── tesseract.py       ← Tesseract wrapper
├── utils/
│   └── deps.py            ← dependency detection
├── tests/                 ← unit tests
├── pyproject.toml
├── LICENSE
└── README.md
```

---

## Configuration

Config file is auto-created at `~/.workspace-tools/config.yaml`:

```yaml
temp_dir: /tmp/workspace-tools
output_dir: .
log_level: INFO
engine_paths:
  ghostscript: gs
  tesseract: tesseract
  libreoffice: libreoffice
compression:
  default_preset: ebook
ocr:
  language: eng
```

Logs are written to `~/.workspace-tools/logs/pdf-tool.log`.

---

## Cross-Platform Notes

- Uses `pathlib` for all path operations (Windows / Unix compatible)
- Uses `tempfile` for temporary files (auto-resolves to correct OS temp dir)
- Ghostscript binary auto-detected: `gs` (Linux/macOS) or `gswin64c` (Windows)
- LibreOffice binary: `libreoffice` or `soffice` depending on platform

---

## License

MIT — see [LICENSE](LICENSE)

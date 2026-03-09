"""
Configuration loader for workspace-tools.
Reads from ~/.workspace-tools/config.yaml (auto-created with defaults).
"""

import os
import tempfile
from pathlib import Path
from typing import Any

try:
    import yaml  # PyYAML optional; fall back to defaults if missing
    _YAML_AVAILABLE = True
except ImportError:
    _YAML_AVAILABLE = False

# ── Config directory & file ──────────────────────────────────────────────────
CONFIG_DIR = Path.home() / ".workspace-tools"
CONFIG_FILE = CONFIG_DIR / "config.yaml"

# ── Sensible cross-platform defaults ─────────────────────────────────────────
DEFAULTS: dict[str, Any] = {
    "temp_dir": str(Path(tempfile.gettempdir()) / "workspace-tools"),
    "output_dir": str(Path.cwd()),
    "log_level": "INFO",
    "engine_paths": {
        "ghostscript": "gs",           # "gswin64c" on Windows handled at runtime
        "tesseract": "tesseract",
        "libreoffice": "libreoffice",  # "soffice" on some systems
        "pdftoppm": "pdftoppm",
    },
    "compression": {
        "default_preset": "screen",    # gs presets: screen, ebook, printer, prepress
    },
    "ocr": {
        "language": "eng",
    },
}


def _ensure_config_exists() -> None:
    """Create default config file if it does not exist."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    if not CONFIG_FILE.exists() and _YAML_AVAILABLE:
        with open(CONFIG_FILE, "w", encoding="utf-8") as fh:
            yaml.dump(DEFAULTS, fh, default_flow_style=False)


def load_config() -> dict[str, Any]:
    """
    Load configuration from YAML file, merging with defaults.

    Returns:
        Merged configuration dictionary.
    """
    _ensure_config_exists()

    config = dict(DEFAULTS)  # start from defaults

    if _YAML_AVAILABLE and CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as fh:
                user_cfg = yaml.safe_load(fh) or {}
            # Shallow-merge top-level keys
            for key, value in user_cfg.items():
                if isinstance(value, dict) and isinstance(config.get(key), dict):
                    config[key] = {**config[key], **value}
                else:
                    config[key] = value
        except Exception:
            pass  # silently fall back to defaults

    # Normalise paths
    config["temp_dir"] = Path(config["temp_dir"])
    config["output_dir"] = Path(config["output_dir"])
    config["temp_dir"].mkdir(parents=True, exist_ok=True)

    # Windows Ghostscript override
    if os.name == "nt":
        config["engine_paths"].setdefault("ghostscript", "gswin64c")

    return config


# Module-level singleton
CONFIG = load_config()

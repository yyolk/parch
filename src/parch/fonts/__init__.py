"""Vendored Barlow (sans) and Liberation Serif (OFL-1.1)."""

from pathlib import Path


def font_dir() -> Path:
    return Path(__file__).resolve().parent

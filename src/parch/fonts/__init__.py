"""Vendored Jost (OFL-1.1) — Book, Medium, Bold, Heavy — plus the type ramp."""

from pathlib import Path

from parch.fonts.ramp import JostRamp, TypeInk, TypeRamp, TypeRole

__all__ = ["JostRamp", "TypeInk", "TypeRamp", "TypeRole", "font_dir"]


def font_dir() -> Path:
    return Path(__file__).resolve().parent

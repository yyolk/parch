"""Vendored Jost (OFL-1.1) — Book, Medium, Bold, Heavy — plus the type ramp."""

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from parch.fonts.ramp import JostRamp, TypeInk, TypeRamp, TypeRole

__all__ = ["JostRamp", "TypeInk", "TypeRamp", "TypeRole", "font_dir"]


def font_dir() -> Path:
    return Path(__file__).resolve().parent


def __getattr__(name: str):
    if name in {"JostRamp", "TypeInk", "TypeRamp", "TypeRole"}:
        from parch.fonts.ramp import JostRamp, TypeInk, TypeRamp, TypeRole

        return {
            "JostRamp": JostRamp,
            "TypeInk": TypeInk,
            "TypeRamp": TypeRamp,
            "TypeRole": TypeRole,
        }[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

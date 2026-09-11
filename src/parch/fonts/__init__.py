"""Vendored Jost + Besley + Martian Grotesk (OFL-1.1) and the type ramp."""

from parch.fonts.catalog import (
    FontCatalog,
    TypeFamily,
    TypeWeight,
    font_dir,
    jost_besley_catalog,
    jost_catalog,
    martian_besley_catalog,
)
from parch.fonts.ramp import JostBesleyRamp, JostRamp, MartianBesleyRamp, TypeInk, TypeRamp, TypeRole

__all__ = [
    "FontCatalog",
    "JostBesleyRamp",
    "JostRamp",
    "MartianBesleyRamp",
    "TypeFamily",
    "TypeInk",
    "TypeRamp",
    "TypeRole",
    "TypeWeight",
    "font_dir",
    "jost_besley_catalog",
    "jost_catalog",
    "martian_besley_catalog",
]

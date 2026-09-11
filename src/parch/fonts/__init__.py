"""Vendored Jost (OFL-1.1) and the type ramp."""

from parch.fonts.catalog import FontCatalog, TypeFamily, TypeWeight, font_dir, jost_catalog
from parch.fonts.ramp import (
    ROLE_WEIGHTS,
    SIZE_BANDS,
    JostRamp,
    TypeInk,
    TypeRamp,
    TypeRole,
    band_weight,
    cut_for,
)

__all__ = [
    "FontCatalog",
    "JostRamp",
    "ROLE_WEIGHTS",
    "SIZE_BANDS",
    "TypeFamily",
    "TypeInk",
    "TypeRamp",
    "TypeRole",
    "TypeWeight",
    "band_weight",
    "cut_for",
    "font_dir",
    "jost_catalog",
]

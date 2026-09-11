"""Vendored Jost (OFL-1.1) and the chrome / body type ramps."""

from parch.fonts.catalog import FontCatalog, TypeFamily, TypeWeight, font_dir, jost_catalog
from parch.fonts.ramp import (
    BodyRamp,
    BodyRole,
    ChromeRamp,
    ChromeRole,
    JostBodyRamp,
    JostChromeRamp,
    TypeInk,
    jost_ramps,
)

__all__ = [
    "BodyRamp",
    "BodyRole",
    "ChromeRamp",
    "ChromeRole",
    "FontCatalog",
    "JostBodyRamp",
    "JostChromeRamp",
    "TypeFamily",
    "TypeInk",
    "TypeWeight",
    "font_dir",
    "jost_catalog",
    "jost_ramps",
]

"""Vendored Jost (OFL-1.1) and the type ramp."""

from parch.fonts.catalog import FontCatalog, TypeFamily, TypeWeight, font_dir, jost_catalog
from parch.fonts.ramp import (
    HOUSE_TYPE_OVERLAY,
    PRESS_TITLE_SIZE,
    PRESS_TITLE_WEIGHT,
    PRESS_TYPE_OVERLAY,
    EffectiveRamp,
    JostRamp,
    OverlayStack,
    TypeInk,
    TypeOverlay,
    TypePatch,
    TypeRamp,
    TypeRole,
    apply_overlay,
    bind_ramp,
    merge_overlays,
)

__all__ = [
    "HOUSE_TYPE_OVERLAY",
    "PRESS_TITLE_SIZE",
    "PRESS_TITLE_WEIGHT",
    "PRESS_TYPE_OVERLAY",
    "EffectiveRamp",
    "FontCatalog",
    "JostRamp",
    "OverlayStack",
    "TypeFamily",
    "TypeInk",
    "TypeOverlay",
    "TypePatch",
    "TypeRamp",
    "TypeRole",
    "TypeWeight",
    "apply_overlay",
    "bind_ramp",
    "font_dir",
    "jost_catalog",
    "merge_overlays",
]

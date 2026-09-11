"""Vendored Jost (OFL-1.1) and the type ramp."""

from parch.fonts.catalog import FontCatalog, TypeFamily, TypeWeight, font_dir, jost_catalog
from parch.fonts.ramp import (
    BoundRamp,
    JostRamp,
    ROOT_CONTEXT,
    TypeContext,
    TypeInk,
    TypePatch,
    TypeRamp,
    TypeRole,
    merge_role_over_context,
)

__all__ = [
    "BoundRamp",
    "FontCatalog",
    "JostRamp",
    "ROOT_CONTEXT",
    "TypeContext",
    "TypeFamily",
    "TypeInk",
    "TypePatch",
    "TypeRamp",
    "TypeRole",
    "TypeWeight",
    "font_dir",
    "jost_catalog",
    "merge_role_over_context",
]

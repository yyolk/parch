"""Vendored Jost (OFL-1.1) and the type ramp."""

from parch.fonts.catalog import FontCatalog, TypeFamily, TypeWeight, font_dir, jost_catalog
from parch.fonts.ramp import (
    PROOF_CHROME_SIZE,
    PROOF_COVER_BROW_SIZE,
    PROOF_PAGE_TITLE_SIZE,
    PROOF_PROFILE,
    EffectiveRamp,
    JostRamp,
    ProofProfile,
    TypeInk,
    TypeOverlay,
    TypePatch,
    TypeRamp,
    TypeRole,
    apply_overlay,
    bind_ramp,
    compose_overlays,
)

__all__ = [
    "PROOF_CHROME_SIZE",
    "PROOF_COVER_BROW_SIZE",
    "PROOF_PAGE_TITLE_SIZE",
    "PROOF_PROFILE",
    "EffectiveRamp",
    "FontCatalog",
    "JostRamp",
    "ProofProfile",
    "TypeFamily",
    "TypeInk",
    "TypeOverlay",
    "TypePatch",
    "TypeRamp",
    "TypeRole",
    "TypeWeight",
    "apply_overlay",
    "bind_ramp",
    "compose_overlays",
    "font_dir",
    "jost_catalog",
]

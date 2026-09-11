"""Role-based type: painters ask for roles; a ramp resolves plotter ink.

Explicit object — no ambient container, no signature injection, no globals.
``TypeInk`` carries family + weight + size. Painters call ``ramp.ink(role)``
and pass those fields through; they do not think in sans/serif slots.

``family`` stays on the ink so a later dual-font ramp can pick another
catalog family without ripping out the plotter kwarg. Today every role
resolves to ``family="jost"``. Overlay never changes family.

Closed default set is today's ``TypeRole`` (four keys). Device overlay
(thesis M) is the target-device layer. This spike adds a separate
``ProofProfile`` layer for on-screen proofs / specimens:

    EffectiveRamp = defaults ⊕ device ⊕ proof
"""

from dataclasses import dataclass, field
from typing import Literal, Protocol

from parch.fonts.catalog import FontCatalog, TypeFamily, TypeWeight, jost_catalog

type TypeRole = Literal["cover_year", "cover_brow", "page_title", "chrome"]

_WEIGHTS: frozenset[str] = frozenset(("book", "medium", "bold", "heavy"))
_ROLES: frozenset[str] = frozenset(("cover_year", "cover_brow", "page_title", "chrome"))


@dataclass(frozen=True, slots=True)
class TypeInk:
    """Resolved family / weight / size for ``Plotter.text``."""

    family: TypeFamily
    weight: TypeWeight
    size: float


class TypeRamp(Protocol):
    catalog: FontCatalog

    def ink(self, role: TypeRole) -> TypeInk:
        """Resolve a closed type role to plotter-ready ink."""
        ...


_JOST: dict[TypeRole, TypeInk] = {
    "cover_year": TypeInk(family="jost", weight="heavy", size=42),
    "cover_brow": TypeInk(family="jost", weight="medium", size=10),
    "page_title": TypeInk(family="jost", weight="medium", size=11),
    "chrome": TypeInk(family="jost", weight="book", size=7.4),
}


@dataclass(frozen=True, slots=True)
class TypePatch:
    """Partial ink override. Missing fields keep the previous ink. No I/O."""

    size: float | None = None
    weight: TypeWeight | None = None

    def __post_init__(self) -> None:
        if self.size is not None and self.size <= 0:
            raise ValueError(f"size must be > 0, not {self.size}")
        if self.weight is not None and self.weight not in _WEIGHTS:
            raise ValueError(f"unknown weight {self.weight!r}")


@dataclass(frozen=True, slots=True)
class TypeOverlay:
    """Frozen partial overrides keyed by ``TypeRole``. Pure data — no I/O.

    Each role is optional. A present ``TypePatch`` may set size, weight, or
    both; ``None`` on a patch field keeps the previous ink for that field.
    """

    cover_year: TypePatch | None = None
    cover_brow: TypePatch | None = None
    page_title: TypePatch | None = None
    chrome: TypePatch | None = None

    def patch(self, role: TypeRole) -> TypePatch | None:
        match role:
            case "cover_year":
                return self.cover_year
            case "cover_brow":
                return self.cover_brow
            case "page_title":
                return self.page_title
            case "chrome":
                return self.chrome


def apply_overlay(base: TypeInk, patch: TypePatch | None) -> TypeInk:
    """Explicit patch field wins; missing field keeps ``base``. Family stays."""
    if patch is None:
        return base
    return TypeInk(
        family=base.family,
        weight=base.weight if patch.weight is None else patch.weight,
        size=base.size if patch.size is None else patch.size,
    )


def _compose_patch(base: TypePatch | None, over: TypePatch | None) -> TypePatch | None:
    if over is None:
        return base
    if base is None:
        return over
    return TypePatch(
        size=over.size if over.size is not None else base.size,
        weight=over.weight if over.weight is not None else base.weight,
    )


def compose_overlays(*overlays: TypeOverlay | None) -> TypeOverlay:
    """Later overlay's explicit fields win per role, then per size/weight."""
    acc = TypeOverlay()
    for overlay in overlays:
        if overlay is None:
            continue
        acc = TypeOverlay(
            cover_year=_compose_patch(acc.cover_year, overlay.cover_year),
            cover_brow=_compose_patch(acc.cover_brow, overlay.cover_brow),
            page_title=_compose_patch(acc.page_title, overlay.page_title),
            chrome=_compose_patch(acc.chrome, overlay.chrome),
        )
    return acc


@dataclass(frozen=True, slots=True)
class JostRamp:
    """Single-family Jost role map. Default — and currently only — closed table."""

    catalog: FontCatalog = field(default_factory=jost_catalog)

    def ink(self, role: TypeRole) -> TypeInk:
        ink = _JOST[role]
        self.catalog.path(ink.family, ink.weight)
        return ink


@dataclass(frozen=True, slots=True)
class EffectiveRamp:
    """Closed Jost defaults ⊕ overlay. Painters call ``ink``; they never read the overlay."""

    overlay: TypeOverlay = field(default_factory=TypeOverlay)
    catalog: FontCatalog = field(default_factory=jost_catalog)

    def ink(self, role: TypeRole) -> TypeInk:
        if role not in _ROLES:
            raise KeyError(f"unknown type role {role!r}")
        ink = apply_overlay(_JOST[role], self.overlay.patch(role))
        self.catalog.path(ink.family, ink.weight)
        return ink


def bind_ramp(*, ramp: TypeRamp | None = None, overlay: TypeOverlay | None = None) -> TypeRamp:
    """Explicit ``ramp`` wins. Otherwise ``EffectiveRamp(defaults ⊕ overlay)``."""
    if ramp is not None:
        return ramp
    return EffectiveRamp(overlay=TypeOverlay() if overlay is None else overlay)


# Slightly larger chrome / title than the closed defaults — on-screen review.
# Device overlay (thesis M) is a separate layer and is not mutated here.
PROOF_CHROME_SIZE = 9.2
PROOF_PAGE_TITLE_SIZE = 13.0
PROOF_COVER_BROW_SIZE = 12.0


@dataclass(frozen=True, slots=True)
class ProofProfile:
    """Press-mode overlay for proofs / specimens (on-screen review).

    Selected by ``press(..., proof=True)`` or ``parch proof``. Composition is
    ``defaults ⊕ device ⊕ proof``. Does not change Nomad's device overlay.
    """

    overlay: TypeOverlay = field(
        default_factory=lambda: TypeOverlay(
            chrome=TypePatch(size=PROOF_CHROME_SIZE),
            page_title=TypePatch(size=PROOF_PAGE_TITLE_SIZE),
            cover_brow=TypePatch(size=PROOF_COVER_BROW_SIZE),
        )
    )


PROOF_PROFILE = ProofProfile()

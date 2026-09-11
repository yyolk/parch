"""Role-based type: painters ask for roles; a ramp resolves plotter ink.

Explicit object — no ambient container, no signature injection, no globals.
``TypeInk`` carries family + weight + size. Painters call ``ramp.ink(role)``
and pass those fields through; they do not think in sans/serif slots.

Thesis M overlaid size/weight only. Thesis U lets ``TypePatch`` set optional
``family`` too. Today the catalog is still Jost-only; ``family="jost"`` is
the only cut that resolves. A later dual-font catalog registers more
``(family, weight)`` pairs — painters already pass ``family=`` and do not
change.

``EffectiveRamp.ink`` resolves through ``catalog.path(family, weight)``.
Unknown family (or weight) raises ``KeyError`` there — the catalog is the
closed set, not ``TypePatch`` validation.
"""

from dataclasses import dataclass, field
from typing import Literal, Protocol, cast

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
    """Partial ink override. Missing fields keep the default. No I/O.

    ``family`` is an optional catalog key. Today only ``"jost"`` is
    registered. The overlay accepts the field so a future dual-font
    catalog can plug in without a ``TypePatch`` signature change.
    Unknown family is not rejected here — ``catalog.path`` is the check.
    """

    size: float | None = None
    weight: TypeWeight | None = None
    family: str | None = None

    def __post_init__(self) -> None:
        if self.size is not None and self.size <= 0:
            raise ValueError(f"size must be > 0, not {self.size}")
        if self.weight is not None and self.weight not in _WEIGHTS:
            raise ValueError(f"unknown weight {self.weight!r}")


@dataclass(frozen=True, slots=True)
class TypeOverlay:
    """Frozen partial overrides keyed by ``TypeRole``. Pure data — no I/O.

    Each role is optional. A present ``TypePatch`` may set size, weight,
    and/or family; ``None`` on a patch field keeps the previous value.
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
    """Explicit patch field wins; missing field keeps ``base``.

    Family overlay wins when present; missing family keeps the default.
    """
    if patch is None:
        return base
    family = base.family if patch.family is None else cast(TypeFamily, patch.family)
    return TypeInk(
        family=family,
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
        family=over.family if over.family is not None else base.family,
    )


def compose_overlays(*overlays: TypeOverlay | None) -> TypeOverlay:
    """Later overlay's explicit fields win per role, then per size/weight/family."""
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
    """Closed Jost defaults ⊕ overlay. Painters call ``ink``; they never read the overlay.

    ``ink`` always resolves through ``catalog.path(family, weight)`` so an
    unknown overlay family fails at the catalog — the same check a future
    dual-font map will use.
    """

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


# Explicit Jost family on every role — proves the overlay API without
# changing the look. Size/weight stay unset (thesis M owns those knobs).
JOST_FAMILY_OVERLAY = TypeOverlay(
    cover_year=TypePatch(family="jost"),
    cover_brow=TypePatch(family="jost"),
    page_title=TypePatch(family="jost"),
    chrome=TypePatch(family="jost"),
)

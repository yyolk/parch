"""Role-based type: painters ask for roles; a ramp resolves plotter ink.

Explicit object — no ambient container, no signature injection, no globals.
``TypeInk`` carries family + weight + size. Painters call ``ramp.ink(role)``
and pass those fields through; they do not think in sans/serif slots.

``family`` stays on the ink so a later dual-font ramp can pick another
catalog family without ripping out the plotter kwarg. Today every role
resolves to ``family="jost"``. Overlay never changes family.

Closed default set is today's ``TypeRole`` (four keys). Device and/or the
press TOML may overlay size/weight as data. Merge order is
``code defaults ⊕ device ⊕ toml`` (later explicit fields win).
"""

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Literal, Protocol

from parch.fonts.catalog import FontCatalog, TypeFamily, TypeWeight, jost_catalog

type TypeRole = Literal["cover_year", "cover_brow", "page_title", "chrome"]

TYPE_ROLES: frozenset[str] = frozenset(("cover_year", "cover_brow", "page_title", "chrome"))
TYPE_WEIGHTS: frozenset[str] = frozenset(("book", "medium", "bold", "heavy"))
TYPE_PATCH_KEYS: frozenset[str] = frozenset(("size", "weight"))


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
        if self.weight is not None and self.weight not in TYPE_WEIGHTS:
            raise ValueError(
                f"unknown Jost weight {self.weight!r}; use book, medium, bold, or heavy"
            )


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

    @classmethod
    def from_mapping(cls, table: Mapping[str, object]) -> TypeOverlay:
        """Parse a role→patch table. Unknown roles, fields, or weights fail."""
        unknown = set(table) - TYPE_ROLES
        if unknown:
            key = sorted(unknown)[0]
            raise ValueError(f"unknown typography overlay role {key!r}")
        patches: dict[str, TypePatch] = {}
        for role in TYPE_ROLES:
            if role not in table:
                continue
            raw = table[role]
            if not isinstance(raw, Mapping):
                raise ValueError(f"typography overlay {role} must be a table")
            patches[role] = _patch_from_mapping(role, raw)
        return cls(
            cover_year=patches.get("cover_year"),
            cover_brow=patches.get("cover_brow"),
            page_title=patches.get("page_title"),
            chrome=patches.get("chrome"),
        )


def _patch_from_mapping(role: str, table: Mapping[str, object]) -> TypePatch:
    unknown = set(table) - TYPE_PATCH_KEYS
    if unknown:
        key = sorted(unknown)[0]
        raise ValueError(f"unknown typography overlay {role} key {key!r}")
    size: float | None = None
    if "size" in table:
        raw_size = table["size"]
        if isinstance(raw_size, bool) or not isinstance(raw_size, (int, float)):
            raise ValueError(f"typography overlay {role}.size must be a number")
        size = float(raw_size)
    weight: TypeWeight | None = None
    if "weight" in table:
        raw_weight = table["weight"]
        if not isinstance(raw_weight, str):
            raise ValueError(f"typography overlay {role}.weight must be a string")
        if raw_weight not in TYPE_WEIGHTS:
            raise ValueError(
                f"unknown Jost weight {raw_weight!r}; use book, medium, bold, or heavy"
            )
        weight = raw_weight
    return TypePatch(size=size, weight=weight)


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
        if role not in TYPE_ROLES:
            raise KeyError(f"unknown type role {role!r}")
        ink = apply_overlay(_JOST[role], self.overlay.patch(role))
        self.catalog.path(ink.family, ink.weight)
        return ink


def bind_ramp(*, ramp: TypeRamp | None = None, overlay: TypeOverlay | None = None) -> TypeRamp:
    """Explicit ``ramp`` wins. Otherwise ``EffectiveRamp(defaults ⊕ overlay)``."""
    if ramp is not None:
        return ramp
    return EffectiveRamp(overlay=TypeOverlay() if overlay is None else overlay)

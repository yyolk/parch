"""Role-based type: painters ask for roles; a ramp resolves plotter ink.

Explicit object — no ambient container, no signature injection, no globals.
``TypeInk`` carries family + weight + size. Painters call ``ramp.ink(role)``
and pass those fields through; they do not think in sans/serif slots.

Unmigrated painters still pass ``face`` + ``bold``. That path is not a
plotter secret: ``FaceBridge`` (owned by the ramp) maps
``(face, bold, size)`` → ``TypeInk``. ``Fpdf2Plotter`` asks
``ramp.resolve_face(...)`` when ``family`` is omitted. Cover / header stay
on roles. Dual path is intentional until those painters adopt roles.

``family`` stays on the ink so a later dual-font ramp can pick another
catalog family without ripping out the plotter kwarg. Today every role
and every face bridge resolves to ``family="jost"``. Overlay never
changes family.

``EffectiveRamp`` is closed Jost defaults ⊕ a frozen ``TypeOverlay``
(optional size/weight per today's four roles). Press / device wiring
builds one ramp and passes it in.
"""

from dataclasses import dataclass, field
from typing import Literal, Protocol

from parch.fonts.catalog import FontCatalog, TypeFamily, TypeWeight, jost_catalog

type TypeRole = Literal["cover_year", "cover_brow", "page_title", "chrome"]
type TypeFace = Literal["sans", "serif"]

_WEIGHTS: frozenset[str] = frozenset(("book", "medium", "bold", "heavy"))


@dataclass(frozen=True, slots=True)
class TypeInk:
    """Resolved family / weight / size for ``Plotter.text``."""

    family: TypeFamily
    weight: TypeWeight
    size: float


# Unmigrated face+bold → curated Jost cut. Weight override is not in the
# table — ``FaceBridge.resolve`` applies it before lookup. Size is carried
# onto the ink; it is not a weight axis today.
_FACE: dict[tuple[TypeFace, bool], TypeWeight] = {
    ("serif", False): "medium",
    ("serif", True): "medium",
    ("sans", False): "book",
    ("sans", True): "bold",
}


@dataclass(frozen=True, slots=True)
class FaceBridge:
    """Explicit ``(face, bold, size)`` → ``TypeInk``. Same catalog as the ramp.

    Pure table + catalog lookup. No I/O, no ambient container. Serif maps
    to Medium (the old Liberation Serif stand-in); sans regular is Book;
    sans bold is Bold. An explicit ``weight`` wins over face+bold.
    """

    catalog: FontCatalog = field(default_factory=jost_catalog)

    def resolve(
        self,
        face: TypeFace,
        bold: bool,
        size: float,
        *,
        weight: TypeWeight | None = None,
    ) -> TypeInk:
        cut = weight if weight is not None else _FACE[(face, bold)]
        ink = TypeInk(family="jost", weight=cut, size=size)
        self.catalog.path(ink.family, ink.weight)
        return ink


class TypeRamp(Protocol):
    catalog: FontCatalog

    def ink(self, role: TypeRole) -> TypeInk:
        """Resolve a closed type role to plotter-ready ink."""
        ...

    def resolve_face(
        self,
        face: TypeFace,
        bold: bool,
        size: float,
        *,
        weight: TypeWeight | None = None,
    ) -> TypeInk:
        """Resolve an unmigrated face+bold path to plotter-ready ink."""
        ...


_JOST: dict[TypeRole, TypeInk] = {
    "cover_year": TypeInk(family="jost", weight="heavy", size=42),
    "cover_brow": TypeInk(family="jost", weight="medium", size=10),
    "page_title": TypeInk(family="jost", weight="medium", size=11),
    "chrome": TypeInk(family="jost", weight="book", size=7.4),
}


@dataclass(frozen=True, slots=True)
class TypePatch:
    """Partial ink override. Missing fields keep the default. No I/O."""

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
    both; ``None`` on a patch field keeps the closed default for that field.
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


def _resolve_role(catalog: FontCatalog, role: TypeRole, overlay: TypeOverlay) -> TypeInk:
    ink = apply_overlay(_JOST[role], overlay.patch(role))
    catalog.path(ink.family, ink.weight)
    return ink


@dataclass(frozen=True, slots=True)
class JostRamp:
    """Single-family Jost role map + face bridge. Closed default table."""

    catalog: FontCatalog = field(default_factory=jost_catalog)

    def ink(self, role: TypeRole) -> TypeInk:
        return _resolve_role(self.catalog, role, TypeOverlay())

    def resolve_face(
        self,
        face: TypeFace,
        bold: bool,
        size: float,
        *,
        weight: TypeWeight | None = None,
    ) -> TypeInk:
        return FaceBridge(self.catalog).resolve(face, bold, size, weight=weight)


@dataclass(frozen=True, slots=True)
class EffectiveRamp:
    """Closed Jost defaults ⊕ overlay. Painters call ``ink``; they never read the overlay."""

    overlay: TypeOverlay = field(default_factory=TypeOverlay)
    catalog: FontCatalog = field(default_factory=jost_catalog)

    def ink(self, role: TypeRole) -> TypeInk:
        return _resolve_role(self.catalog, role, self.overlay)

    def resolve_face(
        self,
        face: TypeFace,
        bold: bool,
        size: float,
        *,
        weight: TypeWeight | None = None,
    ) -> TypeInk:
        return FaceBridge(self.catalog).resolve(face, bold, size, weight=weight)


def bind_ramp(*, ramp: TypeRamp | None = None, overlay: TypeOverlay | None = None) -> TypeRamp:
    """Explicit ``ramp`` wins. Otherwise ``EffectiveRamp(defaults ⊕ overlay)``."""
    if ramp is not None:
        return ramp
    return EffectiveRamp(overlay=TypeOverlay() if overlay is None else overlay)

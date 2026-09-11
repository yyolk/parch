"""Typographic scale: painters pick a step, not a page name.

Explicit object — no ambient container, no signature injection, no globals.
``TypeInk`` carries family + weight + size. Migrated painters call
``ramp.ink(step, emphasis="regular")`` and pass those fields through; they do
not think in sans/serif slots or invent one-off page roles.

Unmigrated painters still pass ``face`` + ``bold``. That path is not a
plotter secret: ``FaceBridge`` (owned by the ramp) maps
``(face, bold, size)`` → ``TypeInk``. ``Fpdf2Plotter`` asks
``ramp.resolve_face(...)`` when ``family`` is omitted. Dual path is
intentional until those painters adopt steps.

``family`` stays on the ink so a later dual-font ramp can pick another
catalog family without ripping out the plotter kwarg. Today every step
and every face bridge resolves to ``family="jost"``. Overlay never
changes family.

``EffectiveRamp`` is closed Jost scale defaults ⊕ a frozen ``TypeOverlay``
(optional size/weight per ``TypeStep``). Press / device wiring builds one
ramp and passes it in. Overlay keys match ``ink()``'s step argument;
emphasis is a weight variant of that step, not a second overlay axis.

Today's four page-semantic roles map as:

- ``cover_year`` → ``display``
- ``cover_brow`` → ``eyebrow``
- ``page_title`` → ``title``
- ``chrome`` → ``chrome`` (same token; now a scale step)
"""

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Literal, Protocol

from parch.fonts.catalog import FontCatalog, TypeFamily, TypeWeight, jost_catalog

type TypeStep = Literal[
    "display",
    "title",
    "eyebrow",
    "body",
    "chrome",
    "label",
    "caption",
]
type TypeEmphasis = Literal["regular", "strong"]
type TypeFace = Literal["sans", "serif"]

# Closed ladder, largest → smallest. Every step is used by a painter.
TYPE_STEPS: tuple[TypeStep, ...] = (
    "display",
    "title",
    "eyebrow",
    "body",
    "chrome",
    "label",
    "caption",
)

_WEIGHTS: frozenset[str] = frozenset(("book", "medium", "bold", "heavy"))


class MigratedSurface(StrEnum):
    """Painter entrypoints that must call ``ramp.ink`` — no face-only text."""

    COVER = "paint_cover"
    HEADER = "paint_header"
    NAV = "paint_nav"
    YEAR = "paint_annual"
    MONTH = "paint_month_grid"
    WEEK = "paint_week"
    DAILY = "paint_daily"
    PROJECTS_INDEX = "paint_projects_index"


MIGRATED_SURFACES: frozenset[MigratedSurface] = frozenset(MigratedSurface)

# Habit / meeting / review / tasks stay on FaceBridge this cut.
BRIDGE_BACKLOG: frozenset[str] = frozenset(
    {
        "paint_habit_grid",
        "paint_meetings_index",
        "paint_meeting",
        "paint_review_index",
        "paint_review",
        "paint_tasks_index",
        "paint_task",
    }
)


@dataclass(frozen=True, slots=True)
class TypeInk:
    """Resolved family / weight / size for ``Plotter.text``."""

    family: TypeFamily
    weight: TypeWeight
    size: float


@dataclass(frozen=True, slots=True)
class ScaleCut:
    """One closed step: a size plus the regular / strong Jost cuts."""

    size: float
    regular: TypeWeight
    strong: TypeWeight


# Audit of painter sizes, snapped to seven steps. Nearby one-offs collapse
# onto the nearest cut (6.2/6.6 → label 6.4; 7.0/7.6 → chrome 7.4;
# 5.2–5.8 → caption 5.4; 8.5 → body 8.2; 9.2 → title 11). No unused steps.
JOST_SCALE: dict[TypeStep, ScaleCut] = {
    "display": ScaleCut(size=42, regular="heavy", strong="heavy"),
    "title": ScaleCut(size=11, regular="medium", strong="bold"),
    "eyebrow": ScaleCut(size=10, regular="medium", strong="bold"),
    "body": ScaleCut(size=8.2, regular="book", strong="bold"),
    "chrome": ScaleCut(size=7.4, regular="book", strong="bold"),
    "label": ScaleCut(size=6.4, regular="book", strong="bold"),
    "caption": ScaleCut(size=5.4, regular="book", strong="bold"),
}


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

    def ink(self, step: TypeStep, emphasis: TypeEmphasis = "regular") -> TypeInk:
        """Resolve a closed scale step (+ optional emphasis) to plotter ink."""
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


def scale_ink(step: TypeStep, emphasis: TypeEmphasis = "regular") -> TypeInk:
    """Look up the closed Jost scale table. Raises ``KeyError`` on an unknown step."""
    cut = JOST_SCALE[step]
    weight = cut.regular if emphasis == "regular" else cut.strong
    return TypeInk(family="jost", weight=weight, size=cut.size)


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
    """Frozen partial overrides keyed by ``TypeStep``. Pure data — no I/O.

    Each step is optional. A present ``TypePatch`` may set size, weight, or
    both; ``None`` on a patch field keeps the closed default for that field.
    A patch applies to both emphases of the step; an explicit weight
    replaces the emphasis-derived cut.
    """

    display: TypePatch | None = None
    title: TypePatch | None = None
    eyebrow: TypePatch | None = None
    body: TypePatch | None = None
    chrome: TypePatch | None = None
    label: TypePatch | None = None
    caption: TypePatch | None = None

    def patch(self, step: TypeStep) -> TypePatch | None:
        return getattr(self, step)


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
    """Later overlay's explicit fields win per step, then per size/weight."""
    acc = TypeOverlay()
    for overlay in overlays:
        if overlay is None:
            continue
        acc = TypeOverlay(
            **{step: _compose_patch(acc.patch(step), overlay.patch(step)) for step in TYPE_STEPS}
        )
    return acc


def _resolve_step(
    catalog: FontCatalog,
    step: TypeStep,
    emphasis: TypeEmphasis,
    overlay: TypeOverlay,
) -> TypeInk:
    ink = apply_overlay(scale_ink(step, emphasis), overlay.patch(step))
    catalog.path(ink.family, ink.weight)
    return ink


@dataclass(frozen=True, slots=True)
class JostRamp:
    """Single-family Jost scale + face bridge. Closed default table."""

    catalog: FontCatalog = field(default_factory=jost_catalog)

    def ink(self, step: TypeStep, emphasis: TypeEmphasis = "regular") -> TypeInk:
        return _resolve_step(self.catalog, step, emphasis, TypeOverlay())

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
    """Closed Jost scale ⊕ overlay. Painters call ``ink``; they never read the overlay."""

    overlay: TypeOverlay = field(default_factory=TypeOverlay)
    catalog: FontCatalog = field(default_factory=jost_catalog)

    def ink(self, step: TypeStep, emphasis: TypeEmphasis = "regular") -> TypeInk:
        return _resolve_step(self.catalog, step, emphasis, self.overlay)

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

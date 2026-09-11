"""Role-based type: painters ask for roles; a ramp resolves plotter ink.

Explicit object — no ambient container, no signature injection, no globals.
``TypeInk`` carries family + weight + size. Painters call ``ramp.ink(role)``
and pass those fields through; they do not think in sans/serif slots.

``family`` stays on the ink so a later dual-font ramp can pick another
catalog family without ripping out the plotter kwarg. Today every role
resolves to ``family="jost"``. Overlay never changes family.

Closed default set is today's ``TypeRole`` (four keys). A TypeStep ladder
(display/title/eyebrow/body/chrome/label/caption × emphasis) is larger;
this spike keeps the smaller closed table and stacks device / house /
press overlays as data.
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
    """Partial ink override. Missing fields keep the lower layer. No I/O."""

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
    both; ``None`` on a patch field keeps the lower layer for that field.
    Family is never a field — overlays cannot imply a family.
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


def _merge_patch(lower: TypePatch | None, upper: TypePatch | None) -> TypePatch | None:
    """Later explicit field wins; missing keeps the lower patch field."""
    if upper is None:
        return lower
    if lower is None:
        return upper
    return TypePatch(
        size=upper.size if upper.size is not None else lower.size,
        weight=upper.weight if upper.weight is not None else lower.weight,
    )


def merge_overlays(*layers: TypeOverlay | None) -> TypeOverlay:
    """Merge overlays bottom → top. Later wins field-wise.

    Rules:

    1. ``None`` layer is skipped (optional house / unused slot).
    2. Missing role keeps the lower layer's patch.
    3. Present role, missing field keeps the lower field.
    4. Present role, explicit field wins (later layer).
    5. Family is never implied or overlaid — ``TypePatch`` has no family.
    """
    acc = TypeOverlay()
    for layer in layers:
        if layer is None:
            continue
        acc = TypeOverlay(
            cover_year=_merge_patch(acc.cover_year, layer.cover_year),
            cover_brow=_merge_patch(acc.cover_brow, layer.cover_brow),
            page_title=_merge_patch(acc.page_title, layer.page_title),
            chrome=_merge_patch(acc.chrome, layer.chrome),
        )
    return acc


@dataclass(frozen=True, slots=True)
class OverlayStack:
    """Named ordered overlays above in-code defaults. Later wins field-wise.

    Bottom → top after defaults:

    1. ``device`` — device-owned scale (Nomad bumps chrome).
    2. ``house`` — optional house/style layer (skipped when ``None``).
    3. ``press`` — press/job layer (this spike bumps page_title).

    CLI/ephemeral is omitted: existing flags overlay spec year/month/day,
    not type. ``press()`` builds this stack and passes one ``EffectiveRamp``.
    Painters never see the stack — only ``ramp.ink``.
    """

    device: TypeOverlay | None = None
    house: TypeOverlay | None = None
    press: TypeOverlay | None = None

    def layers(self) -> tuple[TypeOverlay | None, TypeOverlay | None, TypeOverlay | None]:
        return (self.device, self.house, self.press)

    def merge(self) -> TypeOverlay:
        return merge_overlays(*self.layers())


# Optional house/style slot. Empty — reserved; supply a real overlay via
# ``press(..., house=)`` or ``OverlayStack(house=...)`` to occupy the layer.
HOUSE_TYPE_OVERLAY = TypeOverlay()

# Press/job layer for this spike. Distinct from Nomad chrome so both
# layers read on one page (header title vs chrome meta/nav).
PRESS_TITLE_SIZE = 13.0
PRESS_TITLE_WEIGHT: TypeWeight = "bold"
PRESS_TYPE_OVERLAY = TypeOverlay(
    page_title=TypePatch(size=PRESS_TITLE_SIZE, weight=PRESS_TITLE_WEIGHT),
)


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
    """Closed Jost defaults ⊕ merged overlay stack.

    Painters call ``ink``; they never read the overlay or the stack.
    """

    overlay: TypeOverlay = field(default_factory=TypeOverlay)
    catalog: FontCatalog = field(default_factory=jost_catalog)

    def ink(self, role: TypeRole) -> TypeInk:
        if role not in _ROLES:
            raise KeyError(f"unknown type role {role!r}")
        ink = apply_overlay(_JOST[role], self.overlay.patch(role))
        self.catalog.path(ink.family, ink.weight)
        return ink

    @classmethod
    def from_stack(
        cls, stack: OverlayStack, catalog: FontCatalog | None = None
    ) -> "EffectiveRamp":
        return cls(overlay=stack.merge(), catalog=catalog or jost_catalog())


def bind_ramp(
    *,
    ramp: TypeRamp | None = None,
    stack: OverlayStack | None = None,
    overlay: TypeOverlay | None = None,
) -> TypeRamp:
    """Explicit ``ramp`` wins the whole object. Else stack, else one overlay."""
    if ramp is not None:
        return ramp
    if stack is not None:
        return EffectiveRamp.from_stack(stack)
    return EffectiveRamp(overlay=TypeOverlay() if overlay is None else overlay)

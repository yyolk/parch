"""Typographic scale: painters pick a step, not a page name.

Explicit object — no ambient container, no signature injection, no globals.
``TypeInk`` carries family + weight + size. Painters pass a frozen
``TypeRef`` (``TypeStep`` + optional emphasis + optional size) or the ink
itself. ``Plotter.text`` takes ``ink=`` or ``ref=`` resolved at the
plotter edge via ``plotter.ramp``. They do not think in sans/serif slots
or invent one-off page roles.

Ratio-driven steps take size from ``pt_from_em(root_body, JOST_RATIOS[step])``.
``JOST_RATIOS`` values are ``Em`` (multiples of ``root_body``). ``display`` is
a fixed-``Pt`` exception (cover year) and does not track root. Root lives on
``Device.root_body: Pt`` and on the ramp (``JostRamp`` / ``EffectiveRamp``).
Press constructs the ramp with the device root.

**Overlay size is an absolute ``Pt`` override for that step.** It does not
change ``root_body`` and does not rescale sibling steps. A chrome
``size=9.6`` patch leaves title / body / micro at their em-derived
sizes. ``TypeRef.size`` is a per-call absolute ``Pt`` override and wins over
both the em size and an overlay size.

``family`` stays on the ink so a later dual-font ramp can pick another
catalog family without ripping out the plotter path. Today every step
resolves to ``family="jost"``. Overlay never changes family.

``EffectiveRamp`` is closed Jost scale defaults ⊕ stacked frozen
``TypeOverlay`` layers (optional size/weight per ``TypeStep``). Press
builds

    EffectiveRamp = defaults ⊕ device ⊕ toml ⊕ proof (if on)

at ``device.root_body``. Overlay keys match ``ink()``'s step argument;
emphasis is a weight variant of that step, not a second overlay axis.

Press TOML may set ``[typography.overlay.<step>]`` size/weight. Merge
order is ``defaults ⊕ device ⊕ toml ⊕ proof`` (optional
``press(..., overlay=)`` layers last). Overlay never changes family.

``validate_overlay`` is pure — no I/O — and returns ``OverlayOk`` or a
typed issue (unknown step, bad weight, bad size, version mismatch).
``schema_version`` policy today: **exact match**. Press validates before
``bind_ramp`` builds ``EffectiveRamp``. Old role names (``cover_year``,
``cover_brow``, ``page_title``) are unknown steps.
"""

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Literal, NewType, Protocol

from parch import ConfigError
from parch.fonts.catalog import FontCatalog, TypeFamily, TypeWeight, jost_catalog

# Thin size tags at the ramp / device / overlay / ink boundary.
# Em = multiple of root_body; Pt = absolute PDF point. No Mm/Px, no operators.
Em = NewType("Em", float)
Pt = NewType("Pt", float)


def pt_from_em(root: Pt, em: Em) -> Pt:
    """Resolve an em multiple against an absolute root. Pure."""
    return Pt(float(root) * float(em))


type TypeStep = Literal[
    "display",
    "title",
    "eyebrow",
    "body",
    "chrome",
    "label",
    "caption",
    "micro",
]
type TypeEmphasis = Literal["regular", "strong"]

# Closed ladder, largest → smallest. Every step is used by a painter.
TYPE_STEPS: tuple[TypeStep, ...] = (
    "display",
    "title",
    "eyebrow",
    "body",
    "chrome",
    "label",
    "caption",
    "micro",
)

_WEIGHTS: frozenset[str] = frozenset(("book", "medium", "bold", "heavy"))
TYPE_WEIGHTS = _WEIGHTS
TYPE_PATCH_KEYS: frozenset[str] = frozenset(("size", "weight"))

OVERLAY_SCHEMA_VERSION = 1

# Inclusive size bands (pt) per closed step. Nonpositive is a separate issue.
OVERLAY_SIZE_RANGE: dict[str, tuple[float, float]] = {
    "display": (18.0, 72.0),
    "title": (8.0, 24.0),
    "eyebrow": (6.0, 24.0),
    "body": (6.0, 16.0),
    "chrome": (5.0, 16.0),
    "label": (4.0, 12.0),
    "caption": (4.0, 10.0),
    "micro": (2.5, 8.0),
}


class MigratedSurface(StrEnum):
    """Painter entrypoints that must pass ``TypeRef`` / ink — no face-only text."""

    COVER = "paint_cover"
    HEADER = "paint_header"
    NAV = "paint_nav"
    YEAR = "paint_annual"
    MONTH = "paint_month_grid"
    WEEK = "paint_week"
    DAILY = "paint_daily"
    DAILY_NOTES = "paint_notes"
    SCHEDULE = "paint_schedule"
    PRIORITIES = "paint_priorities"
    PROJECTS_INDEX = "paint_projects_index"
    PROJECT = "paint_project"
    QUARTER = "paint_quarter"
    HABIT = "paint_habit_grid"
    MEETINGS_INDEX = "paint_meetings_index"
    MEETING = "paint_meeting"
    REVIEW_INDEX = "paint_review_index"
    REVIEW = "paint_review"
    TASKS_INDEX = "paint_tasks_index"
    TASK = "paint_task"


MIGRATED_SURFACES: frozenset[MigratedSurface] = frozenset(MigratedSurface)


@dataclass(frozen=True, slots=True)
class TypeInk:
    """Resolved family / weight / size for ``Plotter.text``."""

    family: TypeFamily
    weight: TypeWeight
    size: Pt


@dataclass(frozen=True, slots=True)
class TypeRef:
    """Painter-facing type request. ``TypeStep`` vocabulary only.

    No family, no weight. Optional ``emphasis`` and ``size``. ``size`` is
    an absolute ``Pt`` override of the step default (and an overlay size)
    for that one call.
    """

    step: TypeStep
    emphasis: TypeEmphasis = "regular"
    size: Pt | None = None

    def __post_init__(self) -> None:
        if self.step not in TYPE_STEPS:
            raise ValueError(f"unknown type step {self.step!r}")
        if self.emphasis not in ("regular", "strong"):
            raise ValueError(f"unknown emphasis {self.emphasis!r}")
        if self.size is not None and self.size <= 0:
            raise ValueError(f"size must be > 0, not {self.size}")


@dataclass(frozen=True, slots=True)
class ScaleCut:
    """One closed step: a resolved ``Pt`` plus the regular / strong Jost cuts."""

    size: Pt
    regular: TypeWeight
    strong: TypeWeight


# Default / Nomad body. Ratio-driven steps are ``pt_from_em(root_body, JOST_RATIOS)``.
ROOT_BODY = Pt(8.5)
DISPLAY_SIZE = Pt(42.0)

# Target sizes at ``ROOT_BODY``. ``display`` is the fixed-pt exception.
_STEP_AT_ROOT: dict[TypeStep, Pt] = {
    "title": Pt(11),
    "eyebrow": Pt(10),
    "body": Pt(8.5),
    "chrome": Pt(7.4),
    "label": Pt(6.4),
    "caption": Pt(5.4),
    "micro": Pt(4.3),
}

# ``size`` and ``ROOT_BODY`` are ``Pt``; peel tags → divide as bare float → wrap ``Em``.
# Same boundary as ``pt_from_em``. Avoid reading Pt/Pt as still points.
JOST_RATIOS: dict[TypeStep, Em] = {
    step: Em(float(size) / float(ROOT_BODY)) for step, size in _STEP_AT_ROOT.items()
}

_STEP_WEIGHTS: dict[TypeStep, tuple[TypeWeight, TypeWeight]] = {
    "display": ("heavy", "heavy"),
    "title": ("medium", "bold"),
    "eyebrow": ("medium", "bold"),
    "body": ("book", "bold"),
    "chrome": ("book", "bold"),
    "label": ("book", "bold"),
    "caption": ("book", "bold"),
    "micro": ("book", "bold"),
}


def step_size(step: TypeStep, root_body: Pt = ROOT_BODY) -> Pt:
    """Em-derived size, or the fixed display exception."""
    if step == "display":
        return DISPLAY_SIZE
    return pt_from_em(root_body, JOST_RATIOS[step])


def scale_cut(step: TypeStep, root_body: Pt = ROOT_BODY) -> ScaleCut:
    """One closed step at ``root_body`` (display ignores root)."""
    regular, strong = _STEP_WEIGHTS[step]
    return ScaleCut(size=step_size(step, root_body), regular=regular, strong=strong)


def jost_scale(root_body: Pt = ROOT_BODY) -> dict[TypeStep, ScaleCut]:
    """Closed scale table at ``root_body``. Overlay validation keys off the steps."""
    return {step: scale_cut(step, root_body) for step in TYPE_STEPS}


# Default-root snapshot. Tests and ``jost_defaults()`` read this table.
JOST_SCALE: dict[TypeStep, ScaleCut] = jost_scale()


class TypeRamp(Protocol):
    catalog: FontCatalog

    def ink(self, step: TypeStep, emphasis: TypeEmphasis = "regular") -> TypeInk:
        """Resolve a closed scale step (+ optional emphasis) to plotter ink."""
        ...

    def resolve(self, ref: TypeRef) -> TypeInk:
        """Resolve a painter ``TypeRef`` to plotter-ready ink."""
        ...


def resolve_ref(ramp: TypeRamp, ref: TypeRef) -> TypeInk:
    """``ramp.ink(step, emphasis)``, then an explicit ``TypeRef.size`` wins.

    Uses ``ink()`` so stub ramps that only implement ``ink`` still work.
    """
    ink = ramp.ink(ref.step, ref.emphasis)
    if ref.size is None:
        return ink
    return TypeInk(family=ink.family, weight=ink.weight, size=Pt(float(ref.size)))


def scale_ink(
    step: TypeStep,
    emphasis: TypeEmphasis = "regular",
    *,
    root_body: Pt = ROOT_BODY,
) -> TypeInk:
    """Look up the closed Jost scale at ``root_body``. Raises ``KeyError`` on an unknown step."""
    cut = scale_cut(step, root_body)
    weight = cut.regular if emphasis == "regular" else cut.strong
    return TypeInk(family="jost", weight=weight, size=cut.size)


@dataclass(frozen=True, slots=True)
class TypePatch:
    """Partial ink override. Missing fields keep the default. No I/O."""

    size: Pt | None = None
    weight: TypeWeight | None = None

    def __post_init__(self) -> None:
        if self.size is not None and self.size <= 0:
            raise ValueError(f"size must be > 0, not {self.size}")
        if self.weight is not None and self.weight not in _WEIGHTS:
            raise ValueError(f"unknown weight {self.weight!r}")


@dataclass(frozen=True, slots=True)
class TypeOverlay:
    """Frozen partial overrides keyed by ``TypeStep``. Pure data — no I/O.

    ``schema_version`` version-locks the shape. Policy today: exact match of
    ``OVERLAY_SCHEMA_VERSION``. Each step is optional. A present ``TypePatch``
    may set size, weight, or both; ``None`` on a patch field keeps the closed
    default for that field. A patch applies to both emphases of the step; an
    explicit weight replaces the emphasis-derived cut. Overlay size is an
    absolute ``Pt`` override for that step — it does not change ``root_body``.
    """

    schema_version: int = OVERLAY_SCHEMA_VERSION
    display: TypePatch | None = None
    title: TypePatch | None = None
    eyebrow: TypePatch | None = None
    body: TypePatch | None = None
    chrome: TypePatch | None = None
    label: TypePatch | None = None
    caption: TypePatch | None = None
    micro: TypePatch | None = None

    def patch(self, step: TypeStep) -> TypePatch | None:
        return getattr(self, step)

    @classmethod
    def from_mapping(cls, table: Mapping[str, object]) -> TypeOverlay:
        """Parse a step→patch table (plus ``schema_version``). Typed issues fail."""
        match validate_overlay(table, jost_defaults()):
            case OverlayOk(overlay=ok):
                return ok
            case issue:
                raise ValueError(str(issue))


def jost_defaults() -> dict[TypeStep, ScaleCut]:
    """Closed Jost scale table. Overlay validation keys off this map."""
    return dict(JOST_SCALE)


@dataclass(frozen=True, slots=True)
class OverlayOk:
    """Successful ``validate_overlay`` — ready to bind an ``EffectiveRamp``."""

    overlay: TypeOverlay


@dataclass(frozen=True, slots=True)
class UnknownStep:
    step: str

    def __str__(self) -> str:
        return f"unknown step {self.step!r}"


@dataclass(frozen=True, slots=True)
class BadWeight:
    weight: object
    step: str

    def __str__(self) -> str:
        return f"bad weight {self.weight!r} for step {self.step!r}"


@dataclass(frozen=True, slots=True)
class NonpositiveSize:
    size: object
    step: str

    def __str__(self) -> str:
        return f"nonpositive size {self.size!r} for step {self.step!r}"


@dataclass(frozen=True, slots=True)
class SizeOutOfRange:
    size: float
    step: str
    lo: float
    hi: float

    def __str__(self) -> str:
        return f"size {self.size} for step {self.step!r} not in [{self.lo:g}, {self.hi:g}]"


@dataclass(frozen=True, slots=True)
class VersionMismatch:
    got: object
    expected: int = OVERLAY_SCHEMA_VERSION

    def __str__(self) -> str:
        return (
            f"schema_version {self.got!r} does not exactly match {self.expected} "
            "(exact version match for now)"
        )


type OverlayIssue = UnknownStep | BadWeight | NonpositiveSize | SizeOutOfRange | VersionMismatch
type OverlayResult = OverlayOk | OverlayIssue
type OverlayData = TypeOverlay | Mapping[str, object]


def _as_float(value: object) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return float(value)


def _check_patch(step: str, size: object | None, weight: object | None) -> OverlayIssue | None:
    if weight is not None and weight not in _WEIGHTS:
        return BadWeight(weight=weight, step=step)
    if size is None:
        return None
    parsed = _as_float(size)
    if parsed is None:
        return NonpositiveSize(size=size, step=step)
    if parsed <= 0:
        return NonpositiveSize(size=parsed, step=step)
    lo, hi = OVERLAY_SIZE_RANGE[step]
    if not lo <= parsed <= hi:
        return SizeOutOfRange(size=parsed, step=step, lo=lo, hi=hi)
    return None


def _overlay_from_fields(
    schema_version: int,
    patches: Mapping[str, TypePatch | None],
) -> TypeOverlay:
    return TypeOverlay(
        schema_version=schema_version,
        **{step: patches.get(step) for step in TYPE_STEPS},
    )


def validate_overlay(overlay: OverlayData, defaults: Mapping[str, object]) -> OverlayResult:
    """Pure overlay check. No I/O. ``defaults`` is the closed step table.

    Accepts a ``TypeOverlay`` or a mapping (press TOML / future ``parch new``).
    Mapping keys besides ``schema_version`` are step names — unknown names
    (including old role keys like ``cover_year``) are ``UnknownStep``.
    Version policy: exact match of ``OVERLAY_SCHEMA_VERSION``.
    """
    allowed = frozenset(defaults)
    if isinstance(overlay, TypeOverlay):
        if overlay.schema_version != OVERLAY_SCHEMA_VERSION:
            return VersionMismatch(got=overlay.schema_version)
        for step in TYPE_STEPS:
            patch = overlay.patch(step)
            if patch is None:
                continue
            if step not in allowed:
                return UnknownStep(step=step)
            issue = _check_patch(step, patch.size, patch.weight)
            if issue is not None:
                return issue
        return OverlayOk(overlay=overlay)

    if overlay.get("schema_version") != OVERLAY_SCHEMA_VERSION:
        return VersionMismatch(got=overlay.get("schema_version"))

    built: dict[str, TypePatch | None] = {}
    for key, raw in overlay.items():
        if key == "schema_version":
            continue
        if key not in allowed:
            return UnknownStep(step=str(key))
        if raw is None:
            built[key] = None
            continue
        if not isinstance(raw, Mapping):
            return UnknownStep(step=str(key))
        extra = set(raw) - TYPE_PATCH_KEYS
        if extra:
            return UnknownStep(step=f"{key}.{next(iter(sorted(extra)))}")
        size = raw.get("size")
        weight = raw.get("weight")
        issue = _check_patch(key, size, weight)
        if issue is not None:
            return issue
        built[key] = TypePatch(
            size=None if size is None else Pt(float(size)),
            weight=None if weight is None else weight,  # type: ignore[arg-type]
        )
    return OverlayOk(overlay=_overlay_from_fields(OVERLAY_SCHEMA_VERSION, built))


def require_overlay(overlay: OverlayData, defaults: Mapping[str, object]) -> TypeOverlay:
    """``validate_overlay`` then ``ConfigError`` — used by press/device/bind."""
    match validate_overlay(overlay, defaults):
        case OverlayOk(overlay=ok):
            return ok
        case issue:
            raise ConfigError(f"type overlay: {issue}")


def apply_overlay(base: TypeInk, patch: TypePatch | None) -> TypeInk:
    """Explicit patch field wins; missing field keeps ``base``. Family stays."""
    if patch is None:
        return base
    return TypeInk(
        family=base.family,
        weight=base.weight if patch.weight is None else patch.weight,
        size=base.size if patch.size is None else Pt(float(patch.size)),
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
    root_body: Pt,
) -> TypeInk:
    ink = apply_overlay(scale_ink(step, emphasis, root_body=root_body), overlay.patch(step))
    catalog.path(ink.family, ink.weight)
    return ink


def _require_root_body(root_body: Pt) -> Pt:
    if root_body <= 0:
        raise ValueError(f"root_body must be > 0, not {root_body}")
    return Pt(float(root_body))


@dataclass(frozen=True, slots=True)
class JostRamp:
    """Single-family Jost scale. Sizes from ``root_body ×`` ratios (display fixed)."""

    root_body: Pt = ROOT_BODY
    catalog: FontCatalog = field(default_factory=jost_catalog)

    def __post_init__(self) -> None:
        _require_root_body(self.root_body)

    def ink(self, step: TypeStep, emphasis: TypeEmphasis = "regular") -> TypeInk:
        return _resolve_step(self.catalog, step, emphasis, TypeOverlay(), self.root_body)

    def resolve(self, ref: TypeRef) -> TypeInk:
        return resolve_ref(self, ref)


@dataclass(frozen=True, slots=True)
class EffectiveRamp:
    """Closed Jost scale at ``root_body`` ⊕ overlay.

    Painters call ``ink`` / pass refs; they never read the overlay.
    Overlay size is an absolute ``Pt`` override for that step only.
    """

    overlay: TypeOverlay = field(default_factory=TypeOverlay)
    root_body: Pt = ROOT_BODY
    catalog: FontCatalog = field(default_factory=jost_catalog)

    def __post_init__(self) -> None:
        _require_root_body(self.root_body)

    def ink(self, step: TypeStep, emphasis: TypeEmphasis = "regular") -> TypeInk:
        return _resolve_step(self.catalog, step, emphasis, self.overlay, self.root_body)

    def resolve(self, ref: TypeRef) -> TypeInk:
        return resolve_ref(self, ref)


def bind_ramp(
    *,
    ramp: TypeRamp | None = None,
    overlay: OverlayData | None = None,
    defaults: Mapping[str, object] | None = None,
    root_body: Pt | None = None,
) -> TypeRamp:
    """Explicit ``ramp`` wins. Otherwise validate, then ``EffectiveRamp`` at ``root_body``."""
    if ramp is not None:
        return ramp
    table = JOST_SCALE if defaults is None else defaults
    checked = require_overlay(TypeOverlay() if overlay is None else overlay, table)
    return EffectiveRamp(
        overlay=checked,
        root_body=ROOT_BODY if root_body is None else root_body,
    )


# Slightly larger chrome / title / eyebrow than the closed scale — on-screen
# review. Device overlay stays a separate layer and is not mutated here.
# Keys are TypeStep names (not the old page-semantic roles).
PROOF_CHROME_SIZE = Pt(9.2)
PROOF_TITLE_SIZE = Pt(13.0)
PROOF_EYEBROW_SIZE = Pt(12.0)


@dataclass(frozen=True, slots=True)
class ProofProfile:
    """Press-mode overlay for proofs / specimens (on-screen review).

    Selected by ``press(..., proof=True)`` or ``parch proof``. Composition is
    ``defaults ⊕ device ⊕ toml ⊕ proof``. Does not change Nomad's identity
    device overlay. ``display`` (cover year) is not patched.
    """

    overlay: TypeOverlay = field(
        default_factory=lambda: TypeOverlay(
            chrome=TypePatch(size=PROOF_CHROME_SIZE),
            title=TypePatch(size=PROOF_TITLE_SIZE),
            eyebrow=TypePatch(size=PROOF_EYEBROW_SIZE),
        )
    )


PROOF_PROFILE = ProofProfile()

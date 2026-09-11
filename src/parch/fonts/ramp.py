"""Role-based type: painters ask for roles; a ramp resolves plotter ink.

Explicit object — no ambient container, no signature injection, no globals.
``TypeInk`` carries family + weight + size. Painters call ``ramp.ink(role)``
and pass those fields through; they do not think in sans/serif slots.

``family`` stays on the ink so a later dual-font ramp can pick another
catalog family without ripping out the plotter kwarg. Today every role
resolves to ``family="jost"``. Overlay never changes family.

Thesis S: overlay is **safe data**. ``TypeOverlay`` carries ``schema_version``.
``validate_overlay(overlay, defaults)`` is pure — no I/O — and returns
``OverlayOk`` or a typed issue (unknown step, bad weight, nonpositive size,
size out of range, version mismatch). Press/device validate before building
``EffectiveRamp``. Version policy today: **exact match**.
"""

from dataclasses import dataclass, field
from typing import Literal, Mapping, Protocol

from parch import ConfigError
from parch.fonts.catalog import FontCatalog, TypeFamily, TypeWeight, jost_catalog

# Closed step/role keys — same four as today's TypeRole table. A TypeStep
# ladder (display/title/eyebrow/body/chrome/label/caption × emphasis) is
# larger; unknown names fail validation rather than inventing a role.
type TypeRole = Literal["cover_year", "cover_brow", "page_title", "chrome"]
type TypeStep = TypeRole

OVERLAY_SCHEMA_VERSION = 1

_STEPS: frozenset[str] = frozenset(("cover_year", "cover_brow", "page_title", "chrome"))
_WEIGHTS: frozenset[str] = frozenset(("book", "medium", "bold", "heavy"))
_PATCH_FIELDS: frozenset[str] = frozenset(("size", "weight"))

# Inclusive size bands (pt) per closed step. Nonpositive is a separate issue.
OVERLAY_SIZE_RANGE: dict[str, tuple[float, float]] = {
    "cover_year": (18.0, 72.0),
    "cover_brow": (6.0, 24.0),
    "page_title": (8.0, 24.0),
    "chrome": (5.0, 16.0),
}


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


def jost_defaults() -> dict[TypeRole, TypeInk]:
    """Closed Jost default table. Overlay validation keys off this map."""
    return dict(_JOST)


@dataclass(frozen=True, slots=True)
class TypePatch:
    """Partial ink override. Missing fields keep the default. No I/O.

    Invariants live in ``validate_overlay`` — the constructor stays open so
    raw / future ``parch new`` data can be checked as data, not by
    ``__post_init__`` side effects.
    """

    size: float | None = None
    weight: TypeWeight | None = None


@dataclass(frozen=True, slots=True)
class TypeOverlay:
    """Frozen partial overrides keyed by closed step/role. Pure data — no I/O.

    ``schema_version`` version-locks the shape for later ``parch new`` /
    ``parch edit``. Policy today: exact match of ``OVERLAY_SCHEMA_VERSION``.
    """

    schema_version: int = OVERLAY_SCHEMA_VERSION
    cover_year: TypePatch | None = None
    cover_brow: TypePatch | None = None
    page_title: TypePatch | None = None
    chrome: TypePatch | None = None

    def patch(self, step: TypeStep) -> TypePatch | None:
        match step:
            case "cover_year":
                return self.cover_year
            case "cover_brow":
                return self.cover_brow
            case "page_title":
                return self.page_title
            case "chrome":
                return self.chrome


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
        cover_year=patches.get("cover_year"),
        cover_brow=patches.get("cover_brow"),
        page_title=patches.get("page_title"),
        chrome=patches.get("chrome"),
    )


def validate_overlay(overlay: OverlayData, defaults: Mapping[str, TypeInk]) -> OverlayResult:
    """Pure overlay check. No I/O. ``defaults`` is the closed step table.

    Accepts a ``TypeOverlay`` or a mapping (future ``parch new`` / TOML shape).
    Mapping keys besides ``schema_version`` are step names — unknown names are
    ``UnknownStep``. Version policy: exact match of ``OVERLAY_SCHEMA_VERSION``.
    """
    allowed = frozenset(defaults)
    if isinstance(overlay, TypeOverlay):
        if overlay.schema_version != OVERLAY_SCHEMA_VERSION:
            return VersionMismatch(got=overlay.schema_version)
        for step in _STEPS:
            patch = overlay.patch(step)  # type: ignore[arg-type]
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
        extra = set(raw) - _PATCH_FIELDS
        if extra:
            return UnknownStep(step=f"{key}.{next(iter(extra))}")
        size = raw.get("size")
        weight = raw.get("weight")
        issue = _check_patch(key, size, weight)
        if issue is not None:
            return issue
        built[key] = TypePatch(
            size=None if size is None else float(size),
            weight=None if weight is None else weight,  # type: ignore[arg-type]
        )
    return OverlayOk(overlay=_overlay_from_fields(OVERLAY_SCHEMA_VERSION, built))


def require_overlay(overlay: OverlayData, defaults: Mapping[str, TypeInk]) -> TypeOverlay:
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
            schema_version=OVERLAY_SCHEMA_VERSION,
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
    """Closed Jost defaults ⊕ validated overlay. Painters call ``ink`` only."""

    overlay: TypeOverlay = field(default_factory=TypeOverlay)
    catalog: FontCatalog = field(default_factory=jost_catalog)

    def ink(self, role: TypeRole) -> TypeInk:
        if role not in _STEPS:
            raise KeyError(f"unknown type role {role!r}")
        ink = apply_overlay(_JOST[role], self.overlay.patch(role))
        self.catalog.path(ink.family, ink.weight)
        return ink


def bind_ramp(
    *,
    ramp: TypeRamp | None = None,
    overlay: OverlayData | None = None,
    defaults: Mapping[str, TypeInk] | None = None,
) -> TypeRamp:
    """Explicit ``ramp`` wins. Otherwise validate, then ``EffectiveRamp``."""
    if ramp is not None:
        return ramp
    table = _JOST if defaults is None else defaults
    checked = require_overlay(TypeOverlay() if overlay is None else overlay, table)
    return EffectiveRamp(overlay=checked)

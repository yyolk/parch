"""Typographic scale: painters pick a step, not a page name.

Explicit object — no ambient container, no signature injection, no globals.
``TypeInk`` carries family + weight + size. Painters pass a frozen
``TypeRef`` (``TypeStep`` + optional emphasis) or the ink itself.
``Plotter.text`` takes ``ink=`` or ``ref=`` resolved at the plotter edge
via ``plotter.ramp.ink``. They do not think in sans/serif slots or invent
one-off page roles.

Ratio-driven steps take size from ``pt_from_em(root_body, JOST_RATIOS[step])``.
``JOST_RATIOS`` values are ``Em`` (multiples of ``root_body``). ``display`` is
a fixed-``Pt`` exception (cover year) and does not track root. Root lives on
``Device.root_body: Pt`` and on ``EffectiveRamp``. Press constructs the ramp
with the device root.

**Overlay size is an absolute ``Pt`` override for that step.** It does not
change ``root_body`` and does not rescale sibling steps. A chrome
``size=9.6`` patch leaves title / body / micro at their em-derived sizes.
Absolute ``Pt`` overrides live only on overlay ``TypePatch``.

``family`` stays on the ink. Today every step
resolves to ``family="jost"``. Overlay never changes family.

``EffectiveRamp`` is the closed Jost scale at ``root_body`` ⊕ a stacked
frozen ``TypeOverlay`` (optional size/weight per ``TypeStep``). Press
builds

    EffectiveRamp = defaults ⊕ toml ⊕ proof (if on) ⊕ press kwarg

at ``device.root_body``. Overlay keys match ``ink()``'s step argument;
emphasis is a weight variant of that step, not a second overlay axis.

Press TOML may set ``[typography.overlay.<step>]`` size/weight.
``require_overlay`` is pure — no I/O — and raises ``ConfigError`` on an
unknown step, bad weight, bad size, or version mismatch.
``schema_version`` policy today: **exact match**. Press validates before
``bind_ramp``. Old role names (``cover_year``, ``cover_brow``,
``page_title``) are unknown steps.
"""

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Literal, NewType, Protocol

from parch import ConfigError
from parch.fonts.catalog import FontCatalog, TypeFamily, TypeWeight, jost_catalog

# Thin size tags at the ramp / overlay / ink boundary.
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
_PATCH_KEYS: frozenset[str] = frozenset(("size", "weight"))

OVERLAY_SCHEMA_VERSION = 1

# Inclusive size bands (pt) per closed step. Nonpositive is a separate check.
_SIZE_RANGE: dict[str, tuple[float, float]] = {
    "display": (18.0, 72.0),
    "title": (8.0, 24.0),
    "eyebrow": (6.0, 24.0),
    "body": (6.0, 16.0),
    "chrome": (5.0, 16.0),
    "label": (4.0, 12.0),
    "caption": (4.0, 10.0),
    "micro": (2.5, 8.0),
}


@dataclass(frozen=True, slots=True)
class TypeInk:
    """Resolved family / weight / size for ``Plotter.text``."""

    family: TypeFamily
    weight: TypeWeight
    size: Pt


@dataclass(frozen=True, slots=True)
class TypeRef:
    """Painter-facing type request. ``TypeStep`` vocabulary only.

    No family, no weight, no per-call size. Optional ``emphasis``.
    """

    step: TypeStep
    emphasis: TypeEmphasis = "regular"

    def __post_init__(self) -> None:
        if self.step not in TYPE_STEPS:
            raise ValueError(f"unknown type step {self.step!r}")
        if self.emphasis not in ("regular", "strong"):
            raise ValueError(f"unknown emphasis {self.emphasis!r}")


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


def _cut(step: TypeStep, root_body: Pt = ROOT_BODY) -> ScaleCut:
    regular, strong = _STEP_WEIGHTS[step]
    size = (
        DISPLAY_SIZE if step == "display" else pt_from_em(root_body, JOST_RATIOS[step])
    )
    return ScaleCut(size=size, regular=regular, strong=strong)


# Closed table at the default root. Overlay validation keys off the steps.
JOST_SCALE: dict[TypeStep, ScaleCut] = {step: _cut(step) for step in TYPE_STEPS}


class TypeRamp(Protocol):
    catalog: FontCatalog

    def ink(self, step: TypeStep, emphasis: TypeEmphasis = "regular") -> TypeInk:
        """Resolve a closed scale step (+ optional emphasis) to plotter ink."""
        ...

    def resolve(self, ref: TypeRef) -> TypeInk:
        """Resolve a painter ``TypeRef`` to plotter-ready ink."""
        ...


def _ink(
    step: TypeStep,
    emphasis: TypeEmphasis = "regular",
    *,
    root_body: Pt = ROOT_BODY,
) -> TypeInk:
    cut = _cut(step, root_body)
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
        """Parse a step→patch table (plus ``schema_version``). Bad input fails."""
        return require_overlay(table)


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
            **{
                step: _compose_patch(acc.patch(step), overlay.patch(step))
                for step in TYPE_STEPS
            }
        )
    return acc


def _as_float(value: object) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return float(value)


def _check_patch(step: str, size: object | None, weight: object | None) -> None:
    if weight is not None and weight not in _WEIGHTS:
        raise ConfigError(f"type overlay: bad weight {weight!r} for step {step!r}")
    if size is None:
        return
    parsed = _as_float(size)
    if parsed is None or parsed <= 0:
        raise ConfigError(f"type overlay: nonpositive size {size!r} for step {step!r}")
    lo, hi = _SIZE_RANGE[step]
    if not lo <= parsed <= hi:
        raise ConfigError(
            f"type overlay: size {parsed} for step {step!r} not in [{lo:g}, {hi:g}]"
        )


def _overlay_from_fields(
    schema_version: int,
    patches: Mapping[str, TypePatch | None],
) -> TypeOverlay:
    return TypeOverlay(
        schema_version=schema_version,
        **{step: patches.get(step) for step in TYPE_STEPS},
    )


type OverlayData = TypeOverlay | Mapping[str, object]


def require_overlay(overlay: OverlayData) -> TypeOverlay:
    """Pure overlay check. No I/O. Raises ``ConfigError`` before paint.

    Accepts a ``TypeOverlay`` or a mapping (press TOML / future ``parch new``).
    Mapping keys besides ``schema_version`` are step names — unknown names
    (including old role keys like ``cover_year``) fail. Version policy: exact
    match of ``OVERLAY_SCHEMA_VERSION``.
    """
    if isinstance(overlay, TypeOverlay):
        if overlay.schema_version != OVERLAY_SCHEMA_VERSION:
            raise ConfigError(
                f"type overlay: schema_version {overlay.schema_version!r} does not "
                f"exactly match {OVERLAY_SCHEMA_VERSION} (exact version match for now)"
            )
        for step in TYPE_STEPS:
            patch = overlay.patch(step)
            if patch is None:
                continue
            _check_patch(step, patch.size, patch.weight)
        return overlay

    if overlay.get("schema_version") != OVERLAY_SCHEMA_VERSION:
        raise ConfigError(
            f"type overlay: schema_version {overlay.get('schema_version')!r} does not "
            f"exactly match {OVERLAY_SCHEMA_VERSION} (exact version match for now)"
        )

    built: dict[str, TypePatch | None] = {}
    for key, raw in overlay.items():
        if key == "schema_version":
            continue
        if key not in TYPE_STEPS:
            raise ConfigError(f"type overlay: unknown step {key!r}")
        if raw is None:
            built[key] = None
            continue
        if not isinstance(raw, Mapping):
            raise ConfigError(f"type overlay: unknown step {key!r}")
        extra = set(raw) - _PATCH_KEYS
        if extra:
            raise ConfigError(
                f"type overlay: unknown step {f'{key}.{next(iter(sorted(extra)))}'!r}"
            )
        size = raw.get("size")
        weight = raw.get("weight")
        _check_patch(key, size, weight)
        built[key] = TypePatch(
            size=None if size is None else Pt(float(size)),
            weight=None if weight is None else weight,  # type: ignore[arg-type]
        )
    return _overlay_from_fields(OVERLAY_SCHEMA_VERSION, built)


def _require_root_body(root_body: Pt) -> Pt:
    if root_body <= 0:
        raise ValueError(f"root_body must be > 0, not {root_body}")
    return Pt(float(root_body))


@dataclass(frozen=True, slots=True)
class EffectiveRamp:
    """Closed Jost scale at ``root_body`` ⊕ overlay.

    Default overlay is empty — same ink as the closed table. Painters call
    ``ink`` / pass refs; they never read the overlay. Overlay size is an
    absolute ``Pt`` override for that step only.
    """

    overlay: TypeOverlay = field(default_factory=TypeOverlay)
    root_body: Pt = ROOT_BODY
    catalog: FontCatalog = field(default_factory=jost_catalog)

    def __post_init__(self) -> None:
        _require_root_body(self.root_body)

    def ink(self, step: TypeStep, emphasis: TypeEmphasis = "regular") -> TypeInk:
        ink = apply_overlay(
            _ink(step, emphasis, root_body=self.root_body), self.overlay.patch(step)
        )
        self.catalog.path(ink.family, ink.weight)
        return ink

    def resolve(self, ref: TypeRef) -> TypeInk:
        return self.ink(ref.step, ref.emphasis)


def bind_ramp(
    *,
    overlay: OverlayData | None = None,
    root_body: Pt | None = None,
) -> TypeRamp:
    """Validate overlay, then ``EffectiveRamp`` at ``root_body``."""
    return EffectiveRamp(
        overlay=require_overlay(TypeOverlay() if overlay is None else overlay),
        root_body=ROOT_BODY if root_body is None else root_body,
    )


@dataclass(frozen=True, slots=True)
class ProofProfile:
    """Press-mode overlay for proofs / specimens (on-screen review).

    Selected by ``press(..., proof=True)`` or ``parch proof``. Composition is
    ``defaults ⊕ toml ⊕ proof``. ``display`` (cover year) is not patched.
    """

    overlay: TypeOverlay = field(
        default_factory=lambda: TypeOverlay(
            chrome=TypePatch(size=Pt(9.2)),
            title=TypePatch(size=Pt(13.0)),
            eyebrow=TypePatch(size=Pt(12.0)),
        )
    )


PROOF_PROFILE = ProofProfile()

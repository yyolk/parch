"""Two-phase type: painters pass ``TypeRef``; the bound ramp resolves ink.

Explicit object — no ambient container, no signature injection, no globals.
``TypeRef`` is a closed step or role literal plus optional emphasis and
optional size. It has no family and no weight. ``TypeInk`` is the resolved
cut (family + weight + size) and is produced once by ``TypeRamp.resolve``.

The plotter holds the ramp. ``Plotter.text(..., ref=)`` asks
``plotter.ramp.resolve(ref)``. Painters do not unpack ink into kwargs.

``family`` stays on the ink so a later dual-font ramp can pick another
catalog family without ripping out the plotter path. Today every ref
resolves to ``family="jost"``.
"""

from dataclasses import dataclass, field
from typing import Literal, Protocol

from parch.fonts.catalog import FontCatalog, TypeFamily, TypeWeight, jost_catalog

type TypeStep = Literal["display", "title", "eyebrow", "body", "chrome", "label", "caption"]
type TypeRole = Literal["cover_year", "cover_brow", "cover_specs", "page_title", "chrome"]
type TypeEmphasis = Literal["regular", "strong"]


@dataclass(frozen=True, slots=True)
class TypeRef:
    """Painter-facing type request. No family, no weight.

    ``step`` is a closed scale step or a cover/header role alias.
    ``emphasis`` is regular or strong. ``size`` overrides the step default.
    """

    step: TypeStep | TypeRole
    emphasis: TypeEmphasis = "regular"
    size: float | None = None


@dataclass(frozen=True, slots=True)
class TypeInk:
    """Resolved family / weight / size. Produced only by ``TypeRamp.resolve``."""

    family: TypeFamily
    weight: TypeWeight
    size: float


class TypeRamp(Protocol):
    catalog: FontCatalog

    def resolve(self, ref: TypeRef) -> TypeInk:
        """Resolve a painter ``TypeRef`` to plotter-ready ink."""
        ...


_ROLE_TO_STEP: dict[str, TypeStep] = {
    "cover_year": "display",
    "cover_brow": "eyebrow",
    "cover_specs": "body",
    "page_title": "title",
    "chrome": "chrome",
}

_STEPS: dict[TypeStep, tuple[TypeWeight, TypeWeight, float]] = {
    "display": ("heavy", "heavy", 42),
    "title": ("medium", "bold", 11),
    "eyebrow": ("medium", "bold", 10),
    "body": ("book", "bold", 8.2),
    "chrome": ("book", "bold", 7.4),
    "label": ("book", "bold", 6.4),
    "caption": ("book", "bold", 5.4),
}


@dataclass(frozen=True, slots=True)
class JostRamp:
    """Single-family Jost step/role map. Default — and currently only — ramp."""

    catalog: FontCatalog = field(default_factory=jost_catalog)

    def resolve(self, ref: TypeRef) -> TypeInk:
        if ref.step in _ROLE_TO_STEP:
            step = _ROLE_TO_STEP[ref.step]
        elif ref.step in _STEPS:
            step = ref.step
        else:
            raise KeyError(f"unknown type step/role {ref.step!r}")
        regular, strong, default_size = _STEPS[step]
        weight = strong if ref.emphasis == "strong" else regular
        size = default_size if ref.size is None else ref.size
        ink = TypeInk(family="jost", weight=weight, size=size)
        self.catalog.path(ink.family, ink.weight)
        return ink

    def ink(self, role: TypeRole) -> TypeInk:
        """Role convenience — same as ``resolve(TypeRef(step=role))``."""
        return self.resolve(TypeRef(step=role))

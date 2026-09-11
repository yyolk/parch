"""Step-based type: painters ask for steps; a ramp resolves plotter ink.

Explicit object — no ambient container, no signature injection, no globals.
``TypeInk`` carries family + weight + size. Painters call ``ramp.ink(step)``
and pass those fields through; they do not think in sans/serif slots or
hardcode pt on migrated sites.

Size is pure math: ``root_body * ratio``, except ``display`` (cover year)
which is a fixed-pt lockup. Weight comes from a closed step→weight table.
``family`` stays on the ink so a later dual-font ramp can pick another
catalog family without ripping out the plotter kwarg. Today every step
resolves to ``family="jost"``.
"""

from dataclasses import dataclass, field
from typing import Literal, Protocol

from parch.fonts.catalog import FontCatalog, TypeFamily, TypeWeight, jost_catalog

# Closed step set. Painters pick a step; they do not invent sizes.
type TypeStep = Literal[
    "display",  # cover year — FIXED pt, does not track root
    "title",  # page titles, week day numbers
    "brow",  # cover brow
    "body",  # calendar day numbers (month grid)
    "chrome",  # header meta, nav, schedule hours
    "caption",  # labels, weekday names, ticket numbers
    "cell",  # compact calendar cells, status, week numbers
    "micro",  # mini-month weekday initials
]

# Back-compat name — same closed set.
type TypeRole = TypeStep

# Nomad body. ``Device.root_body`` is the live source; this default matches it.
DEFAULT_ROOT_BODY = 8.5

# display / cover_year: lockup, not 5em (5 × 8.5 = 42.5). Stays 42pt when root moves.
DISPLAY_PT = 42.0

# Ratios in em of ``root_body``. ``display`` is absent — fixed exception.
STEP_RATIO: dict[TypeStep, float] = {
    "title": 1.3,
    "brow": 10 / DEFAULT_ROOT_BODY,  # 1.176… — keeps 10pt at Nomad root
    "body": 1.0,
    "chrome": 0.87,
    "caption": 0.75,
    "cell": 0.62,
    "micro": 0.51,
}

STEP_WEIGHT: dict[TypeStep, TypeWeight] = {
    "display": "heavy",
    "title": "medium",
    "brow": "medium",
    "body": "bold",
    "chrome": "book",
    "caption": "book",
    "cell": "book",
    "micro": "book",
}


@dataclass(frozen=True, slots=True)
class TypeInk:
    """Resolved family / weight / size for ``Plotter.text``."""

    family: TypeFamily
    weight: TypeWeight
    size: float


class TypeRamp(Protocol):
    catalog: FontCatalog

    def ink(self, step: TypeStep) -> TypeInk:
        """Resolve a closed type step to plotter-ready ink."""
        ...


@dataclass(frozen=True, slots=True)
class JostRamp:
    """Single-family Jost step ramp. Default — and currently only — ramp.

    ``root_body`` is the 1em size in pt. Pass ``Device.root_body`` at the
    press / layout boundary. Painters never see the number.
    """

    catalog: FontCatalog = field(default_factory=jost_catalog)
    root_body: float = DEFAULT_ROOT_BODY

    def ink(self, step: TypeStep) -> TypeInk:
        weight = STEP_WEIGHT[step]
        if step == "display":
            size = DISPLAY_PT
        else:
            size = self.root_body * STEP_RATIO[step]
        ink = TypeInk(family="jost", weight=weight, size=size)
        self.catalog.path(ink.family, ink.weight)
        return ink

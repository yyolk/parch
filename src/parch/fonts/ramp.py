"""Role-based type: painters ask for roles; a ramp resolves plotter ink.

Explicit object — no ambient container, no signature injection, no globals.
``TypeInk`` carries family + weight + size. Painters call ``ramp.ink(role)``
and pass the ink through; they do not think in sans/serif slots.

``family`` stays on the ink so a later dual-font ramp can pick another
catalog family without ripping out the plotter argument. Today every role
resolves to ``family="jost"``.
"""

from dataclasses import dataclass, field
from typing import Literal, Protocol

from parch.fonts.catalog import FontCatalog, TypeFamily, TypeWeight, jost_catalog

type TypeRole = Literal[
    "cover_year",
    "cover_brow",
    "page_title",
    "chrome",
    "cover_specs",
    "nav",
    "nav_on",
    "body",
    "emphasis",
    "mark",
]


@dataclass(frozen=True, slots=True)
class TypeInk:
    """Resolved family / weight / size for ``Plotter.text``."""

    family: TypeFamily
    weight: TypeWeight
    size: float

    def at(self, size: float) -> "TypeInk":
        """Same cut at a different point size."""
        if size == self.size:
            return self
        return TypeInk(family=self.family, weight=self.weight, size=size)


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
    "cover_specs": TypeInk(family="jost", weight="book", size=8.2),
    "nav": TypeInk(family="jost", weight="book", size=7.6),
    "nav_on": TypeInk(family="jost", weight="bold", size=7.6),
    "body": TypeInk(family="jost", weight="book", size=6.4),
    "emphasis": TypeInk(family="jost", weight="bold", size=8.5),
    "mark": TypeInk(family="jost", weight="medium", size=6.6),
}


@dataclass(frozen=True, slots=True)
class JostRamp:
    """Single-family Jost role map. Default — and currently only — ramp."""

    catalog: FontCatalog = field(default_factory=jost_catalog)

    def ink(self, role: TypeRole) -> TypeInk:
        ink = _JOST[role]
        self.catalog.path(ink.family, ink.weight)
        return ink

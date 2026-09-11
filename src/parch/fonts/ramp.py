"""Role-based type: painters ask for roles; a ramp resolves plotter ink.

Explicit object — no ambient container, no signature injection, no globals.
``TypeInk`` carries family + weight + size. Components declare the roles they
need (``typography()`` / ``TypoNeeds``). Painters ask, ``resolve`` via the
ramp, then draw — they do not hardcode role names in geometry code.

``family`` stays on the ink so a later dual-font ramp can pick another
catalog family without ripping out the plotter kwarg. Today every role
resolves to ``family="jost"``.
"""

from dataclasses import dataclass, field
from typing import Literal, Protocol

from parch.fonts.catalog import FontCatalog, TypeFamily, TypeWeight, jost_catalog

type TypeRole = Literal[
    "cover_year",
    "cover_brow",
    "cover_spec",
    "page_title",
    "chrome",
    "mini_month",
    "mini_month_on",
    "mini_dow",
    "mini_day",
    "mini_day_on",
    "month_dow",
    "month_week",
    "month_day",
    "week_dow",
    "week_day",
    "week_month",
    "well_label",
    "schedule_hour",
    "ticket_stub",
]


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
    "cover_spec": TypeInk(family="jost", weight="book", size=8.2),
    "page_title": TypeInk(family="jost", weight="medium", size=11),
    "chrome": TypeInk(family="jost", weight="book", size=7.4),
    "mini_month": TypeInk(family="jost", weight="book", size=6.4),
    "mini_month_on": TypeInk(family="jost", weight="bold", size=6.4),
    "mini_dow": TypeInk(family="jost", weight="book", size=4.3),
    "mini_day": TypeInk(family="jost", weight="book", size=5.3),
    "mini_day_on": TypeInk(family="jost", weight="bold", size=5.3),
    "month_dow": TypeInk(family="jost", weight="book", size=6.6),
    "month_week": TypeInk(family="jost", weight="book", size=5.8),
    "month_day": TypeInk(family="jost", weight="bold", size=8.5),
    "week_dow": TypeInk(family="jost", weight="book", size=6.6),
    "week_day": TypeInk(family="jost", weight="bold", size=11),
    "week_month": TypeInk(family="jost", weight="book", size=6.6),
    "well_label": TypeInk(family="jost", weight="book", size=6.4),
    "schedule_hour": TypeInk(family="jost", weight="book", size=7),
    "ticket_stub": TypeInk(family="jost", weight="medium", size=6.6),
}


@dataclass(frozen=True, slots=True)
class JostRamp:
    """Single-family Jost role map. Default — and currently only — ramp."""

    catalog: FontCatalog = field(default_factory=jost_catalog)

    def ink(self, role: TypeRole) -> TypeInk:
        ink = _JOST[role]
        self.catalog.path(ink.family, ink.weight)
        return ink

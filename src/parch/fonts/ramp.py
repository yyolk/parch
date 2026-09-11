"""Role-based type: painters ask for roles; a ramp resolves plotter ink.

Explicit object — no ambient container, no signature injection, no globals.
``TypeInk`` carries family + weight + size. Painters call ``ramp.ink(role)``
and pass those fields through; they do not think in sans/serif slots.

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
    "cover_specs",
    "page_title",
    "chrome",
    "nav_item",
    "nav_item_active",
    "label",
    "section_heading",
    "caption",
    "body",
    "weekday",
    "weekday_mini",
    "calendar_num",
    "day_num",
    "review_num",
    "calendar_num_mini",
    "calendar_num_mini_on",
    "chip_label",
    "index_mark",
    "habit_num",
    "habit_dow",
    "clone_mark",
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


# Closed Jost map. Sizes keep the audited MVP kind; near-duplicates share a role.
_JOST: dict[TypeRole, TypeInk] = {
    "cover_year": TypeInk(family="jost", weight="heavy", size=42),
    "cover_brow": TypeInk(family="jost", weight="medium", size=10),
    "cover_specs": TypeInk(family="jost", weight="book", size=8.2),
    "page_title": TypeInk(family="jost", weight="medium", size=11),
    "chrome": TypeInk(family="jost", weight="book", size=7.4),
    "nav_item": TypeInk(family="jost", weight="book", size=7.6),
    "nav_item_active": TypeInk(family="jost", weight="bold", size=7.6),
    "label": TypeInk(family="jost", weight="book", size=6.4),
    "section_heading": TypeInk(family="jost", weight="bold", size=6.4),
    "caption": TypeInk(family="jost", weight="book", size=5.8),
    "body": TypeInk(family="jost", weight="book", size=7.0),
    "weekday": TypeInk(family="jost", weight="book", size=6.6),
    "weekday_mini": TypeInk(family="jost", weight="book", size=4.3),
    "calendar_num": TypeInk(family="jost", weight="bold", size=8.5),
    "day_num": TypeInk(family="jost", weight="bold", size=11),
    "review_num": TypeInk(family="jost", weight="bold", size=9.2),
    "calendar_num_mini": TypeInk(family="jost", weight="book", size=5.3),
    "calendar_num_mini_on": TypeInk(family="jost", weight="bold", size=5.3),
    "chip_label": TypeInk(family="jost", weight="medium", size=7.0),
    "index_mark": TypeInk(family="jost", weight="medium", size=6.4),
    "habit_num": TypeInk(family="jost", weight="book", size=4.4),
    "habit_dow": TypeInk(family="jost", weight="book", size=4.4),
    "clone_mark": TypeInk(family="jost", weight="book", size=5.2),
}


@dataclass(frozen=True, slots=True)
class JostRamp:
    """Single-family Jost role map. Default — and currently only — ramp."""

    catalog: FontCatalog = field(default_factory=jost_catalog)

    def ink(self, role: TypeRole) -> TypeInk:
        ink = _JOST[role]
        self.catalog.path(ink.family, ink.weight)
        return ink

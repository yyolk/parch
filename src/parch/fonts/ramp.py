"""Role-based type: painters ask for roles; a ramp resolves plotter ink.

Explicit object — no ambient container, no signature injection, no globals.
``TypeInk`` carries family + weight + size. Painters call ``ramp.ink(role)``
and pass those fields through; they do not think in sans/serif slots.

``family`` stays on the ink so a later dual-font ramp can pick another
catalog family without ripping out the plotter kwarg. Today every role
resolves to ``family="jost"``.

Roles are the Thesis J freeze: RecordingPlotter over the MVP press,
clustered by (size, bold, face) plus sample strings. See ``AUDIT.md``.
Serif+bold call sites drew Jost Medium (``resolve_weight``); those roles
freeze as ``medium`` — what the book drew, not the painter's face flag.
"""

from dataclasses import dataclass, field
from typing import Literal, Protocol

from parch.fonts.catalog import FontCatalog, TypeFamily, TypeWeight, jost_catalog

# Frozen after the MVP text-op audit. Do not add speculative scale names.
type TypeRole = Literal[
    "cover_year",
    "cover_brow",
    "cover_spec",
    "page_title",
    "week_day",
    "review_day",
    "month_day",
    "nav",
    "nav_on",
    "chrome",
    "tasks_week",
    "hour",
    "review_week",
    "weekday",
    "project_stub",
    "label",
    "cal_month",
    "week_range",
    "index_month",
    "meeting_stub",
    "cue",
    "review_dow",
    "status",
    "cal_day",
    "cal_day_on",
    "priority_mark",
    "habit_day",
    "cal_dow",
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


# (role → ink) frozen from artifacts/mvp + AUDIT.md cluster table.
# size/weight are exact; names come from sample strings, not a type scale.
JOST_ROLES: dict[TypeRole, TypeInk] = {
    "cover_year": TypeInk(family="jost", weight="heavy", size=42),
    "cover_brow": TypeInk(family="jost", weight="medium", size=10),
    "cover_spec": TypeInk(family="jost", weight="book", size=8.2),
    "page_title": TypeInk(family="jost", weight="medium", size=11),
    "week_day": TypeInk(family="jost", weight="bold", size=11),
    "review_day": TypeInk(family="jost", weight="bold", size=9.2),
    "month_day": TypeInk(family="jost", weight="bold", size=8.5),
    "nav": TypeInk(family="jost", weight="book", size=7.6),
    "nav_on": TypeInk(family="jost", weight="bold", size=7.6),
    "chrome": TypeInk(family="jost", weight="book", size=7.4),
    "tasks_week": TypeInk(family="jost", weight="medium", size=7.2),
    "hour": TypeInk(family="jost", weight="book", size=7.0),
    "review_week": TypeInk(family="jost", weight="medium", size=7.0),
    "weekday": TypeInk(family="jost", weight="book", size=6.6),
    "project_stub": TypeInk(family="jost", weight="medium", size=6.6),
    "label": TypeInk(family="jost", weight="book", size=6.4),
    "cal_month": TypeInk(family="jost", weight="bold", size=6.4),
    "week_range": TypeInk(family="jost", weight="book", size=6.2),
    "index_month": TypeInk(family="jost", weight="bold", size=6.2),
    "meeting_stub": TypeInk(family="jost", weight="medium", size=6.2),
    "cue": TypeInk(family="jost", weight="book", size=5.8),
    "review_dow": TypeInk(family="jost", weight="book", size=5.6),
    "status": TypeInk(family="jost", weight="book", size=5.4),
    "cal_day": TypeInk(family="jost", weight="book", size=5.3),
    "cal_day_on": TypeInk(family="jost", weight="bold", size=5.3),
    "priority_mark": TypeInk(family="jost", weight="book", size=5.2),
    "habit_day": TypeInk(family="jost", weight="book", size=4.4),
    "cal_dow": TypeInk(family="jost", weight="book", size=4.3),
}


@dataclass(frozen=True, slots=True)
class JostRamp:
    """Single-family Jost role map. Default — and currently only — ramp."""

    catalog: FontCatalog = field(default_factory=jost_catalog)

    def ink(self, role: TypeRole) -> TypeInk:
        ink = JOST_ROLES[role]
        self.catalog.path(ink.family, ink.weight)
        return ink

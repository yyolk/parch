"""Role-based type: painters ask for roles; a ramp resolves plotter ink.

Explicit object — no ambient container, no signature injection, no globals.
``TypeInk`` carries family + weight + size. Migrated painters call
``ramp.ink(role)`` and pass those fields through.

Unlisted painters keep the face/bold vocabulary via ``ramp.faces``
(``FaceBridge``). That path is intentional and typed — the same ramp object,
a second method — not a hidden default. Today every role and every bridged
face still resolves to ``family="jost"``.

``MigratedSurface`` is the strangler allowlist: listed painter entrypoints
must emit family+weight (no face-only ``Plotter.text``). CI asserts that.
"""

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Literal, Protocol

from parch.fonts.catalog import FontCatalog, TypeFamily, TypeWeight, jost_catalog

type TypeRole = Literal[
    "cover_year",
    "cover_brow",
    "cover_specs",
    "page_title",
    "chrome",
    "label",
    "label_on",
    "quiet",
    "week_num",
    "micro",
    "grid",
    "grid_on",
    "day_num",
    "week_day",
    "hour",
    "ticket",
]

type TypeFace = Literal["sans", "serif"]


class MigratedSurface(StrEnum):
    """Painter entrypoints that must call ``ramp.ink`` — no face-only text."""

    COVER = "paint_cover"
    HEADER = "paint_header"
    YEAR = "paint_annual"
    MONTH = "paint_month_grid"
    WEEK = "paint_week"
    DAILY = "paint_daily"
    PROJECTS_INDEX = "paint_projects_index"


MIGRATED_SURFACES: frozenset[MigratedSurface] = frozenset(MigratedSurface)

# Habit / meeting / review / tasks stay on FaceBridge this spike.
BRIDGE_BACKLOG: frozenset[str] = frozenset(
    {
        "paint_habit_grid",
        "paint_meetings_index",
        "paint_meeting",
        "paint_review_index",
        "paint_review",
        "paint_tasks_index",
        "paint_task",
    }
)


@dataclass(frozen=True, slots=True)
class TypeInk:
    """Resolved family / weight / size for ``Plotter.text``."""

    family: TypeFamily
    weight: TypeWeight
    size: float


@dataclass(frozen=True, slots=True)
class FaceInk:
    """Legacy face+bold ink. Unmigrated painters only — still visible as face-only ops."""

    face: TypeFace
    bold: bool
    size: float


@dataclass(frozen=True, slots=True)
class FaceBridge:
    """Typed face+bold path on the ramp. Dual to ``TypeRamp.ink``, not ambient.

    Returns ``FaceInk`` so recordings stay face-only until a surface moves onto
    a role. Weight mapping (sans book/bold, serif medium) stays in the plotter.
    """

    def ink(self, face: TypeFace = "sans", *, bold: bool = False, size: float) -> FaceInk:
        return FaceInk(face=face, bold=bold, size=size)


class TypeRamp(Protocol):
    catalog: FontCatalog
    faces: FaceBridge

    def ink(self, role: TypeRole) -> TypeInk:
        """Resolve a closed type role to plotter-ready ink."""
        ...


_JOST: dict[TypeRole, TypeInk] = {
    "cover_year": TypeInk(family="jost", weight="heavy", size=42),
    "cover_brow": TypeInk(family="jost", weight="medium", size=10),
    "cover_specs": TypeInk(family="jost", weight="book", size=8.2),
    "page_title": TypeInk(family="jost", weight="medium", size=11),
    "chrome": TypeInk(family="jost", weight="book", size=7.4),
    "label": TypeInk(family="jost", weight="book", size=6.4),
    "label_on": TypeInk(family="jost", weight="bold", size=6.4),
    "quiet": TypeInk(family="jost", weight="book", size=6.6),
    "week_num": TypeInk(family="jost", weight="book", size=5.8),
    "micro": TypeInk(family="jost", weight="book", size=4.3),
    "grid": TypeInk(family="jost", weight="book", size=5.3),
    "grid_on": TypeInk(family="jost", weight="bold", size=5.3),
    "day_num": TypeInk(family="jost", weight="bold", size=8.5),
    "week_day": TypeInk(family="jost", weight="bold", size=11),
    "hour": TypeInk(family="jost", weight="book", size=7),
    "ticket": TypeInk(family="jost", weight="medium", size=6.6),
}


@dataclass(frozen=True, slots=True)
class JostRamp:
    """Single-family Jost role map. Default — and currently only — ramp."""

    catalog: FontCatalog = field(default_factory=jost_catalog)
    faces: FaceBridge = field(default_factory=FaceBridge)

    def ink(self, role: TypeRole) -> TypeInk:
        ink = _JOST[role]
        self.catalog.path(ink.family, ink.weight)
        return ink

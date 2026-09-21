"""Closed page-kind table. ``page_kind.py`` is generated from it."""

from dataclasses import dataclass
from typing import Literal, TypeIs

from parch.sections.page_kind import PageFace, PageKind, WellKind

type OutlinePolicy = Literal["run", "each", "skip"]


@dataclass(frozen=True, slots=True)
class PageKindSpec:
    """Id, nav chip, outline policy, and paint face for one page kind."""

    id: str
    strip: str
    outline: OutlinePolicy
    face: PageFace


PAGE_KIND_TABLE: tuple[PageKindSpec, ...] = (
    PageKindSpec("cover", "Year", "skip", "cover"),
    PageKindSpec("annual", "Year", "run", "well"),
    PageKindSpec("favorites", "Fav", "run", "well"),
    PageKindSpec("my_100", "100", "run", "well"),
    PageKindSpec("checkoff_365", "365", "run", "well"),
    PageKindSpec("projects_index", "Proj", "run", "well"),
    PageKindSpec("project", "Proj", "skip", "well"),
    PageKindSpec("meetings_index", "Meet", "run", "well"),
    PageKindSpec("meeting", "Meet", "skip", "well"),
    PageKindSpec("tasks_index", "Task", "run", "well"),
    PageKindSpec("task", "Task", "skip", "well"),
    PageKindSpec("review_index", "Rev", "run", "well"),
    PageKindSpec("review", "Rev", "skip", "well"),
    PageKindSpec("quarter", "Quar", "each", "well"),
    PageKindSpec("month", "Mon", "each", "well"),
    PageKindSpec("habits", "Habit", "skip", "well"),
    PageKindSpec("weekly", "Week", "skip", "well"),
    PageKindSpec("daily", "Day", "skip", "well"),
    PageKindSpec("daily_notes", "Notes", "skip", "well"),
    PageKindSpec("engineering_front", "", "skip", "engineering"),
    PageKindSpec("engineering_back", "", "skip", "engineering"),
    PageKindSpec("steno", "", "skip", "steno"),
    PageKindSpec("dotgrid", "", "skip", "dotgrid"),
    PageKindSpec("lined", "", "skip", "lined"),
    PageKindSpec("bujo_key", "Key", "run", "well"),
    PageKindSpec("bujo_index", "Idx", "run", "well"),
    PageKindSpec("future_log", "Fut", "run", "well"),
    PageKindSpec("monthly_log", "Mon", "each", "well"),
    PageKindSpec("monthly_tasks", "Mon", "skip", "well"),
    PageKindSpec("rapid_log", "Day", "skip", "well"),
    PageKindSpec("collection", "Col", "run", "well"),
)


def _by_id(rows: tuple[PageKindSpec, ...]) -> dict[str, PageKindSpec]:
    found: dict[str, PageKindSpec] = {}
    for row in rows:
        if row.id in found:
            raise ValueError(f"duplicate page kind {row.id!r}")
        found[row.id] = row
    return found


PAGE_KIND_BY_ID: dict[str, PageKindSpec] = _by_id(PAGE_KIND_TABLE)


def page_face(kind: PageKind) -> PageFace:
    """Paint-dispatch key recorded on the kind's table row."""
    return PAGE_KIND_BY_ID[kind].face


def is_well_kind(kind: PageKind) -> TypeIs[WellKind]:
    """True when this kind's paint face is the headered well."""
    return page_face(kind) == "well"


def outline_kinds(policy: OutlinePolicy) -> frozenset[str]:
    """Kind ids whose outline policy is ``policy``."""
    return frozenset(row.id for row in PAGE_KIND_TABLE if row.outline == policy)


def _literal_alias(name: str, values: tuple[str, ...]) -> str:
    inner = "\n".join(f'    "{value}",' for value in values)
    return f"type {name} = Literal[\n{inner}\n]"


def render_page_kind_module() -> str:
    """Render ``page_kind.py`` from ``PAGE_KIND_TABLE``."""
    ids = tuple(row.id for row in PAGE_KIND_TABLE)
    faces: list[str] = []
    for row in PAGE_KIND_TABLE:
        if row.face not in faces:
            faces.append(row.face)
    wells = tuple(row.id for row in PAGE_KIND_TABLE if row.face == "well")
    return "\n".join(
        (
            '"""Generated from PAGE_KIND_TABLE. Do not edit."""',
            "",
            "from typing import Literal",
            "",
            _literal_alias("PageKind", ids),
            "",
            _literal_alias("PageFace", tuple(faces)),
            "",
            _literal_alias("WellKind", wells),
            "",
        )
    )

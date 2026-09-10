"""Thesis O — named checklist index + one G-craft leaf per name. Not in YearPlanner."""

from parch.calendar import month_touching_weeks
from parch.components import (
    ProjectIndexItem,
    ProjectLeaf,
    ProjectsBoard,
    ProjectsIndexChecklist,
)
from parch.sections.nav import planner_nav
from parch.sections.page import Page
from parch.spec import Spec

# Printed names — the index is a book, not an empty form.
CHECKLIST_NAMES: tuple[str, ...] = (
    "Atlas",
    "Beacon",
    "Compass",
    "Harbor",
    "Kernel",
    "Ledger",
    "Meadow",
    "Mosaic",
    "Nomad",
    "Parch",
    "Spine",
    "Well",
)


def checklist_items(spec: Spec) -> tuple[ProjectIndexItem, ...]:
    """Named rows with dests and two-digit dest/page numbers."""
    names = CHECKLIST_NAMES[: spec.project_index_rows]
    return tuple(
        ProjectIndexItem(
            name=name,
            dest=spec.dest_for_project(number),
            page=f"{number:02d}",
        )
        for number, name in enumerate(names, start=1)
    )


class ProjectsIndexChecklistSection:
    """Index + leaf pages. Default stacked-card Projects board stays on the book."""

    def __init__(self, spec: Spec) -> None:
        self.spec = spec

    def pages(self) -> list[Page]:
        spec = self.spec
        first = month_touching_weeks(spec.year, spec.month, spec.weekday_start)[0]
        index_dest = spec.projects_index_checklist_dest
        nav = planner_nav(
            spec,
            week_dest=spec.dest_for_week(first[0]),
            proj_dest=index_dest,
        )
        items = checklist_items(spec)
        pages = [
            Page(
                dest=index_dest,
                kind="projects_index_checklist",
                title="Projects",
                nav=nav,
                components=(ProjectsIndexChecklist(year=spec.year, items=items),),
            )
        ]
        for item in items:
            pages.append(
                Page(
                    dest=item.dest,
                    kind="project",
                    title=item.name,
                    nav=nav,
                    components=(
                        ProjectLeaf(
                            year=spec.year,
                            name=item.name,
                            dest=item.dest,
                            index_dest=index_dest,
                            page=item.page,
                            tasks=spec.project_tasks,
                        ),
                        ProjectsBoard(
                            year=spec.year,
                            cards=1,
                            tasks=spec.project_tasks,
                        ),
                    ),
                )
            )
        return pages

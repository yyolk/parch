"""Thesis C — A–Z projects index + one page per entry. Not in YearPlanner."""

from parch.calendar import month_touching_weeks
from parch.components import ProjectIndexEntry, ProjectLeaf, ProjectsBoard, ProjectsIndexAlpha
from parch.sections.nav import planner_nav
from parch.sections.page import Page
from parch.spec import Spec

# Sample catalog so the index reads as a book, not an empty form.
# Letters without a pressed name are omitted (gazetteer style).
_ALPHA_NAMES: tuple[tuple[str, str], ...] = (
    ("Archive", "archive"),
    ("Atlas", "atlas"),
    ("Bridge", "bridge"),
    ("Beacon", "beacon"),
    ("Compass", "compass"),
    ("Critic", "critic"),
    ("Drift", "drift"),
    ("Focus", "focus"),
    ("Harbor", "harbor"),
    ("Hatch", "hatch"),
    ("Kernel", "kernel"),
    ("Ledger", "ledger"),
    ("Lantern", "lantern"),
    ("Meadow", "meadow"),
    ("Mosaic", "mosaic"),
    ("Nomad", "nomad"),
    ("Press", "press"),
    ("Parch", "parch"),
    ("Spine", "spine"),
    ("Specimen", "specimen"),
    ("Tracks", "tracks"),
    ("Tide", "tide"),
    ("Well", "well"),
)


def alpha_entries(spec: Spec) -> tuple[ProjectIndexEntry, ...]:
    """Named index rows with dests and two-digit page hints."""
    return tuple(
        ProjectIndexEntry(
            name=name,
            letter=name[0].upper(),
            dest=spec.dest_for_project(slug),
            hint=f"{index:02d}",
        )
        for index, (name, slug) in enumerate(_ALPHA_NAMES, start=1)
    )


class ProjectsIndexAlphaSection:
    """Index + leaf pages. Default stacked-card Projects board stays on the book."""

    def __init__(self, spec: Spec) -> None:
        self.spec = spec

    def pages(self) -> list[Page]:
        spec = self.spec
        first = month_touching_weeks(spec.year, spec.month, spec.weekday_start)[0]
        week_dest = spec.dest_for_week(first[0])
        index_dest = spec.projects_index_alpha_dest
        nav = planner_nav(spec, week_dest=week_dest, proj_dest=index_dest)
        entries = alpha_entries(spec)
        pages = [
            Page(
                dest=index_dest,
                kind="projects_index_alpha",
                title="Projects",
                nav=nav,
                components=(
                    ProjectsIndexAlpha(
                        year=spec.year,
                        index_dest=index_dest,
                        entries=entries,
                    ),
                ),
            )
        ]
        for entry in entries:
            pages.append(
                Page(
                    dest=entry.dest,
                    kind="project",
                    title=entry.name,
                    nav=nav,
                    components=(
                        ProjectLeaf(
                            year=spec.year,
                            name=entry.name,
                            dest=entry.dest,
                            index_dest=index_dest,
                            hint=entry.hint,
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

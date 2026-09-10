"""Thesis N — spine-cover Projects index + one G-craft leaf per spine. Not in YearPlanner."""

from parch.calendar import month_touching_weeks
from parch.components import ProjectLeaf, ProjectSpine, ProjectsBoard, ProjectsIndexSpines
from parch.sections.nav import planner_nav
from parch.sections.page import Page
from parch.spec import Spec

# Short stamped titles — stacked on a thin spine, not write-in underlines.
_SPINE_NAMES: tuple[tuple[str, str], ...] = (
    ("Atlas", "atlas"),
    ("Beacon", "beacon"),
    ("Drift", "drift"),
    ("Focus", "focus"),
    ("Harbor", "harbor"),
    ("Hatch", "hatch"),
    ("Ledger", "ledger"),
    ("Nomad", "nomad"),
    ("Parch", "parch"),
    ("Press", "press"),
    ("Spine", "spine"),
    ("Tide", "tide"),
)


def spine_catalog(spec: Spec) -> tuple[ProjectSpine, ...]:
    """Named spines with dests and two-digit leaf hints. Length follows the spec knob."""
    chosen = _SPINE_NAMES[: spec.project_index_spines]
    return tuple(
        ProjectSpine(
            name=name,
            dest=spec.dest_for_project(slug),
            hint=f"{index:02d}",
        )
        for index, (name, slug) in enumerate(chosen, start=1)
    )


class ProjectsIndexSpinesSection:
    """Index + leaf pages. Default stacked-card Projects board stays on the book."""

    def __init__(self, spec: Spec) -> None:
        self.spec = spec

    def pages(self) -> list[Page]:
        spec = self.spec
        first = month_touching_weeks(spec.year, spec.month, spec.weekday_start)[0]
        week_dest = spec.dest_for_week(first[0])
        index_dest = spec.projects_index_spines_dest
        nav = planner_nav(spec, week_dest=week_dest, proj_dest=index_dest)
        spines = spine_catalog(spec)
        pages = [
            Page(
                dest=index_dest,
                kind="projects_index_spines",
                title="Projects",
                nav=nav,
                components=(
                    ProjectsIndexSpines(
                        year=spec.year,
                        index_dest=index_dest,
                        spines=spines,
                    ),
                ),
            )
        ]
        for spine in spines:
            pages.append(
                Page(
                    dest=spine.dest,
                    kind="project",
                    title=spine.name,
                    nav=nav,
                    components=(
                        ProjectLeaf(
                            year=spec.year,
                            name=spine.name,
                            dest=spine.dest,
                            index_dest=index_dest,
                            hint=spine.hint,
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

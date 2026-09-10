from parch.calendar import month_touching_weeks
from parch.components.projects_index_bands import (
    ProjectIndexBand,
    ProjectIndexRow,
    ProjectLeaf,
    ProjectsIndexBands,
)
from parch.sections.nav import planner_nav
from parch.sections.page import NavItem, Page
from parch.spec import Spec

INDEX_BAND_LABELS = ("Active", "Waiting", "Done")
INDEX_ROWS = 4


def _proj_nav(spec: Spec) -> tuple[NavItem, ...]:
    first = month_touching_weeks(spec.year, spec.month, spec.weekday_start)[0]
    return planner_nav(spec, week_dest=spec.dest_for_week(first[0])) + (
        NavItem("Proj", spec.projects_index_bands_dest),
    )


class ProjectsIndexBandsSection:
    """Thesis D experiment — index + linked leaves. Not in the default YearPlanner walk."""

    def __init__(self, spec: Spec) -> None:
        self.spec = spec

    def pages(self) -> list[Page]:
        spec = self.spec
        rows_n = spec.project_index_rows
        bands: list[ProjectIndexBand] = []
        leaves: list[Page] = []
        n = 1
        nav = _proj_nav(spec)
        index_dest = spec.projects_index_bands_dest
        for label in INDEX_BAND_LABELS:
            rows: list[ProjectIndexRow] = []
            for _ in range(rows_n):
                dest = spec.dest_for_project(n)
                rows.append(ProjectIndexRow(dest=dest))
                leaves.append(
                    Page(
                        dest=dest,
                        kind="project",
                        title="Project",
                        nav=nav,
                        components=(
                            ProjectLeaf(
                                year=spec.year,
                                tasks=spec.project_tasks,
                                index_dest=index_dest,
                            ),
                        ),
                    )
                )
                n += 1
            bands.append(ProjectIndexBand(label=label, rows=tuple(rows)))
        index = Page(
            dest=index_dest,
            kind="projects_index_bands",
            title="Projects",
            nav=nav,
            components=(ProjectsIndexBands(year=spec.year, bands=tuple(bands)),),
        )
        return [index, *leaves]

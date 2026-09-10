from parch.calendar import month_touching_weeks
from parch.components import ProjectsIndexDetail
from parch.sections.nav import planner_nav
from parch.sections.page import Page
from parch.spec import Spec

INDEX_ROWS = 6


class ProjectsIndexDetailSection:
    """Thesis F experiment page — not in the default YearPlanner walk."""

    def __init__(self, spec: Spec) -> None:
        self.spec = spec

    def pages(self) -> list[Page]:
        spec = self.spec
        first = month_touching_weeks(spec.year, spec.month, spec.weekday_start)[0]
        return [
            Page(
                dest=spec.projects_index_detail_dest,
                kind="projects_index_detail",
                title="Projects",
                nav=planner_nav(spec, week_dest=spec.dest_for_week(first[0])),
                components=(
                    ProjectsIndexDetail(
                        year=spec.year,
                        index_rows=INDEX_ROWS,
                        tasks=spec.project_tasks,
                    ),
                ),
            )
        ]

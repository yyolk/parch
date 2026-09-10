from parch.calendar import month_touching_weeks
from parch.components import ProjectsMatrix
from parch.sections.nav import planner_nav
from parch.sections.page import Page
from parch.spec import Spec

MATRIX_ROWS = 5
MATRIX_CRITERIA = 5


class ProjectsMatrixSection:
    """Thesis J experiment page — not in the default YearPlanner walk."""

    def __init__(self, spec: Spec) -> None:
        self.spec = spec

    def pages(self) -> list[Page]:
        spec = self.spec
        first = month_touching_weeks(spec.year, spec.month, spec.weekday_start)[0]
        return [
            Page(
                dest=spec.projects_matrix_dest,
                kind="projects_matrix",
                title="Projects",
                nav=planner_nav(spec, week_dest=spec.dest_for_week(first[0])),
                components=(
                    ProjectsMatrix(
                        year=spec.year,
                        rows=MATRIX_ROWS,
                        criteria=MATRIX_CRITERIA,
                    ),
                ),
            )
        ]

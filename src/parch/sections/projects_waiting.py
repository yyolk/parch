from parch.calendar import month_touching_weeks
from parch.components import ProjectsWaiting
from parch.sections.nav import planner_nav
from parch.sections.page import Page
from parch.spec import Spec


class ProjectsWaitingSection:
    """Thesis P experiment page — not in the default YearPlanner walk."""

    def __init__(self, spec: Spec) -> None:
        self.spec = spec

    def pages(self) -> list[Page]:
        spec = self.spec
        first = month_touching_weeks(spec.year, spec.month, spec.weekday_start)[0]
        return [
            Page(
                dest=spec.projects_waiting_dest,
                kind="projects_waiting",
                title="Projects",
                nav=planner_nav(spec, week_dest=spec.dest_for_week(first[0])),
                components=(
                    ProjectsWaiting(
                        year=spec.year,
                        rows=spec.project_waiting_rows,
                    ),
                ),
            )
        ]

from parch.calendar import month_touching_weeks
from parch.components import ProjectsLog
from parch.sections.nav import planner_nav
from parch.sections.page import Page
from parch.spec import Spec


class ProjectsLogSection:
    """Thesis N experiment page — not in the default YearPlanner walk."""

    def __init__(self, spec: Spec) -> None:
        self.spec = spec

    def pages(self) -> list[Page]:
        spec = self.spec
        first = month_touching_weeks(spec.year, spec.month, spec.weekday_start)[0]
        return [
            Page(
                dest=spec.projects_log_dest,
                kind="projects_log",
                title="Projects",
                nav=planner_nav(spec, week_dest=spec.dest_for_week(first[0])),
                components=(
                    ProjectsLog(
                        year=spec.year,
                        entries=spec.project_log_entries,
                    ),
                ),
            )
        ]

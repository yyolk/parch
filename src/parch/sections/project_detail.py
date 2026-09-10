from parch.calendar import month_touching_weeks
from parch.components import ProjectDetail
from parch.sections.nav import planner_nav
from parch.sections.page import Page
from parch.spec import Spec


class ProjectDetailSection:
    """Exploratory one-project deep page. Does not replace the 3-card board."""

    def __init__(self, spec: Spec) -> None:
        self.spec = spec

    def pages(self) -> list[Page]:
        spec = self.spec
        first = month_touching_weeks(spec.year, spec.month, spec.weekday_start)[0]
        return [
            Page(
                dest=spec.project_detail_dest,
                kind="project_detail",
                title="Project",
                nav=planner_nav(spec, week_dest=spec.dest_for_week(first[0])),
                components=(
                    ProjectDetail(year=spec.year, tasks=spec.project_detail_tasks),
                ),
            )
        ]

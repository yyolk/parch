from parch.calendar import month_touching_weeks
from parch.components import ProjectsHorizon
from parch.sections.nav import planner_nav
from parch.sections.page import Page
from parch.spec import Spec

HORIZON_SLOTS = 2
HORIZON_TICKS = 2


class ProjectsHorizonSection:
    """Thesis I experiment page — not in the default YearPlanner walk."""

    def __init__(self, spec: Spec) -> None:
        self.spec = spec

    def pages(self) -> list[Page]:
        spec = self.spec
        first = month_touching_weeks(spec.year, spec.month, spec.weekday_start)[0]
        return [
            Page(
                dest=spec.projects_horizon_dest,
                kind="projects_horizon",
                title="Projects",
                nav=planner_nav(spec, week_dest=spec.dest_for_week(first[0])),
                components=(
                    ProjectsHorizon(
                        year=spec.year,
                        slots=HORIZON_SLOTS,
                        ticks=HORIZON_TICKS,
                    ),
                ),
            )
        ]

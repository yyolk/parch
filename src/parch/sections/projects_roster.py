"""Thesis B — dense project roster. Parallel experiment; not in the default book."""

from parch.calendar import month_touching_weeks
from parch.components import ROSTER_ROWS, ProjectsRoster
from parch.sections.nav import planner_nav
from parch.sections.page import Page
from parch.spec import Spec


class ProjectsRosterSection:
    def __init__(self, spec: Spec) -> None:
        self.spec = spec

    def pages(self) -> list[Page]:
        spec = self.spec
        first = month_touching_weeks(spec.year, spec.month, spec.weekday_start)[0]
        return [
            Page(
                dest=spec.projects_roster_dest,
                kind="projects_roster",
                title="Projects",
                nav=planner_nav(spec, week_dest=spec.dest_for_week(first[0])),
                components=(ProjectsRoster(year=spec.year, rows=ROSTER_ROWS),),
            )
        ]

from parch.calendar import month_touching_weeks
from parch.components import ProjectsColumns
from parch.sections.nav import planner_nav
from parch.sections.page import Page
from parch.spec import Spec


class ProjectsBoardSection:
    """Throwaway Thesis A page — not the locked stacked-card Projects section."""

    def __init__(self, spec: Spec) -> None:
        self.spec = spec

    def pages(self) -> list[Page]:
        spec = self.spec
        first = month_touching_weeks(spec.year, spec.month, spec.weekday_start)[0]
        return [
            Page(
                dest=spec.projects_board_dest,
                kind="projects_board",
                title="Projects",
                nav=planner_nav(spec, week_dest=spec.dest_for_week(first[0])),
                components=(
                    ProjectsColumns(
                        year=spec.year,
                        cards=spec.board_cards,
                        ticks=spec.board_ticks,
                    ),
                ),
            )
        ]

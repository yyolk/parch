from parch.calendar import month_touching_weeks
from parch.components import ProjectTicket, ProjectsBoard, ProjectsIndex
from parch.sections.nav import planner_nav
from parch.sections.page import Page
from parch.spec import Spec


class ProjectsSection:
    def __init__(self, spec: Spec) -> None:
        self.spec = spec

    def pages(self) -> list[Page]:
        spec = self.spec
        first = month_touching_weeks(spec.year, spec.month, spec.weekday_start)[0]
        nav = planner_nav(spec, week_dest=spec.dest_for_week(first[0]))
        tickets = tuple(
            ProjectTicket(number=slot, dest=spec.dest_for_project(slot))
            for slot in range(1, spec.project_tickets + 1)
        )
        built = [
            Page(
                dest=spec.projects_dest,
                kind="projects",
                title="Projects",
                nav=nav,
                components=(
                    ProjectsBoard(
                        year=spec.year,
                        cards=spec.project_cards,
                        tasks=spec.project_tasks,
                    ),
                ),
            ),
            Page(
                dest=spec.projects_index_dest,
                kind="projects_index",
                title="Projects",
                nav=nav,
                components=(
                    ProjectsIndex(
                        year=spec.year,
                        dest=spec.projects_index_dest,
                        tickets=tickets,
                    ),
                ),
            ),
        ]
        built.extend(
            Page(
                dest=ticket.dest,
                kind="project",
                title="Projects",
                nav=nav,
                components=(
                    ProjectsBoard(
                        year=spec.year,
                        cards=spec.project_cards,
                        tasks=spec.project_tasks,
                        index_dest=spec.projects_index_dest,
                    ),
                ),
            )
            for ticket in tickets
        )
        return built

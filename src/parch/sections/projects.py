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
        week_dest = spec.dest_for_week(first[0])
        nav = planner_nav(spec, week_dest=week_dest)
        tickets = tuple(
            ProjectTicket(number=slot, dest=spec.dest_for_project(slot))
            for slot in range(1, spec.project_count + 1)
        )
        per = spec.project_tickets
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
            )
        ]
        for page_i in range(1, spec.project_index_pages + 1):
            start = (page_i - 1) * per
            slice_tickets = tickets[start : start + per]
            dest = spec.dest_for_projects_index(page_i)
            built.append(
                Page(
                    dest=dest,
                    kind="projects_index",
                    title="Projects",
                    nav=nav,
                    components=(
                        ProjectsIndex(
                            year=spec.year,
                            dest=dest,
                            tickets=slice_tickets,
                        ),
                    ),
                )
            )
        built.extend(
            Page(
                dest=ticket.dest,
                kind="project",
                title="Projects",
                nav=planner_nav(
                    spec,
                    week_dest=week_dest,
                    proj_dest=spec.dest_for_projects_index_of(ticket.number),
                ),
                components=(
                    ProjectsBoard(
                        year=spec.year,
                        cards=spec.project_cards,
                        tasks=spec.project_tasks,
                        index_dest=spec.dest_for_projects_index_of(ticket.number),
                        number=ticket.number,
                    ),
                ),
            )
            for ticket in tickets
        )
        return built

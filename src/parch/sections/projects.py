from parch.calendar import month_touching_weeks
from parch.components import ProjectsBoard, ProjectsIndex, ProjectTicket
from parch.sections.nav import planner_nav
from parch.sections.page import NavItem, Page
from parch.spec import Spec


class ProjectsSection:
    def __init__(self, spec: Spec, *, nav: tuple[NavItem, ...] | None = None) -> None:
        self.spec = spec
        self._nav = nav

    def pages(self) -> list[Page]:
        spec = self.spec
        first = month_touching_weeks(spec.year, spec.month, spec.weekday_start)[0]
        week_dest = spec.dest_for_week(first[0])
        nav = (
            self._nav
            if self._nav is not None
            else planner_nav(spec, week_dest=week_dest)
        )
        tickets = tuple(
            ProjectTicket(number=slot, dest=spec.dest_for_project(slot))
            for slot in range(1, spec.project_count + 1)
        )
        per = spec.project_tickets
        built: list[Page] = []
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
                nav=self._leaf_nav(spec, week_dest, ticket.number),
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

    def _leaf_nav(self, spec: Spec, week_dest: str, number: int) -> tuple[NavItem, ...]:
        proj_dest = spec.dest_for_projects_index_of(number)
        if self._nav is None:
            return planner_nav(spec, week_dest=week_dest, proj_dest=proj_dest)
        return tuple(
            NavItem(item.label, proj_dest if item.label == "Proj" else item.dest)
            for item in self._nav
        )

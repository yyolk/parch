from parch.calendar import month_touching_weeks
from parch.components import ProjectSheet, ProjectsIndex
from parch.sections.nav import planner_nav
from parch.sections.page import Page
from parch.spec import Spec


class ProjectsIndexSection:
    """2×2 cover index plus one G-craft sheet per slot. PROJ lands on the index."""

    def __init__(self, spec: Spec) -> None:
        self.spec = spec

    def pages(self) -> list[Page]:
        spec = self.spec
        first = month_touching_weeks(spec.year, spec.month, spec.weekday_start)[0]
        nav = planner_nav(spec, week_dest=spec.dest_for_week(first[0]))
        dests = tuple(spec.dest_for_project(n) for n in range(1, spec.project_index_slots + 1))
        titles = spec.project_titles
        built = [
            Page(
                dest=spec.projects_index_dest,
                kind="projects_index",
                title="Projects",
                nav=nav,
                components=(ProjectsIndex(year=spec.year, dests=dests, titles=titles),),
            )
        ]
        for number, dest, title in zip(range(1, len(dests) + 1), dests, titles, strict=True):
            built.append(
                Page(
                    dest=dest,
                    kind="project",
                    title="Project",
                    nav=nav,
                    components=(
                        ProjectSheet(
                            year=spec.year,
                            number=number,
                            title=title,
                            tasks=spec.project_tasks,
                            index_dest=spec.projects_index_dest,
                        ),
                    ),
                )
            )
        return built

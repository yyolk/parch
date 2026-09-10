from parch.calendar import month_touching_weeks
from parch.components import ProjectLeaf, ProjectsIndex
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
        dests = tuple(spec.dest_for_project(n) for n in range(1, spec.project_index_rows + 1))
        built = [
            Page(
                dest=spec.projects_dest,
                kind="projects",
                title="Projects",
                nav=nav,
                components=(ProjectsIndex(year=spec.year, dests=dests),),
            )
        ]
        for number, dest in enumerate(dests, start=1):
            built.append(
                Page(
                    dest=dest,
                    kind="project",
                    title=f"Project {number:02d}",
                    nav=nav,
                    components=(
                        ProjectLeaf(
                            year=spec.year,
                            number=number,
                            tasks=spec.project_tasks,
                            dest=dest,
                            index_dest=spec.projects_dest,
                        ),
                    ),
                )
            )
        return built

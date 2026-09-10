from parch.calendar import month_touching_weeks
from parch.components import ProjectLeaf, ProjectNode, ProjectsBoard, ProjectsIndex
from parch.components.projects import timeline_months
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
        nodes = tuple(
            ProjectNode(when=when, dest=spec.dest_for_project(number))
            for number, when in enumerate(timeline_months(spec.project_index_rows), start=1)
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
                components=(ProjectsIndex(year=spec.year, nodes=nodes),),
            ),
        ]
        for number, node in enumerate(nodes, start=1):
            built.append(
                Page(
                    dest=node.dest,
                    kind="project",
                    title=f"Project {number:02d}",
                    nav=nav,
                    components=(
                        ProjectLeaf(
                            year=spec.year,
                            number=number,
                            tasks=spec.project_tasks,
                            index_dest=spec.projects_index_dest,
                        ),
                    ),
                )
            )
        return built

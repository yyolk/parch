from parch.calendar import month_touching_weeks
from parch.components import ProjectLeaf, ProjectsBoard, ProjectsIndex
from parch.components.projects import project_roster
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
        rows = project_roster(spec.project_index_rows, spec.dest_for_project)
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
                components=(ProjectsIndex(year=spec.year, rows=rows),),
            ),
        ]
        for number, entry in enumerate(rows, start=1):
            built.append(
                Page(
                    dest=entry.dest,
                    kind="project",
                    title=entry.title,
                    nav=nav,
                    components=(
                        ProjectLeaf(
                            year=spec.year,
                            number=number,
                            title=entry.title,
                            glyph=entry.glyph,
                            status=entry.status,
                            tasks=spec.project_tasks,
                            index_dest=spec.projects_index_dest,
                        ),
                    ),
                )
            )
        return built

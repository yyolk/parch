from parch.calendar import month_touching_weeks
from parch.components import ProjectPage, ProjectsBoard, ProjectsIndex
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
        featured = spec.dest_for_project(1)
        entries = tuple(
            spec.dest_for_project(slot) for slot in range(2, spec.project_page_count + 1)
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
                        featured=featured,
                        entries=entries,
                    ),
                ),
            ),
        ]
        built.extend(
            Page(
                dest=spec.dest_for_project(slot),
                kind="project",
                title="Project",
                nav=nav,
                components=(
                    ProjectPage(
                        year=spec.year,
                        slot=slot,
                        dest=spec.dest_for_project(slot),
                        index_dest=spec.projects_index_dest,
                        tasks=spec.project_tasks,
                    ),
                ),
            )
            for slot in range(1, spec.project_page_count + 1)
        )
        return built

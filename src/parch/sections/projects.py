from parch.calendar import month_touching_weeks
from parch.components import ProjectEntry, ProjectLeaf, ProjectsIndex
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
        entries = tuple(
            ProjectEntry(dest=spec.dest_for_project(index), number=f"{index:02d}")
            for index in range(1, spec.project_slots + 1)
        )
        built = [
            Page(
                dest=spec.projects_dest,
                kind="projects",
                title="Projects",
                nav=nav,
                components=(ProjectsIndex(year=spec.year, entries=entries),),
            )
        ]
        for entry in entries:
            built.append(
                Page(
                    dest=entry.dest,
                    kind="project",
                    title="Project",
                    nav=nav,
                    components=(
                        ProjectLeaf(
                            year=spec.year,
                            dest=entry.dest,
                            number=entry.number,
                            tasks=spec.project_tasks,
                        ),
                    ),
                )
            )
        return built

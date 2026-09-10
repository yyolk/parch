from parch.calendar import month_touching_weeks
from parch.components import ProjectEntry, ProjectLeaf, ProjectsIndex, sample_projects
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
        catalog = sample_projects(spec.project_index_rows)
        entries = tuple(
            ProjectEntry(name=name, status=status, dest=spec.dest_for_project(number))
            for number, (name, status) in enumerate(catalog, start=1)
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
        for number, entry in enumerate(entries, start=1):
            built.append(
                Page(
                    dest=entry.dest,
                    kind="project",
                    title=entry.name,
                    nav=nav,
                    components=(
                        ProjectLeaf(
                            year=spec.year,
                            number=number,
                            name=entry.name,
                            status=entry.status,
                            tasks=spec.project_tasks,
                            index_dest=spec.projects_dest,
                        ),
                    ),
                )
            )
        return built

from parch.calendar import month_touching_weeks
from parch.components import TaskCover, TasksIndex, WeeklyTasks
from parch.sections.nav import planner_nav
from parch.sections.page import Page
from parch.spec import Spec

TASK_ROWS = 7


class TasksSection:
    """Thesis D — week-thumbnail cover grid plus locked weekly Tasks dests."""

    def __init__(self, spec: Spec) -> None:
        self.spec = spec

    def pages(self) -> list[Page]:
        spec = self.spec
        first = month_touching_weeks(spec.year, spec.month, spec.weekday_start)[0]
        week_dest = spec.dest_for_week(first[0])
        nav = planner_nav(spec, week_dest=week_dest)
        covers = tuple(
            TaskCover(number=slot, dest=spec.dest_for_tasks(slot))
            for slot in range(1, spec.task_count + 1)
        )
        per = spec.task_covers
        built: list[Page] = []
        for page_i in range(1, spec.task_index_pages + 1):
            start = (page_i - 1) * per
            slice_covers = covers[start : start + per]
            dest = spec.dest_for_tasks_index(page_i)
            built.append(
                Page(
                    dest=dest,
                    kind="tasks_index",
                    title="Tasks",
                    nav=nav,
                    components=(
                        TasksIndex(
                            year=spec.year,
                            dest=dest,
                            covers=slice_covers,
                        ),
                    ),
                )
            )
        built.extend(
            Page(
                dest=cover.dest,
                kind="weekly_tasks",
                title="Tasks",
                nav=planner_nav(
                    spec,
                    week_dest=week_dest,
                    task_dest=spec.dest_for_tasks_index_of(cover.number),
                ),
                components=(
                    WeeklyTasks(
                        year=spec.year,
                        rows=TASK_ROWS,
                        index_dest=spec.dest_for_tasks_index_of(cover.number),
                        number=cover.number,
                    ),
                ),
            )
            for cover in covers
        )
        return built

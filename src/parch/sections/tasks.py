from datetime import timedelta

from parch.calendar import month_touching_weeks
from parch.components import TaskWeek, TasksIndex, WeekTasks
from parch.sections.nav import planner_nav
from parch.sections.page import Page
from parch.spec import Spec


class TasksSection:
    """Exploratory Tasks index A + weekly dests. Index rows open weekly Tasks pages."""

    def __init__(self, spec: Spec) -> None:
        self.spec = spec

    def pages(self) -> list[Page]:
        spec = self.spec
        first = month_touching_weeks(spec.year, spec.month, spec.weekday_start)[0]
        week_dest = spec.dest_for_week(first[0])
        nav = planner_nav(spec, week_dest=week_dest)
        weeks = tuple(
            TaskWeek(
                iso_year=monday.isocalendar().year,
                iso_week=monday.isocalendar().week,
                monday=monday,
                sunday=monday + timedelta(days=6),
                dest=spec.dest_for_task_week(monday),
            )
            for monday in spec.task_week_mondays()
        )
        per = spec.task_index_rows
        built: list[Page] = []
        for page_i in range(1, spec.task_index_pages + 1):
            start = (page_i - 1) * per
            slice_weeks = weeks[start : start + per]
            dest = spec.dest_for_tasks_index(page_i)
            built.append(
                Page(
                    dest=dest,
                    kind="tasks_index",
                    title="Tasks",
                    nav=nav,
                    components=(TasksIndex(year=spec.year, dest=dest, weeks=slice_weeks),),
                )
            )
        for week in weeks:
            built.append(
                Page(
                    dest=week.dest,
                    kind="task",
                    title="Tasks",
                    nav=planner_nav(
                        spec,
                        week_dest=week_dest,
                        task_dest=spec.dest_for_tasks_index_of(week.monday),
                    ),
                    components=(
                        WeekTasks(
                            year=week.iso_year,
                            iso_week=week.iso_week,
                            monday=week.monday,
                            sunday=week.sunday,
                            tasks=spec.task_rows,
                            index_dest=spec.dest_for_tasks_index_of(week.monday),
                        ),
                    ),
                )
            )
        return built

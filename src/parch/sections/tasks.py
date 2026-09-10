from datetime import date, timedelta

from parch.calendar import iso_monday, month_touching_weeks
from parch.components import TasksIndex, TaskWeek, WeeklyTasks
from parch.sections.nav import planner_nav
from parch.sections.page import Page
from parch.spec import Spec


def planner_task_weeks(spec: Spec) -> list[list[date]]:
    """First ``task_count`` ISO weeks from the first pressed touching week."""
    first = month_touching_weeks(spec.year, spec.month, spec.weekday_start)[0]
    monday = iso_monday(first[0])
    return [
        [monday + timedelta(days=7 * i + offset) for offset in range(7)]
        for i in range(spec.task_count)
    ]


def _slot(spec: Spec, week: list[date]) -> TaskWeek:
    monday = iso_monday(week[0])
    iso = monday.isocalendar()
    return TaskWeek(
        iso_year=iso.year,
        iso_week=iso.week,
        monday=monday,
        sunday=monday + timedelta(days=6),
        dest=spec.dest_for_tasks(monday),
    )


class TasksSection:
    """Thesis E Tasks index plus weekly checklist dests."""

    def __init__(self, spec: Spec) -> None:
        self.spec = spec

    def pages(self) -> list[Page]:
        spec = self.spec
        weeks = planner_task_weeks(spec)
        first = month_touching_weeks(spec.year, spec.month, spec.weekday_start)[0]
        week_dest = spec.dest_for_week(first[0])
        nav = planner_nav(spec, week_dest=week_dest)
        featured = _slot(spec, weeks[0])
        entries = tuple(_slot(spec, week) for week in weeks[1:])
        built = [
            Page(
                dest=spec.tasks_index_dest,
                kind="tasks_index",
                title="Tasks",
                nav=nav,
                components=(
                    TasksIndex(
                        year=spec.year,
                        dest=spec.tasks_index_dest,
                        featured=featured,
                        entries=entries,
                        preview=spec.task_preview,
                    ),
                ),
            )
        ]
        built.extend(
            Page(
                dest=slot.dest,
                kind="task",
                title="Tasks",
                nav=planner_nav(
                    spec,
                    week_dest=week_dest,
                    task_dest=spec.tasks_index_dest,
                ),
                components=(
                    WeeklyTasks(
                        year=spec.year,
                        iso_week=slot.iso_week,
                        monday=slot.monday,
                        sunday=slot.sunday,
                        tasks=spec.task_checklist,
                        dest=slot.dest,
                        index_dest=spec.tasks_index_dest,
                    ),
                ),
            )
            for slot in (featured, *entries)
        )
        return built

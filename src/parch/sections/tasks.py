from datetime import date, timedelta

from parch.calendar import months_touching_weeks
from parch.components import TasksIndex, TaskWeek, WeeklyTasks
from parch.sections.nav import planner_nav
from parch.sections.page import Page
from parch.spec import Spec

TASK_MORNING = 6
TASK_LATER = 6


class TasksSection:
    """Exploratory Tasks index F + weekly dests. Week chips open Morning|Later pages."""

    def __init__(self, spec: Spec) -> None:
        self.spec = spec

    def pages(self) -> list[Page]:
        spec = self.spec
        weeks = months_touching_weeks(spec.year, spec.months, spec.weekday_start)
        first = weeks[0]
        week_dest = spec.dest_for_week(first[0])
        nav = planner_nav(spec, week_dest=week_dest)
        chips = tuple(_chip(spec, week) for week in weeks)
        built = [
            Page(
                dest=spec.tasks_index_dest,
                kind="tasks_index",
                title="Tasks",
                nav=nav,
                components=(
                    TasksIndex(year=spec.year, dest=spec.tasks_index_dest, weeks=chips),
                ),
            )
        ]
        for chip in chips:
            built.append(
                Page(
                    dest=chip.dest,
                    kind="tasks",
                    title="Tasks",
                    nav=planner_nav(
                        spec,
                        week_dest=spec.dest_for_week(chip.monday),
                        day=chip.monday if spec.presses_day(chip.monday) else _landing(spec, chip),
                        task_dest=spec.tasks_index_dest,
                    ),
                    components=(
                        WeeklyTasks(
                            year=chip.iso_year,
                            iso_week=chip.iso_week,
                            monday=chip.monday,
                            sunday=chip.sunday,
                            morning=TASK_MORNING,
                            later=TASK_LATER,
                            index_dest=spec.tasks_index_dest,
                            number=chip.iso_week,
                        ),
                    ),
                )
            )
        return built


def _chip(spec: Spec, week: list[date]) -> TaskWeek:
    monday = week[0]
    sunday = monday + timedelta(days=6)
    iso = monday.isocalendar()
    return TaskWeek(
        iso_year=iso.year,
        iso_week=iso.week,
        monday=monday,
        sunday=sunday,
        dest=spec.dest_for_tasks(monday),
    )


def _landing(spec: Spec, chip: TaskWeek) -> date:
    for offset in range(7):
        day = chip.monday + timedelta(days=offset)
        if spec.presses_day(day):
            return day
    return spec.date

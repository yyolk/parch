from datetime import date, timedelta

from parch.calendar import MONTH_NAMES, iso_monday, month_week_bands, quarter_of
from parch.components import TaskWeek, TasksIndex, TasksMonthBand, TasksWeekPage
from parch.sections.nav import planner_nav
from parch.sections.page import Page
from parch.spec import Spec


class TasksSection:
    """Tasks index C + weekly dests. Month bands; after Meetings in YearPlanner."""

    def __init__(self, spec: Spec) -> None:
        self.spec = spec

    def pages(self) -> list[Page]:
        spec = self.spec
        built: list[Page] = []
        by_quarter: dict[int, list[TasksMonthBand]] = {}
        for band in self._bands(spec.months):
            by_quarter.setdefault(quarter_of(band.month), []).append(band)
        for quarter in spec.pressed_quarters():
            bands = tuple(by_quarter.get(quarter, ()))
            if not bands:
                continue
            first_week = bands[0].weeks[0]
            landing = self._landing(first_week.monday)
            index_dest = spec.dest_for_tasks_index(quarter)
            built.append(
                Page(
                    dest=index_dest,
                    kind="tasks_index",
                    title="Tasks",
                    nav=planner_nav(
                        spec,
                        week_dest=spec.dest_for_week(first_week.monday),
                        day=landing,
                        month=landing.month,
                        task_dest=index_dest,
                    ),
                    components=(
                        TasksIndex(
                            year=spec.year,
                            dest=index_dest,
                            quarter=quarter,
                            bands=bands,
                        ),
                    ),
                )
            )
            for band in bands:
                for week in band.weeks:
                    built.append(self._dest_page(week, index_dest))
        return built

    def _bands(self, months: tuple[int, ...]) -> tuple[TasksMonthBand, ...]:
        spec = self.spec
        bands: list[TasksMonthBand] = []
        for month, weeks in month_week_bands(spec.year, months, spec.weekday_start):
            rows = tuple(self._task_week(week) for week in weeks)
            bands.append(
                TasksMonthBand(month=month, name=MONTH_NAMES[month - 1], weeks=rows)
            )
        return tuple(bands)

    def _task_week(self, week: list[date]) -> TaskWeek:
        spec = self.spec
        monday = next((day for day in week if day.weekday() == 0), iso_monday(week[0]))
        iso = monday.isocalendar()
        return TaskWeek(
            iso_year=iso.year,
            iso_week=iso.week,
            monday=monday,
            sunday=monday + timedelta(days=6),
            dest=spec.dest_for_task(monday),
        )

    def _dest_page(self, week: TaskWeek, index_dest: str) -> Page:
        spec = self.spec
        landing = self._landing(week.monday)
        return Page(
            dest=week.dest,
            kind="task",
            title="Tasks",
            nav=planner_nav(
                spec,
                week_dest=spec.dest_for_week(week.monday),
                day=landing,
                month=landing.month,
                task_dest=index_dest,
            ),
            components=(
                TasksWeekPage(
                    year=spec.year,
                    iso_year=week.iso_year,
                    iso_week=week.iso_week,
                    monday=week.monday,
                    sunday=week.sunday,
                    rows=spec.task_rows,
                    index_dest=index_dest,
                ),
            ),
        )

    def _landing(self, monday: date) -> date:
        spec = self.spec
        week = [monday + timedelta(days=offset) for offset in range(7)]
        pressed = [day for day in week if spec.presses_day(day)]
        return pressed[0] if pressed else monday

import calendar
from datetime import date

from parch.calendar import month_name, month_touching_weeks
from parch.components import HabitGrid
from parch.sections.nav import planner_nav
from parch.sections.page import Page
from parch.spec import Spec


class HabitSection:
    def __init__(self, spec: Spec) -> None:
        self.spec = spec

    def pages(self) -> list[Page]:
        built: list[Page] = []
        for month in self.spec.months:
            built.extend(self.pages_for(month))
        return built

    def pages_for(self, month: int) -> list[Page]:
        spec = self.spec
        days = calendar.monthrange(spec.year, month)[1]
        first = month_touching_weeks(spec.year, month, spec.weekday_start)[0]
        dests = tuple(
            spec.dest_for_day(date(spec.year, month, day)) for day in range(1, days + 1)
        )
        return [
            Page(
                dest=spec.dest_for_habits(month),
                kind="habits",
                title=f"Habits · {month_name(month)} {spec.year}",
                nav=planner_nav(spec, week_dest=spec.dest_for_week(first[0]), month=month),
                components=(
                    HabitGrid(
                        year=spec.year,
                        month=month,
                        month_name=month_name(month),
                        days=days,
                        rows=spec.habit_columns,
                        month_dest=spec.dest_for_month(month),
                        day_dests=dests,
                        quarter_dest=spec.dest_for_quarter_of(month),
                    ),
                ),
            )
        ]

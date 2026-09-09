from parch.calendar import month_name, month_touching_weeks, month_weeks, weekday_labels
from parch.components import AnnualGrid, AnnualMonth, MonthCell
from parch.sections.nav import planner_nav
from parch.sections.page import Page
from parch.spec import Spec


def build_annual_month(spec: Spec, month: int) -> AnnualMonth:
    pressed = spec.presses(month)
    labels = weekday_labels(spec.weekday_start)
    weeks = []
    for week in month_weeks(spec.year, month, spec.weekday_start):
        cells = []
        for day in week:
            if day is None:
                cells.append(MonthCell(day=None))
            elif pressed:
                cells.append(MonthCell(day=day.day, dest=spec.dest_for_day(day)))
            else:
                cells.append(MonthCell(day=day.day, dest=None))
        weeks.append(tuple(cells))
    return AnnualMonth(
        month=month,
        name=month_name(month),
        dest=spec.dest_for_month(month) if pressed else None,
        weekday_labels=labels,
        weeks=tuple(weeks),
    )


class AnnualSection:
    def __init__(self, spec: Spec) -> None:
        self.spec = spec

    def pages(self) -> list[Page]:
        spec = self.spec
        months = tuple(build_annual_month(spec, month) for month in range(1, 13))
        first = month_touching_weeks(spec.year, spec.month, spec.weekday_start)[0]
        return [
            Page(
                dest=spec.year_dest,
                kind="annual",
                title=str(spec.year),
                nav=planner_nav(spec, week_dest=spec.dest_for_week(first[0])),
                components=(
                    AnnualGrid(
                        year=spec.year,
                        months=months,
                        quarter_dest=spec.quarter_dest,
                    ),
                ),
            )
        ]

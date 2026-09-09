from parch.calendar import iso_monday, month_name, month_touching_weeks, weekday_labels
from parch.components import MonthCell, MonthGrid
from parch.sections.nav import planner_nav
from parch.sections.page import Page
from parch.spec import Spec


class MonthSection:
    def __init__(self, spec: Spec) -> None:
        self.spec = spec

    def pages(self) -> list[Page]:
        built: list[Page] = []
        for month in self.spec.months:
            built.extend(self.pages_for(month))
        return built

    def pages_for(self, month: int) -> list[Page]:
        spec = self.spec
        weeks = []
        week_dests: list[str] = []
        for week in month_touching_weeks(spec.year, month, spec.weekday_start):
            cells = []
            for day in week:
                if day.month != month:
                    cells.append(MonthCell(day=None))
                else:
                    cells.append(MonthCell(day=day.day, dest=spec.dest_for_day(day)))
            weeks.append(tuple(cells))
            monday = next((d for d in week if d.weekday() == 0), iso_monday(week[0]))
            week_dests.append(spec.dest_for_week(monday))
        return [
            Page(
                dest=spec.dest_for_month(month),
                kind="month",
                title=f"{month_name(month)} {spec.year}",
                nav=planner_nav(spec, week_dest=week_dests[0], month=month),
                components=(
                    MonthGrid(
                        year=spec.year,
                        month=month,
                        month_name=month_name(month),
                        weekday_labels=weekday_labels(spec.weekday_start),
                        weeks=tuple(weeks),
                        week_dests=tuple(week_dests),
                        quarter_dest=spec.dest_for_quarter_of(month),
                    ),
                ),
            )
        ]

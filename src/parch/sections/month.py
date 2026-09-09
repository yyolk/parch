from parch.calendar import iso_monday, month_name, month_touching_weeks, weekday_labels
from parch.components import MonthCell, MonthGrid
from parch.sections.nav import planner_nav
from parch.sections.page import Page
from parch.spec import Spec


class MonthSection:
    def __init__(self, spec: Spec) -> None:
        self.spec = spec

    def pages(self) -> list[Page]:
        spec = self.spec
        weeks = []
        week_dests: list[str] = []
        for week in month_touching_weeks(spec.year, spec.month, spec.weekday_start):
            cells = []
            for day in week:
                if day.month != spec.month:
                    cells.append(MonthCell(day=None))
                else:
                    cells.append(MonthCell(day=day.day, dest=spec.dest_for_day(day)))
            weeks.append(tuple(cells))
            monday = next((d for d in week if d.weekday() == 0), iso_monday(week[0]))
            week_dests.append(spec.dest_for_week(monday))
        # WEEK nav on the month page: first ISO week that touches the month.
        return [
            Page(
                dest=spec.month_dest,
                kind="month",
                title=f"{month_name(spec.month)} {spec.year}",
                nav=planner_nav(spec, week_dest=week_dests[0]),
                components=(
                    MonthGrid(
                        year=spec.year,
                        month=spec.month,
                        month_name=month_name(spec.month),
                        weekday_labels=weekday_labels(spec.weekday_start),
                        weeks=tuple(weeks),
                        week_dests=tuple(week_dests),
                    ),
                ),
            )
        ]

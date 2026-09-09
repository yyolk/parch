from datetime import date, timedelta

from parch.calendar import WEEKDAY_LABELS, iso_monday
from parch.components import WeekDay, WeekStrip
from parch.sections.nav import planner_nav
from parch.sections.page import Page
from parch.spec import Spec


class WeeklySection:
    def __init__(self, spec: Spec) -> None:
        self.spec = spec

    def pages_for(self, week: list[date]) -> list[Page]:
        spec = self.spec
        monday = next((d for d in week if d.weekday() == 0), iso_monday(week[0]))
        sunday = monday + timedelta(days=6)
        iso = monday.isocalendar()
        in_month = [d for d in week if d.month == spec.month]
        landing = in_month[0]
        days = tuple(
            WeekDay(
                day=day,
                weekday_label=WEEKDAY_LABELS[day.weekday()],
                dest=spec.dest_for_day(day) if day.month == spec.month else None,
                in_month=day.month == spec.month,
            )
            for day in week
        )
        dest = spec.dest_for_week(monday)
        return [
            Page(
                dest=dest,
                kind="weekly",
                title=f"Week {iso.week:02d}",
                nav=planner_nav(spec, week_dest=dest, day=landing),
                components=(
                    WeekStrip(
                        iso_year=iso.year,
                        iso_week=iso.week,
                        monday=monday,
                        sunday=sunday,
                        days=days,
                    ),
                ),
            )
        ]

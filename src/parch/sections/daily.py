from datetime import date

from parch.calendar import WEEKDAY_FULL
from parch.components import Notes, Schedule
from parch.sections.annual import build_month_mini
from parch.sections.nav import planner_nav
from parch.sections.page import Page
from parch.spec import Spec


class DailySection:
    def __init__(self, spec: Spec) -> None:
        self.spec = spec

    def pages_for(self, day: date) -> list[Page]:
        spec = self.spec
        weekday = WEEKDAY_FULL[day.weekday()]
        hours = tuple(range(spec.schedule_from, spec.schedule_to + 1))
        return [
            Page(
                dest=spec.dest_for_day(day),
                kind="daily",
                title=f"{weekday[:3]} {day.day}",
                nav=planner_nav(
                    spec, week_dest=spec.dest_for_week(day), day=day, month=day.month
                ),
                components=(
                    Schedule(label="Schedule", hours=hours),
                    Notes(label="Notes"),
                    build_month_mini(spec, day),
                ),
            )
        ]

from datetime import date

from parch.calendar import WEEKDAY_FULL
from parch.components import Notes, Priorities, Schedule
from parch.sections.annual import build_month_mini
from parch.sections.nav import planner_nav
from parch.sections.page import Page
from parch.spec import Spec


class DailySection:
    """Daily well. ``Schedule`` leads so layout can tell this from notes-only pages."""

    def __init__(self, spec: Spec) -> None:
        self.spec = spec

    def pages_for(self, day: date) -> list[Page]:
        spec = self.spec
        weekday = WEEKDAY_FULL[day.weekday()]
        hours = spec.schedule_hours
        return [
            Page(
                dest=spec.dest_for_day(day),
                kind="daily",
                title=f"{weekday[:3]} {day.day}",
                nav=planner_nav(
                    spec, week_dest=spec.dest_for_week(day), day=day, month=day.month
                ),
                components=(
                    Schedule(
                        label="Schedule",
                        hours=hours,
                        work_hours=spec.work_hours,
                    ),
                    Notes(label="Notes"),
                    Priorities(label="Priorities", rows=spec.priority_rows),
                    build_month_mini(spec, day),
                ),
            )
        ]

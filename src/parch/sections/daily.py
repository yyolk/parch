from datetime import date

from parch.calendar import WEEKDAY_FULL, month_name
from parch.components import Notes, Schedule
from parch.sections.page import NavItem, Page
from parch.spec import Spec


class DailySection:
    def __init__(self, spec: Spec) -> None:
        self.spec = spec

    def pages_for(self, day: date) -> list[Page]:
        spec = self.spec
        weekday = WEEKDAY_FULL[day.weekday()]
        hours = tuple(range(spec.schedule_from, spec.schedule_to + 1))
        nav = [
            NavItem("Cover", spec.cover_dest),
            NavItem(month_name(spec.month)[:3], spec.month_dest),
        ]
        if spec.notes_pages > 0:
            nav.append(NavItem("Notes", spec.dest_for_notes(day, 1)))
        return [
            Page(
                dest=spec.dest_for_day(day),
                kind="daily",
                title=f"{weekday[:3]} {day.day}",
                nav=tuple(nav),
                components=(
                    Schedule(label="Schedule", hours=hours),
                    Notes(label="Notes"),
                ),
            )
        ]

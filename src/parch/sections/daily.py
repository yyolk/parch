from parch.calendar import WEEKDAY_FULL, month_name
from parch.components import Notes, Schedule
from parch.sections.page import NavItem, Page
from parch.spec import Spec


class DailySection:
    def __init__(self, spec: Spec) -> None:
        self.spec = spec

    def pages(self) -> list[Page]:
        spec = self.spec
        day = spec.date
        weekday = WEEKDAY_FULL[day.weekday()]
        hours = tuple(range(spec.schedule_from, spec.schedule_to + 1))
        return [
            Page(
                dest=spec.day_dest,
                kind="daily",
                title=f"{weekday[:3]} {day.day}",
                nav=(
                    NavItem("Cover", spec.cover_dest),
                    NavItem(month_name(spec.month)[:3], spec.month_dest),
                ),
                components=(
                    Schedule(label="Schedule", hours=hours),
                    Notes(label="Notes"),
                ),
            )
        ]

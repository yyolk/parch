"""Daily notes wells after a daily page — not a second daily layout."""

from parch.calendar import WEEKDAY_FULL, month_name
from parch.components import Notes
from parch.sections.page import NavItem, Page
from parch.spec import Spec


class DailyNotesSection:
    def __init__(self, spec: Spec) -> None:
        self.spec = spec

    def pages(self) -> list[Page]:
        spec = self.spec
        if spec.notes_pages < 1:
            return []
        day = spec.date
        weekday = WEEKDAY_FULL[day.weekday()][:3]
        month = month_name(spec.month)[:3]
        built: list[Page] = []
        for index in range(1, spec.notes_pages + 1):
            built.append(
                Page(
                    dest=spec.notes_dest(index),
                    kind="daily_notes",
                    title=f"{weekday} {day.day}  {index}/{spec.notes_pages}",
                    nav=(
                        NavItem("Cover", spec.cover_dest),
                        NavItem(month, spec.month_dest),
                        NavItem(str(day.day), spec.day_dest),
                    ),
                    components=(
                        Notes(label=f"Notes {index}/{spec.notes_pages}"),
                    ),
                )
            )
        return built

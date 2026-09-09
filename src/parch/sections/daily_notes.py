"""Daily notes wells after a daily page — not a second daily layout."""

from datetime import date

from parch.calendar import WEEKDAY_FULL
from parch.components import Notes
from parch.sections.nav import planner_nav
from parch.sections.page import Page
from parch.spec import Spec


class DailyNotesSection:
    def __init__(self, spec: Spec) -> None:
        self.spec = spec

    def pages_for(self, day: date) -> list[Page]:
        spec = self.spec
        if spec.notes_pages < 1:
            return []
        weekday = WEEKDAY_FULL[day.weekday()][:3]
        built: list[Page] = []
        for index in range(1, spec.notes_pages + 1):
            built.append(
                Page(
                    dest=spec.dest_for_notes(day, index),
                    kind="daily_notes",
                    title=f"{weekday} {day.day}  {index}/{spec.notes_pages}",
                    nav=planner_nav(
                        spec, week_dest=spec.dest_for_week(day), day=day, month=day.month
                    ),
                    components=(
                        Notes(label=f"Notes {index}/{spec.notes_pages}"),
                    ),
                )
            )
        return built

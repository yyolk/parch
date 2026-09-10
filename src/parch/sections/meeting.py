from parch.calendar import month_touching_weeks
from parch.components import MeetingAgenda
from parch.sections.nav import planner_nav
from parch.sections.page import Page
from parch.spec import Spec

MEET_AGENDA = 4
MEET_ACTION_ITEMS = 3


class MeetingSection:
    """Exploratory Meeting page — not in the default YearPlanner walk."""

    def __init__(self, spec: Spec) -> None:
        self.spec = spec

    def pages(self) -> list[Page]:
        spec = self.spec
        first = month_touching_weeks(spec.year, spec.month, spec.weekday_start)[0]
        return [
            Page(
                dest=spec.meeting_dest,
                kind="meeting",
                title="Meeting",
                nav=planner_nav(spec, week_dest=spec.dest_for_week(first[0])),
                components=(
                    MeetingAgenda(
                        year=spec.year,
                        agenda=MEET_AGENDA,
                        action_items=MEET_ACTION_ITEMS,
                    ),
                ),
            )
        ]

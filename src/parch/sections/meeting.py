from parch.calendar import month_touching_weeks
from parch.components import MeetingAgenda, MeetingIndex, MeetingSlot
from parch.sections.nav import planner_nav
from parch.sections.page import Page
from parch.spec import Spec

MEET_AGENDA = 4
MEET_ACTION_ITEMS = 3


class MeetingSection:
    """Thesis E meetings index plus locked dest pages."""

    def __init__(self, spec: Spec) -> None:
        self.spec = spec

    def pages(self) -> list[Page]:
        spec = self.spec
        first = month_touching_weeks(spec.year, spec.month, spec.weekday_start)[0]
        nav = planner_nav(spec, week_dest=spec.dest_for_week(first[0]))
        featured = MeetingSlot(number=1, dest=spec.dest_for_meeting(1))
        entries = tuple(
            MeetingSlot(number=slot, dest=spec.dest_for_meeting(slot))
            for slot in range(2, spec.meeting_count + 1)
        )
        built = [
            Page(
                dest=spec.meetings_index_dest,
                kind="meetings_index",
                title="Meetings",
                nav=nav,
                components=(
                    MeetingIndex(
                        year=spec.year,
                        dest=spec.meetings_index_dest,
                        featured=featured,
                        entries=entries,
                    ),
                ),
            )
        ]
        built.extend(
            Page(
                dest=slot.dest,
                kind="meeting",
                title="Meeting",
                nav=nav,
                components=(
                    MeetingAgenda(
                        year=spec.year,
                        agenda=MEET_AGENDA,
                        action_items=MEET_ACTION_ITEMS,
                        dest=slot.dest,
                        index_dest=spec.meetings_index_dest,
                        number=slot.number,
                    ),
                ),
            )
            for slot in (featured, *entries)
        )
        return built

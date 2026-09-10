from parch.calendar import month_touching_weeks
from parch.components import MeetingAgenda, MeetingIndex, MeetingSlot
from parch.sections.nav import planner_nav
from parch.sections.page import Page
from parch.spec import Spec

MEET_AGENDA = 4
MEET_ACTION_ITEMS = 3


class MeetingSection:
    """Exploratory Meeting index A + locked dests. Index rows open Meeting pages."""

    def __init__(self, spec: Spec) -> None:
        self.spec = spec

    def pages(self) -> list[Page]:
        spec = self.spec
        first = month_touching_weeks(spec.year, spec.month, spec.weekday_start)[0]
        week_dest = spec.dest_for_week(first[0])
        nav = planner_nav(spec, week_dest=week_dest)
        slots = tuple(
            MeetingSlot(number=slot, dest=spec.dest_for_meeting(slot))
            for slot in range(1, spec.meeting_count + 1)
        )
        built = [
            Page(
                dest=spec.meetings_index_dest,
                kind="meetings_index",
                title="Meetings",
                nav=nav,
                components=(
                    MeetingIndex(year=spec.year, dest=spec.meetings_index_dest, slots=slots),
                ),
            )
        ]
        for slot in slots:
            built.append(
                Page(
                    dest=slot.dest,
                    kind="meeting",
                    title="Meeting",
                    nav=planner_nav(
                        spec,
                        week_dest=week_dest,
                        meet_dest=spec.dest_for_meetings_index_of(slot.number),
                    ),
                    components=(
                        MeetingAgenda(
                            year=spec.year,
                            agenda=MEET_AGENDA,
                            action_items=MEET_ACTION_ITEMS,
                            index_dest=spec.dest_for_meetings_index_of(slot.number),
                            number=slot.number,
                        ),
                    ),
                )
            )
        return built

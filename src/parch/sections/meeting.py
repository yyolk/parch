from parch.calendar import month_touching_weeks
from parch.components import MeetingAgenda, MeetingTicket, MeetingsIndex
from parch.sections.nav import planner_nav
from parch.sections.page import Page
from parch.spec import Spec

MEET_AGENDA = 4
MEET_ACTION_ITEMS = 3


class MeetingSection:
    """Thesis B — ticket-stack Meeting index plus locked dest pages."""

    def __init__(self, spec: Spec) -> None:
        self.spec = spec

    def pages(self) -> list[Page]:
        spec = self.spec
        first = month_touching_weeks(spec.year, spec.month, spec.weekday_start)[0]
        week_dest = spec.dest_for_week(first[0])
        nav = planner_nav(spec, week_dest=week_dest)
        tickets = tuple(
            MeetingTicket(number=slot, dest=spec.dest_for_meeting(slot))
            for slot in range(1, spec.meeting_count + 1)
        )
        per = spec.meeting_tickets
        built: list[Page] = []
        for page_i in range(1, spec.meeting_index_pages + 1):
            start = (page_i - 1) * per
            slice_tickets = tickets[start : start + per]
            dest = spec.dest_for_meetings_index(page_i)
            built.append(
                Page(
                    dest=dest,
                    kind="meetings_index",
                    title="Meeting",
                    nav=nav,
                    components=(
                        MeetingsIndex(
                            year=spec.year,
                            dest=dest,
                            tickets=slice_tickets,
                        ),
                    ),
                )
            )
        built.extend(
            Page(
                dest=ticket.dest,
                kind="meeting",
                title="Meeting",
                nav=planner_nav(
                    spec,
                    week_dest=week_dest,
                    meet_dest=spec.dest_for_meetings_index_of(ticket.number),
                ),
                components=(
                    MeetingAgenda(
                        year=spec.year,
                        agenda=MEET_AGENDA,
                        action_items=MEET_ACTION_ITEMS,
                        index_dest=spec.dest_for_meetings_index_of(ticket.number),
                        number=ticket.number,
                    ),
                ),
            )
            for ticket in tickets
        )
        return built

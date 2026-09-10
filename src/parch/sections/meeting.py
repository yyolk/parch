from parch.calendar import month_touching_weeks
from parch.components import MeetingAgenda, MeetingIndex, MeetingIndexBand, MeetingIndexRow
from parch.sections.nav import planner_nav
from parch.sections.page import Page
from parch.spec import Spec

MEET_AGENDA = 4
MEET_ACTION_ITEMS = 3
MEET_INDEX_BAND_LABELS = ("This week", "Next week", "Later")
MEET_INDEX_DATED = (True, True, False)
MEET_INDEX_ROWS = 4


class MeetingSection:
    """Thesis C — week-banded index + locked dests. Not in the default YearPlanner walk."""

    def __init__(self, spec: Spec) -> None:
        self.spec = spec

    def pages(self) -> list[Page]:
        spec = self.spec
        first = month_touching_weeks(spec.year, spec.month, spec.weekday_start)[0]
        index_dest = spec.meetings_index_dest
        nav = planner_nav(
            spec,
            week_dest=spec.dest_for_week(first[0]),
            meet_dest=index_dest,
        )
        bands: list[MeetingIndexBand] = []
        dests: list[Page] = []
        n = 1
        rows_n = spec.meeting_index_rows
        for label, dated in zip(MEET_INDEX_BAND_LABELS, MEET_INDEX_DATED, strict=True):
            rows: list[MeetingIndexRow] = []
            for _ in range(rows_n):
                dest = spec.dest_for_meeting(n)
                rows.append(MeetingIndexRow(dest=dest))
                dests.append(
                    Page(
                        dest=dest,
                        kind="meeting",
                        title="Meeting",
                        nav=nav,
                        components=(
                            MeetingAgenda(
                                year=spec.year,
                                agenda=MEET_AGENDA,
                                action_items=MEET_ACTION_ITEMS,
                                index_dest=index_dest,
                                number=n,
                            ),
                        ),
                    )
                )
                n += 1
            bands.append(MeetingIndexBand(label=label, rows=tuple(rows), dated=dated))
        index = Page(
            dest=index_dest,
            kind="meetings_index",
            title="Meetings",
            nav=nav,
            components=(
                MeetingIndex(year=spec.year, dest=index_dest, bands=tuple(bands)),
            ),
        )
        return [index, *dests]

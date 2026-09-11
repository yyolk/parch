"""Thesis D — each section paints from its frozen StylePack, not a role enum."""

from dataclasses import FrozenInstanceError, replace
from datetime import date

import pytest

from parch.books import YearPlanner
from parch.components import (
    AnnualGrid,
    CoverTitle,
    HabitGrid,
    MeetingAgenda,
    MeetingIndex,
    MonthGrid,
    Notes,
    Priorities,
    ProjectsBoard,
    ProjectsIndex,
    ReviewIndex,
    ReviewWeekPage,
    Schedule,
    TasksIndex,
    TasksWeekPage,
    WeekStrip,
)
from parch.devices.nomad import NOMAD
from parch.fonts import JostRamp, TypeInk, default_packs, jost_catalog
from parch.fonts.packs import (
    AnnualPack,
    BaseChrome,
    CoverPack,
    DailyPack,
    HabitPack,
    MeetingPack,
    MiniMonthPack,
    MonthPack,
    NavPack,
    PlannerPacks,
    ProjectsPack,
    ReviewPack,
    TasksPack,
    WeekPack,
)
from parch.layouts.planner import PlannerLayout
from parch.layouts.planner.layout import well_rect
from parch.layouts.planner.painters import (
    paint_annual,
    paint_cover,
    paint_habit_grid,
    paint_header,
    paint_meeting,
    paint_meetings_index,
    paint_month_grid,
    paint_nav,
    paint_notes,
    paint_priorities,
    paint_project,
    paint_projects_index,
    paint_review,
    paint_review_index,
    paint_schedule,
    paint_task,
    paint_tasks_index,
    paint_week,
)
from parch.plotter import RecordingPlotter
from parch.sections.page import Page
from parch.spec import Spec


def _ink(weight: str, size: float) -> TypeInk:
    return TypeInk(family="jost", weight=weight, size=size)  # type: ignore[arg-type]


def _chrome(title: float = 3, meta: float = 4) -> BaseChrome:
    return BaseChrome(
        title=_ink("bold", title),
        meta=_ink("book", meta),
        nav=NavPack(idle=_ink("book", 5), active=_ink("heavy", 6)),
    )


def _mini(*, month: float = 21, day: float = 22) -> MiniMonthPack:
    return MiniMonthPack(
        month=_ink("book", month),
        month_on=_ink("bold", month),
        weekday=_ink("book", 4),
        day=_ink("book", day),
        day_on=_ink("bold", day),
        day_mark=_ink("bold", day),
    )


def _family(op: tuple[object, ...]) -> object:
    return op[10]


def _texts(plotter: RecordingPlotter) -> list[tuple[object, ...]]:
    return [op for op in plotter.ops if op[0] == "text"]


def _one(kind: str, typ: type):
    page = next(p for p in YearPlanner().pages(Spec(notes_pages=1)) if p.kind == kind)
    for item in page.components:
        if isinstance(item, typ):
            return item
    raise TypeError(kind)


def test_planner_packs_are_frozen_jost_only():
    packs = JostRamp().packs()
    assert isinstance(packs, PlannerPacks)
    with pytest.raises(FrozenInstanceError):
        packs.cover.year = _ink("book", 1)  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        packs.month.day = _ink("book", 1)  # type: ignore[misc]
    inks: list[TypeInk] = [
        packs.cover.year,
        packs.cover.brow,
        packs.cover.specs,
        packs.annual.chrome.title,
        packs.annual.chrome.meta,
        packs.annual.chrome.nav.idle,
        packs.annual.chrome.nav.active,
        packs.annual.mini.month,
        packs.month.day,
        packs.week.day,
        packs.daily.label,
        packs.projects.stub,
        packs.tasks.week,
        packs.review.chip,
        packs.habit.day,
        packs.meeting.stub,
        packs.quarter.label,
    ]
    assert {ink.family for ink in inks} == {"jost"}
    for ink in inks:
        jost_catalog().path(ink.family, ink.weight)
    assert packs.cover.year == TypeInk(family="jost", weight="heavy", size=42)
    assert packs.annual.chrome.title == TypeInk(family="jost", weight="medium", size=11)
    assert packs.annual.chrome is packs.month.chrome
    assert default_packs().cover == packs.cover


def test_cover_painter_uses_cover_pack_not_roles():
    pack = CoverPack(year=_ink("book", 19), brow=_ink("bold", 8), specs=_ink("medium", 7))
    plotter = RecordingPlotter()
    paint_cover(
        plotter,
        NOMAD,
        CoverTitle(year=2026, subtitle="", device_name="nomad", cta_label="", cta_dest="year-2026"),
        pack=pack,
    )
    year = next(op for op in _texts(plotter) if op[2] == "2026")
    assert year[3] == 19
    assert year[9] == "book"
    assert _family(year) == "jost"
    assert year[5] is False
    brow = next(op for op in _texts(plotter) if op[2] == "Year Book")
    assert brow[3] == 8
    assert brow[9] == "bold"
    specs = next(op for op in _texts(plotter) if "monday weeks" in str(op[2]))
    assert specs[3] == 7
    assert specs[9] == "medium"
    assert _family(specs) == "jost"


def test_annual_painter_uses_annual_pack():
    pack = AnnualPack(chrome=_chrome(), mini=_mini(month=31, day=32))
    plotter = RecordingPlotter()
    paint_annual(plotter, well_rect(NOMAD), _one("annual", AnnualGrid), pack=pack)
    jan = next(op for op in _texts(plotter) if op[2] == "Jan")
    assert jan[3] == 31
    assert jan[9] == "bold"
    assert _family(jan) == "jost"
    day = next(op for op in _texts(plotter) if op[2] == "1")
    assert day[3] == 32


def test_month_painter_uses_month_pack():
    pack = MonthPack(chrome=_chrome(), weekday=_ink("book", 14), week=_ink("medium", 13), day=_ink("heavy", 18))
    plotter = RecordingPlotter()
    paint_month_grid(plotter, well_rect(NOMAD), _one("month", MonthGrid), pack=pack)
    mon = next(op for op in _texts(plotter) if op[2] == "M")
    assert mon[3] == 14
    assert _family(mon) == "jost"
    week = next(op for op in _texts(plotter) if op[2] == "W01")
    assert week[3] == 13
    day = next(op for op in _texts(plotter) if op[2] == "1")
    assert day[3] == 18
    assert day[9] == "heavy"


def test_week_painter_uses_week_pack():
    pack = WeekPack(chrome=_chrome(), weekday=_ink("book", 15), day=_ink("heavy", 20), month=_ink("medium", 16))
    plotter = RecordingPlotter()
    paint_week(plotter, well_rect(NOMAD), _one("weekly", WeekStrip), pack=pack)
    dow = next(op for op in _texts(plotter) if op[2] == "Mon")
    assert dow[3] == 15
    num = next(op for op in _texts(plotter) if op[2] == "29")
    assert num[3] == 20
    assert num[9] == "heavy"
    dec = next(op for op in _texts(plotter) if op[2] == "Dec")
    assert dec[3] == 16


def test_daily_painters_use_daily_pack():
    pack = DailyPack(chrome=_chrome(), label=_ink("bold", 17), hour=_ink("medium", 12), mini=_mini())
    well = well_rect(NOMAD)
    sched = RecordingPlotter()
    paint_schedule(sched, well, Schedule(label="Hours", hours=(8, 9)), pack=pack)
    hours = next(op for op in _texts(sched) if op[2] == "Hours")
    assert hours[3] == 17
    eight = next(op for op in _texts(sched) if op[2] == " 8")
    assert eight[3] == 12
    notes = RecordingPlotter()
    paint_notes(notes, well, Notes(label="Scratch"), pack=pack)
    scratch = next(op for op in _texts(notes) if op[2] == "Scratch")
    assert scratch[3] == 17
    prio = RecordingPlotter()
    paint_priorities(prio, well, Priorities(label="Priorities", rows=3), pack=pack)
    label = next(op for op in _texts(prio) if op[2] == "Priorities")
    assert label[3] == 17
    assert _family(label) == "jost"


def test_projects_painter_uses_projects_pack():
    pack = ProjectsPack(
        chrome=_chrome(), stub=_ink("heavy", 23), mark=_ink("bold", 11), status=_ink("book", 10)
    )
    plotter = RecordingPlotter()
    paint_projects_index(plotter, well_rect(NOMAD), _one("projects_index", ProjectsIndex), pack=pack)
    stub = next(op for op in _texts(plotter) if op[2] == "01")
    assert stub[3] == 23
    assert stub[9] == "heavy"
    dest = RecordingPlotter()
    paint_project(dest, well_rect(NOMAD), _one("project", ProjectsBoard), pack=pack)
    mark = next(op for op in _texts(dest) if op[2] == "P")
    assert mark[3] == 11
    todo = next(op for op in _texts(dest) if op[2] == "Todo")
    assert todo[3] == 10


def test_tasks_painter_uses_tasks_pack():
    pack = TasksPack(
        chrome=_chrome(),
        band=_ink("heavy", 24),
        week=_ink("bold", 25),
        range=_ink("book", 9),
        label=_ink("medium", 8),
    )
    plotter = RecordingPlotter()
    paint_tasks_index(plotter, well_rect(NOMAD), _one("tasks_index", TasksIndex), pack=pack)
    jan = next(op for op in _texts(plotter) if op[2] == "January")
    assert jan[3] == 24
    w01 = next(op for op in _texts(plotter) if op[2] == "W01")
    assert w01[3] == 25
    dest = RecordingPlotter()
    paint_task(
        dest,
        well_rect(NOMAD),
        TasksWeekPage(
            year=2026,
            iso_year=2026,
            iso_week=1,
            monday=date(2025, 12, 29),
            sunday=date(2026, 1, 4),
            rows=4,
            index_dest="tasks-index-2026-Q1",
        ),
        pack=pack,
    )
    notes = next(op for op in _texts(dest) if op[2] == "Notes")
    assert notes[3] == 8


def test_review_painter_uses_review_pack():
    pack = ReviewPack(
        chrome=_chrome(),
        band=_ink("heavy", 26),
        chip=_ink("bold", 27),
        weekday=_ink("book", 8),
        day=_ink("medium", 16),
    )
    plotter = RecordingPlotter()
    paint_review_index(plotter, well_rect(NOMAD), _one("review_index", ReviewIndex), pack=pack)
    jan = next(op for op in _texts(plotter) if op[2] == "January")
    assert jan[3] == 26
    w01 = next(op for op in _texts(plotter) if op[2] == "W01")
    assert w01[3] == 27
    dest = RecordingPlotter()
    paint_review(dest, well_rect(NOMAD), _one("review", ReviewWeekPage), pack=pack)
    mon = next(op for op in _texts(dest) if op[2] == "Mon")
    assert mon[3] == 8
    num = next(op for op in _texts(dest) if op[2] == "29")
    assert num[3] == 16


def test_habit_painter_uses_habit_pack():
    pack = HabitPack(
        chrome=_chrome(),
        day=_ink("heavy", 28),
        weekday=_ink("bold", 29),
        label=_ink("book", 7),
        head_day=_ink("book", 3),
        head_weekday=_ink("book", 3),
    )
    plotter = RecordingPlotter()
    paint_habit_grid(plotter, well_rect(NOMAD), _one("habits", HabitGrid), pack=pack)
    one = next(op for op in _texts(plotter) if op[2] == "1")
    assert one[3] == 28
    assert one[9] == "heavy"
    letter = next(op for op in _texts(plotter) if op[2] == "W")
    assert letter[3] == 29


def test_meeting_painter_uses_meeting_pack():
    pack = MeetingPack(
        chrome=_chrome(),
        label=_ink("bold", 30),
        stub=_ink("heavy", 31),
        cue=_ink("medium", 9),
    )
    dest = RecordingPlotter()
    paint_meeting(
        dest,
        well_rect(NOMAD),
        MeetingAgenda(year=2026, agenda=3, action_items=2, index_dest="meetings-index-2026", number=1),
        pack=pack,
    )
    title = next(op for op in _texts(dest) if op[2] == "Title")
    assert title[3] == 30
    index = RecordingPlotter()
    paint_meetings_index(index, well_rect(NOMAD), _one("meetings_index", MeetingIndex), pack=pack)
    stub = next(op for op in _texts(index) if op[2] == "01")
    assert stub[3] == 31
    date_cue = next(op for op in _texts(index) if op[2] == "Date")
    assert date_cue[3] == 9


def test_nav_and_header_use_composed_chrome():
    chrome = _chrome(title=33, meta=34)
    header = RecordingPlotter()
    paint_header(header, NOMAD, "Year", "Q1–Q4", pack=chrome)
    title = next(op for op in _texts(header) if op[2] == "Year")
    assert title[3] == 33
    meta = next(op for op in _texts(header) if op[2] == "Q1–Q4")
    assert meta[3] == 34
    nav = RecordingPlotter()
    paint_nav(nav, NOMAD, (("Year", "year-2026"), ("Mon", "month-2026-01")), "Mon", pack=chrome.nav)
    year = next(op for op in _texts(nav) if op[2] == "Year")
    assert year[3] == 5
    mon = next(op for op in _texts(nav) if op[2] == "Mon")
    assert mon[3] == 6
    assert mon[9] == "heavy"


def test_layout_passes_section_pack_from_ramp_factory():
    """PlannerLayout builds packs from the ramp and hands cover its pack — explicit DI."""

    class StubRamp:
        def __init__(self) -> None:
            self.catalog = jost_catalog()
            built = JostRamp().packs()
            self._packs = replace(
                built,
                cover=CoverPack(
                    year=_ink("book", 41),
                    brow=_ink("bold", 10),
                    specs=_ink("medium", 8),
                ),
            )

        def packs(self) -> PlannerPacks:
            return self._packs

    layout = PlannerLayout(ramp=StubRamp())
    page = Page(
        kind="cover",
        dest="cover",
        title="Cover",
        components=(
            CoverTitle(
                year=2026, subtitle="", device_name="nomad", cta_label="", cta_dest="year-2026"
            ),
        ),
        nav=(),
    )
    plotter = RecordingPlotter()
    layout.paint(page, plotter, NOMAD)
    year = next(op for op in _texts(plotter) if op[2] == "2026")
    assert year[3] == 41
    assert year[9] == "book"
    assert _family(year) == "jost"
    brow = next(op for op in _texts(plotter) if op[2] == "Year Book")
    assert brow[3] == 10
    assert brow[9] == "bold"

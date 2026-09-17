from datetime import date

import pytest

from parch import ConfigError
from parch.books import YearPlanner, outline_entries
from parch.calendar import year_day, year_days
from parch.components import Checkoff365
from parch.devices import NOMAD, SCRIBE
from parch.fonts.ramp import EffectiveRamp
from parch.layouts.planner.painters import (
    CHECKOFF_CIRCLE_SEGS,
    CHECKOFF_COL_PREF,
    CHECKOFF_DIAMOND_STROKE,
    CHECKOFF_GAP,
    CHECKOFF_LABEL_INSET,
    CHECKOFF_NUMERAL_GRAY,
    CHECKOFF_NUMERAL_SCALE,
    HAIR,
    INK,
    MUTED,
    checkoff_columns,
    checkoff_label,
    checkoff_mark,
    checkoff_milestone,
    checkoff_numeral_ink,
    checkoff_seats,
    paint_checkoff_365,
    strip_active,
    strip_items,
    well_rect,
)
from parch.plotter import RecordingPlotter
from parch.sections.checkoff import Checkoff365Section
from parch.spec import Spec
from parch.tracks import rows


def test_year_days_follows_february():
    assert year_days(2026) == 365
    assert year_days(2028) == 366
    assert year_day(2026, 1) == date(2026, 1, 1)
    assert year_day(2026, 365) == date(2026, 12, 31)
    assert year_day(2028, 366) == date(2028, 12, 31)
    assert year_day(2028, 60) == date(2028, 2, 29)


def test_spec_checkoff_default_off_and_dest():
    spec = Spec()
    assert spec.checkoff_365 is False
    assert spec.year_day_count == 365
    assert spec.checkoff_365_dest == "checkoff-365-2026"
    leap = Spec(year=2028)
    assert leap.year_day_count == 366
    assert leap.checkoff_365_dest == "checkoff-365-2028"
    assert Spec.from_mapping({"checkoff_365": True}).checkoff_365 is True
    with pytest.raises(ConfigError, match="checkoff_365 must be a boolean"):
        Spec.from_mapping({"checkoff_365": "true"})


def test_year_planner_omits_checkoff_when_disabled():
    dests = [page.dest for page in YearPlanner().pages(Spec(notes_pages=1))]
    assert dests[:7] == [
        "cover",
        "year-2026",
        "quarter-2026-Q1",
        "quarter-2026-Q2",
        "quarter-2026-Q3",
        "quarter-2026-Q4",
        "month-2026-01",
    ]
    assert "checkoff-365-2026" not in dests
    assert Checkoff365Section(Spec()).pages() == []


def test_year_planner_inserts_checkoff_after_annual_when_enabled():
    spec = Spec(checkoff_365=True, notes_pages=1)
    pages = YearPlanner().pages(spec)
    dests = [page.dest for page in pages]
    assert dests[:8] == [
        "cover",
        "year-2026",
        "checkoff-365-2026",
        "quarter-2026-Q1",
        "quarter-2026-Q2",
        "quarter-2026-Q3",
        "quarter-2026-Q4",
        "month-2026-01",
    ]
    page = next(item for item in pages if item.kind == "checkoff_365")
    assert page.title == "365 Days Check-Off Sheet"
    assert page.dest == "checkoff-365-2026"
    assert strip_active(page.kind) == ""
    labels = [label for label, _ in strip_items(page)]
    assert "365" not in labels
    assert "Check" not in labels
    assert labels == [
        "Year",
        "Quar",
        "Mon",
        "Habit",
        "Week",
        "Rev",
        "Day",
        "Notes",
        "Proj",
        "Meet",
        "Task",
    ]
    assert ("Year", "year-2026") in strip_items(page)
    sheet = next(item for item in page.components if isinstance(item, Checkoff365))
    assert sheet.year == 2026
    assert sheet.days == 365
    assert len(sheet.day_dests) == 365
    assert sheet.day_dests[0] == "2026-01-01"
    assert sheet.day_dests[364] == "2026-12-31"


def test_checkoff_leap_year_uses_366():
    spec = Spec(year=2028, checkoff_365=True, notes_pages=0)
    page = Checkoff365Section(spec).pages()[0]
    sheet = next(item for item in page.components if isinstance(item, Checkoff365))
    assert sheet.days == 366
    assert sheet.day_dests[59] == "2028-02-29"
    assert sheet.day_dests[365] == "2028-12-31"


def test_checkoff_january_only_links_pressed_days():
    spec = Spec(year=2026, months=(1,), checkoff_365=True, notes_pages=0)
    sheet = next(
        item
        for item in Checkoff365Section(spec).pages()[0].components
        if isinstance(item, Checkoff365)
    )
    assert sheet.days == 365
    assert sheet.day_dests[0] == "2026-01-01"
    assert sheet.day_dests[30] == "2026-01-31"
    assert sheet.day_dests[31] is None
    assert sheet.day_dests[364] is None


def test_checkoff_columns_derived_from_well_not_magic_16():
    nomad = well_rect(NOMAD)
    scribe = well_rect(SCRIBE)
    nomad_cols = checkoff_columns(nomad, 365)
    scribe_cols = checkoff_columns(scribe, 365)
    assert 15 <= nomad_cols <= 17
    assert abs(nomad_cols - CHECKOFF_COL_PREF) <= 1
    assert 14 <= scribe_cols <= 20
    nomad_mark = checkoff_mark(checkoff_seats(nomad, 365)[0])
    scribe_mark = checkoff_mark(checkoff_seats(scribe, 365)[0])
    assert scribe_mark.w > nomad_mark.w
    assert nomad_cols != 10
    assert nomad_cols != 18
    assert checkoff_columns(nomad, 366) >= 14
    seats = checkoff_seats(nomad, 365)
    assert len(seats) == 365
    assert seats[0].y == pytest.approx(nomad.y)
    row_n = (365 + nomad_cols - 1) // nomad_cols
    bands = rows(nomad, row_n, gap=CHECKOFF_GAP)
    assert bands[0].y == pytest.approx(nomad.y)
    assert bands[-1].bottom == pytest.approx(nomad.bottom)
    last_row_count = 365 - nomad_cols * (row_n - 1)
    assert last_row_count == len(seats) - nomad_cols * (row_n - 1)
    assert last_row_count < nomad_cols or last_row_count == nomad_cols
    first_mark = checkoff_mark(seats[0])
    assert first_mark.w == pytest.approx(first_mark.h)
    assert first_mark.w < seats[0].w
    assert first_mark.h < seats[0].h
    label = checkoff_label(first_mark)
    assert label.w < first_mark.w
    assert label.h < first_mark.h
    assert label.w == pytest.approx(first_mark.w * (1 - 2 * CHECKOFF_LABEL_INSET))
    assert label.x + label.w / 2 == pytest.approx(first_mark.x + first_mark.w / 2)
    assert label.y + label.h / 2 == pytest.approx(first_mark.y + first_mark.h / 2)


def test_checkoff_milestones_every_tenth():
    assert not checkoff_milestone(1)
    assert not checkoff_milestone(9)
    assert checkoff_milestone(10)
    assert checkoff_milestone(20)
    assert checkoff_milestone(360)
    assert not checkoff_milestone(365)
    assert not checkoff_milestone(366)


def test_checkoff_paint_numbers_circles_diamonds_and_links():
    spec = Spec(checkoff_365=True, notes_pages=1)
    page = Checkoff365Section(spec).pages()[0]
    sheet = next(item for item in page.components if isinstance(item, Checkoff365))
    well = well_rect(NOMAD)
    plotter = RecordingPlotter()
    paint_checkoff_365(plotter, well, sheet)

    texts = [op[2] for op in plotter.ops if op[0] == "text"]
    assert [str(day) for day in range(1, 366)] == [t for t in texts if t.isdigit()]
    assert "366" not in texts
    assert "Favorites" not in texts
    assert "My 100" not in texts
    assert "365 Days Check-Off Sheet" not in texts
    ink = checkoff_numeral_ink(EffectiveRamp())
    assert ink.weight == "medium"
    assert ink.size == pytest.approx(4.3 * CHECKOFF_NUMERAL_SCALE)
    assert ink.size < 4.3
    assert CHECKOFF_NUMERAL_GRAY == MUTED
    assert CHECKOFF_NUMERAL_GRAY > INK
    text_ops = [op for op in plotter.ops if op[0] == "text"]
    assert all(op[9] == "medium" for op in text_ops)
    assert all(op[7] == pytest.approx(CHECKOFF_NUMERAL_GRAY) for op in text_ops)
    assert all(op[3] == pytest.approx(float(ink.size)) for op in text_ops)
    assert all(
        op[1] == checkoff_label(checkoff_mark(seat))
        for op, seat in zip(text_ops, checkoff_seats(well, 365), strict=True)
    )

    seats = checkoff_seats(well, 365)
    diamond_days = [day for day in range(1, 366) if checkoff_milestone(day)]
    circle_days = [day for day in range(1, 366) if not checkoff_milestone(day)]
    assert len(diamond_days) == 36
    assert len(circle_days) == 329

    lines = [op for op in plotter.ops if op[0] == "line"]
    assert len(lines) == len(diamond_days) * 4 + len(circle_days) * CHECKOFF_CIRCLE_SEGS
    diamond_strokes = [
        op[5] for op in lines if op[5] == pytest.approx(CHECKOFF_DIAMOND_STROKE)
    ]
    circle_strokes = [op[5] for op in lines if op[5] == pytest.approx(HAIR)]
    assert len(diamond_strokes) == len(diamond_days) * 4
    assert len(circle_strokes) == len(circle_days) * CHECKOFF_CIRCLE_SEGS
    assert HAIR * 1.25 <= CHECKOFF_DIAMOND_STROKE <= HAIR * 1.5
    fills = [op for op in plotter.ops if op[0] == "rect" and op[3]]
    assert fills == []

    links = [(op[1], op[2]) for op in plotter.ops if op[0] == "link"]
    assert links[0][1] == "2026-01-01"
    assert links[-1][1] == "2026-12-31"
    assert len(links) == 365
    assert links[0][0] == checkoff_mark(seats[0])
    assert links[9][0] == checkoff_mark(seats[9])


def test_checkoff_paint_leap_year_includes_366():
    spec = Spec(year=2028, checkoff_365=True, notes_pages=0)
    sheet = next(
        item
        for item in Checkoff365Section(spec).pages()[0].components
        if isinstance(item, Checkoff365)
    )
    plotter = RecordingPlotter()
    paint_checkoff_365(plotter, well_rect(NOMAD), sheet)
    texts = [op[2] for op in plotter.ops if op[0] == "text"]
    assert "366" in texts
    assert texts.count("1") == 1
    assert [t for t in texts if t.isdigit()][-1] == "366"


def test_checkoff_header_strip_and_outline_when_enabled():
    spec = Spec(checkoff_365=True, months=(1,), notes_pages=0, outline=True)
    book = YearPlanner()
    pages = book.pages(spec)
    plotter = RecordingPlotter()
    book.plot(spec, plotter)
    dests = plotter.dests()
    assert dests[1] == "year-2026"
    assert dests[2] == "checkoff-365-2026"
    texts = [op[2] for op in plotter.ops if op[0] == "text"]
    assert texts.count("365 Days Check-Off Sheet") == 1
    assert "2026" in texts
    assert strip_active("checkoff_365") == ""
    outlined = [dest for _title, dest in plotter.outlines()]
    assert "checkoff-365-2026" in outlined
    assert plotter.outlines() == outline_entries(pages)
    titles = [
        title for title, dest in plotter.outlines() if dest == "checkoff-365-2026"
    ]
    assert titles == ["365 Days Check-Off Sheet"]

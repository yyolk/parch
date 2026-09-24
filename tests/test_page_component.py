"""PK2: layout paints by closed chrome/well component unions, not PageKind."""

from dataclasses import replace
from datetime import date
from typing import TypeAliasType, get_args

import pytest

from parch.components import (
    AnnualMonth,
    ChromeComponent,
    Component,
    CoverTitle,
    DotGridPad,
    EngineeringPad,
    LinedPad,
    Notes,
    PageComponent,
    PerspectivePad,
    Schedule,
    StenoPad,
    WellComponent,
)
from parch.devices.registry import NOMAD
from parch.dotgrid import dotgrid_pages
from parch.layouts.planner import PlannerLayout
from parch.layouts.planner.painters import (
    CLONE_DOT,
    CLONE_DOT_PITCH,
    HEADER_H,
    RULE_C,
    strip_active,
)
from parch.lined import lined_pages
from parch.plotter import RecordingPlotter
from parch.sections.daily import DailySection
from parch.sections.daily_notes import DailyNotesSection
from parch.sections.page import Page
from parch.spec import Spec


def _texts(plotter: RecordingPlotter) -> list[str]:
    return [op[2] for op in plotter.text_ops()]


def _dots(plotter: RecordingPlotter) -> list[tuple]:
    return [
        op
        for op in plotter.ops
        if op[0] == "rect"
        and op[3]
        and not op[2]
        and op[1].w == pytest.approx(CLONE_DOT)
        and op[1].h == pytest.approx(CLONE_DOT)
    ]


def test_pagekind_is_gone():
    import parch.sections.page as page_mod

    assert not hasattr(page_mod, "PageKind")


def test_kind_is_a_free_label():
    page = Page(
        dest="custom-dest",
        kind="graph-paper",
        title="Dots",
        nav=(),
        components=(DotGridPad(sheet=1, sheets=1),),
    )
    assert page.kind == "graph-paper"
    assert isinstance(page.lead, DotGridPad)


def _union_members(alias: object) -> set[type]:
    if isinstance(alias, TypeAliasType):
        alias = alias.__value__
    members: set[type] = set()
    for arg in get_args(alias):
        members.update(_union_members(arg) or {arg})
    return members


def test_chrome_and_well_unions_are_closed_page_leads():
    chrome = _union_members(ChromeComponent)
    well = _union_members(WellComponent)
    page = _union_members(PageComponent)
    component = _union_members(Component)
    assert chrome == {
        CoverTitle,
        EngineeringPad,
        StenoPad,
        DotGridPad,
        LinedPad,
        PerspectivePad,
    }
    assert LinedPad in chrome
    assert chrome.isdisjoint(well)
    assert page == chrome | well
    assert page < component
    assert AnnualMonth not in page
    assert Notes in well
    assert Schedule in well


def test_dotgrid_paints_via_component_not_kind():
    spec = Spec(dotgrid_sheets=1)
    page = replace(dotgrid_pages(spec)[0], kind="not-a-literal")
    assert page.kind == "not-a-literal"
    assert isinstance(page.lead, DotGridPad)
    ink = RecordingPlotter()
    PlannerLayout().paint(page, ink, NOMAD)
    page_rect = NOMAD.page_rect()
    nx = max(2, int(page_rect.w / CLONE_DOT_PITCH))
    ny = max(2, int(page_rect.h / CLONE_DOT_PITCH))
    dots = _dots(ink)
    assert len(dots) == nx * ny
    assert all(op[5] == pytest.approx(RULE_C) for op in dots)
    texts = _texts(ink)
    assert "Year" not in texts
    assert "Dot grid" not in texts
    slabs = [
        op
        for op in ink.ops
        if op[0] == "rect"
        and op[3]
        and op[1].y == pytest.approx(NOMAD.content_top)
        and op[1].h == pytest.approx(HEADER_H)
        and op[5] == pytest.approx(0.0)
    ]
    assert not slabs
    assert strip_active(page) == ""


def test_lined_paints_via_component_not_kind():
    page = replace(lined_pages(Spec(lined_sheets=1))[0], kind="not-a-literal")
    assert isinstance(page.lead, LinedPad)
    ink = RecordingPlotter()
    PlannerLayout().paint(page, ink, NOMAD)
    texts = _texts(ink)
    assert "Year" not in texts
    assert "Lined" not in texts
    slabs = [
        op
        for op in ink.ops
        if op[0] == "rect"
        and op[3]
        and op[1].y == pytest.approx(NOMAD.content_top)
        and op[1].h == pytest.approx(HEADER_H)
        and op[5] == pytest.approx(0.0)
    ]
    assert not slabs
    assert strip_active(page) == ""


def test_daily_schedule_leads_notes_page_is_notes_only():
    spec = Spec(months=(1,), notes_pages=1)
    day = date(2026, 1, 15)
    daily = DailySection(spec).pages_for(day)[0]
    notes = DailyNotesSection(spec).pages_for(day)[0]
    assert isinstance(daily.lead, Schedule)
    assert isinstance(notes.lead, Notes)
    assert strip_active(daily) == "Day"
    assert strip_active(notes) == "Notes"
    relabeled = replace(daily, kind="custom-day")
    ink = RecordingPlotter()
    PlannerLayout().paint(relabeled, ink, NOMAD)
    assert "Schedule" in _texts(ink)


def test_nested_component_cannot_lead_a_page():
    page = Page(
        dest="nested",
        kind="annual",
        title="Nope",
        nav=(),
        components=(
            AnnualMonth(
                month=1,
                name="January",
                dest=None,
                weekday_labels=(),
                weeks=(),
            ),
        ),
    )
    with pytest.raises(TypeError, match="AnnualMonth"):
        PlannerLayout().paint(page, RecordingPlotter(), NOMAD)
    with pytest.raises(TypeError, match="AnnualMonth"):
        strip_active(page)


def test_empty_page_has_no_lead():
    page = Page(dest="empty", kind="cover", title="Empty", nav=(), components=())
    with pytest.raises(TypeError, match="no components"):
        _ = page.lead

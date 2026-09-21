"""PK1: Page is a closed dataclass union, not a PageKind Literal."""

import types
from pathlib import Path
from typing import get_args

from parch.devices import NOMAD
from parch.dotgrid import dotgrid_pages
from parch.layouts.planner import PlannerLayout
from parch.plotter import RecordingPlotter
from parch.sections import page as page_mod
from parch.sections.annual import AnnualSection
from parch.sections.cover import CoverSection
from parch.sections.engineering import EngineeringPadSection
from parch.sections.page import (
    AnnualPage,
    BujoIndexPage,
    BujoKeyPage,
    Checkoff365Page,
    CollectionPage,
    CoverPage,
    DailyNotesPage,
    DailyPage,
    DotgridPage,
    EngineeringBackPage,
    EngineeringFrontPage,
    FavoritesHubPage,
    FullBleedPage,
    FutureLogHubPage,
    HabitsPage,
    HeaderPage,
    MeetingPage,
    MeetingsIndexPage,
    MonthlyLogPage,
    MonthlyTasksPage,
    MonthPage,
    My100HubPage,
    Page,
    ProjectPage,
    ProjectsIndexPage,
    QuarterPage,
    RapidLogHubPage,
    ReviewIndexPage,
    ReviewPage,
    StenoPadPage,
    TaskPage,
    TasksIndexPage,
    WeeklyPage,
)
from parch.sections.steno import StenoPadSection
from parch.spec import Spec

_SRC = Path(__file__).resolve().parents[1] / "src" / "parch"

_MEMBERS = {
    CoverPage,
    AnnualPage,
    FavoritesHubPage,
    My100HubPage,
    Checkoff365Page,
    ProjectsIndexPage,
    ProjectPage,
    MeetingsIndexPage,
    MeetingPage,
    TasksIndexPage,
    TaskPage,
    ReviewIndexPage,
    ReviewPage,
    QuarterPage,
    MonthPage,
    HabitsPage,
    WeeklyPage,
    DailyPage,
    DailyNotesPage,
    EngineeringFrontPage,
    EngineeringBackPage,
    StenoPadPage,
    DotgridPage,
    BujoKeyPage,
    BujoIndexPage,
    FutureLogHubPage,
    MonthlyLogPage,
    MonthlyTasksPage,
    RapidLogHubPage,
    CollectionPage,
}

_KIND_TAGS = {
    "cover",
    "annual",
    "favorites",
    "my_100",
    "checkoff_365",
    "projects_index",
    "project",
    "meetings_index",
    "meeting",
    "tasks_index",
    "task",
    "review_index",
    "review",
    "quarter",
    "month",
    "habits",
    "weekly",
    "daily",
    "daily_notes",
    "engineering_front",
    "engineering_back",
    "steno",
    "dotgrid",
    "bujo_key",
    "bujo_index",
    "future_log",
    "monthly_log",
    "monthly_tasks",
    "rapid_log",
    "collection",
}


def test_pagekind_literal_is_gone():
    text = (_SRC / "sections" / "page.py").read_text()
    assert "type PageKind" not in text
    assert "Literal[" not in text
    assert not hasattr(page_mod, "PageKind")


def test_page_is_closed_union_of_full_bleed_and_header():
    union = Page.__value__
    assert type(union) is types.UnionType
    members = set(get_args(union))
    assert members == _MEMBERS
    assert members == set(get_args(FullBleedPage.__value__)) | set(
        get_args(HeaderPage.__value__)
    )
    assert CoverPage in get_args(FullBleedPage.__value__)
    assert DotgridPage in get_args(FullBleedPage.__value__)
    assert StenoPadPage in get_args(FullBleedPage.__value__)
    assert AnnualPage in get_args(HeaderPage.__value__)


def test_each_member_owns_its_kind_tag():
    assert {cls.kind for cls in _MEMBERS} == _KIND_TAGS


def test_layout_matches_on_type_with_assert_never():
    text = (_SRC / "layouts" / "planner" / "layout.py").read_text()
    assert "from typing import assert_never" in text
    assert "match page:" in text
    assert "match page.kind:" not in text
    assert text.count("assert_never") >= 2


def test_sections_emit_typed_pages_and_layout_paints():
    spec = Spec(months=(1,), notes_pages=0, engineering_sheets=1, steno_sheets=1)
    cover = CoverSection(spec).pages()[0]
    annual = AnnualSection(spec).pages()[0]
    front = EngineeringPadSection(spec).pages()[0]
    steno = StenoPadSection(Spec(steno_sheets=1)).pages()[0]
    dots = dotgrid_pages(Spec(dotgrid_sheets=1))[0]
    assert isinstance(cover, CoverPage)
    assert isinstance(annual, AnnualPage)
    assert isinstance(front, EngineeringFrontPage)
    assert isinstance(steno, StenoPadPage)
    assert isinstance(dots, DotgridPage)
    assert cover.kind == "cover"
    assert annual.kind == "annual"
    assert front.kind == "engineering_front"
    assert steno.kind == "steno"
    assert dots.kind == "dotgrid"
    layout = PlannerLayout()
    for page in (cover, annual, front, steno, dots):
        layout.paint(page, RecordingPlotter(), NOMAD)

"""PK3: ChromeKind and PadKind are two smaller closed unions."""

from parch.devices import NOMAD
from parch.dotgrid import dotgrid_pages
from parch.layouts.planner.layout import PlannerLayout
from parch.layouts.planner.painters import HEADER_H, INK, strip_active
from parch.plotter import RecordingPlotter
from parch.sections.cover import CoverSection
from parch.sections.engineering import EngineeringPadSection
from parch.sections.page import (
    CHROME_KINDS,
    PAD_KINDS,
    ChromeKind,
    PadKind,
    PageKind,
    exhaust_chrome_kind,
    exhaust_pad_kind,
    is_chrome_kind,
    is_pad_kind,
)
from parch.sections.steno import StenoPadSection
from parch.spec import Spec


def test_chrome_and_pad_are_disjoint_closed_sets():
    assert CHROME_KINDS.isdisjoint(PAD_KINDS)
    assert CHROME_KINDS | PAD_KINDS == {
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
    assert "dotgrid" in PAD_KINDS
    assert "dotgrid" not in CHROME_KINDS
    assert "annual" in CHROME_KINDS
    assert "cover" in PAD_KINDS
    assert ChromeKind is not PageKind
    assert PadKind is not PageKind


def test_type_narrowers_partition_page_kind():
    for kind in CHROME_KINDS:
        assert is_chrome_kind(kind)
        assert not is_pad_kind(kind)
    for kind in PAD_KINDS:
        assert is_pad_kind(kind)
        assert not is_chrome_kind(kind)


def test_type_checker_exhausts_both_closed_sets():
    """Every member of each union is listed in its own exhaustive match."""
    assert {exhaust_chrome_kind(kind) for kind in CHROME_KINDS} == CHROME_KINDS
    assert {exhaust_pad_kind(kind) for kind in PAD_KINDS} == PAD_KINDS


def test_chrome_match_does_not_list_pad_kinds():
    chrome_src = PlannerLayout._paint_well.__code__.co_consts
    pad_src = PlannerLayout._paint_pad.__code__.co_consts
    for kind in PAD_KINDS:
        assert kind not in chrome_src
    assert "cover" in pad_src
    assert "dotgrid" in pad_src
    assert "steno" in pad_src
    assert "engineering_front" in pad_src
    assert "annual" not in pad_src
    assert "dotgrid" not in chrome_src
    assert "steno" not in chrome_src
    assert "engineering_front" not in chrome_src


def test_strip_active_is_chrome_only():
    for kind in CHROME_KINDS:
        label = strip_active(kind)
        assert isinstance(label, str)
        assert label


def test_layout_matches_chrome_vs_pad_first():
    cover = CoverSection(Spec()).pages()[0]
    pads = [
        cover,
        *EngineeringPadSection(Spec(engineering_sheets=1)).pages(),
        *StenoPadSection(Spec(steno_sheets=1)).pages(),
        *dotgrid_pages(Spec(dotgrid_sheets=1)),
    ]
    assert [is_pad_kind(page.kind) for page in pads] == [True] * len(pads)
    for page in pads:
        ink = RecordingPlotter()
        PlannerLayout().paint(page, ink, NOMAD)
        slabs = [
            op
            for op in ink.ops
            if op[0] == "rect"
            and op[3]
            and op[1].y == 0.0
            and op[1].h == NOMAD.top_clearance + HEADER_H
            and op[1].w == NOMAD.page_width
            and op[5] == INK
        ]
        assert not slabs, page.kind

"""PK10: family modules re-export one closed PageKind union."""

import ast
import inspect
from typing import get_args

from parch.devices import NOMAD
from parch.kinds import (
    BUJO_KINDS,
    CHROME_KINDS,
    PAD_KINDS,
    PLANNER_KINDS,
    BujoKind,
    ChromeKind,
    PadKind,
    PageKind,
    PlannerKind,
    family_strip_active,
)
from parch.kinds import bujo as bujo_kind
from parch.kinds import chrome as chrome_kind
from parch.kinds import pad as pad_kind
from parch.kinds import planner as planner_kind
from parch.kinds.bujo import exhaust_bujo_kind, paint_bujo
from parch.kinds.chrome import exhaust_chrome_kind, paint_chrome
from parch.kinds.pad import exhaust_pad_kind, paint_pad
from parch.kinds.planner import exhaust_planner_kind, paint_planner
from parch.layouts.planner.layout import PlannerLayout
from parch.layouts.planner.painters import HEADER_H, INK, strip_active
from parch.plotter import RecordingPlotter
from parch.sections import PageKind as SectionPageKind
from parch.sections.annual import AnnualSection
from parch.sections.bujo import BujoKeySection
from parch.sections.cover import CoverSection
from parch.sections.engineering import EngineeringPadSection
from parch.spec import Spec

_PINNED = {
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
    "lined",
    "bujo_key",
    "bujo_index",
    "future_log",
    "monthly_log",
    "monthly_tasks",
    "rapid_log",
    "collection",
}

_FAMILY_MODULES = (chrome_kind, planner_kind, pad_kind, bujo_kind)


def _mentions(fn: object, kinds: frozenset[str]) -> None:
    code = getattr(fn, "__code__", None)
    assert code is not None
    missing = kinds - set(code.co_consts)
    assert not missing, (getattr(fn, "__name__", fn), missing)


def test_page_kind_is_the_reexported_union_of_family_unions():
    assert get_args(PageKind.__value__) == (ChromeKind, PlannerKind, PadKind, BujoKind)
    assert SectionPageKind is PageKind
    assert CHROME_KINDS.isdisjoint(PLANNER_KINDS)
    assert CHROME_KINDS.isdisjoint(PAD_KINDS)
    assert CHROME_KINDS.isdisjoint(BUJO_KINDS)
    assert PLANNER_KINDS.isdisjoint(PAD_KINDS)
    assert PLANNER_KINDS.isdisjoint(BUJO_KINDS)
    assert PAD_KINDS.isdisjoint(BUJO_KINDS)
    assert CHROME_KINDS | PLANNER_KINDS | PAD_KINDS | BUJO_KINDS == _PINNED


def test_cover_is_chrome_and_lined_is_a_pad():
    """PK3 parked cover in PadKind. PK10 keeps cover in chrome and lined in pad."""
    assert "cover" in CHROME_KINDS
    assert "cover" not in PAD_KINDS
    assert "lined" in PAD_KINDS
    assert "lined" not in CHROME_KINDS
    assert "lined" not in PLANNER_KINDS
    assert "lined" not in BUJO_KINDS
    assert "habits" in PLANNER_KINDS
    assert "habits" not in BUJO_KINDS


def test_each_family_match_mentions_every_member():
    assert {exhaust_chrome_kind(kind) for kind in CHROME_KINDS} == CHROME_KINDS
    assert {exhaust_planner_kind(kind) for kind in PLANNER_KINDS} == PLANNER_KINDS
    assert {exhaust_pad_kind(kind) for kind in PAD_KINDS} == PAD_KINDS
    assert {exhaust_bujo_kind(kind) for kind in BUJO_KINDS} == BUJO_KINDS
    _mentions(paint_chrome, CHROME_KINDS)
    _mentions(paint_planner, PLANNER_KINDS)
    _mentions(paint_pad, PAD_KINDS)
    _mentions(paint_bujo, BUJO_KINDS)
    _mentions(planner_kind.planner_header_meta, PLANNER_KINDS)
    _mentions(planner_kind.planner_strip_active, PLANNER_KINDS)
    _mentions(bujo_kind.bujo_header_meta, BUJO_KINDS)
    _mentions(bujo_kind.bujo_strip_active, BUJO_KINDS)


def test_top_level_dispatch_does_not_list_member_strings():
    top = (
        PlannerLayout.paint,
        family_strip_active,
    )
    for fn in top:
        consts = set(fn.__code__.co_consts)
        leaked = _PINNED & consts
        assert not leaked, (fn.__name__, leaked)


def test_family_modules_do_not_import_each_other_or_painters_at_import_time():
    for module in _FAMILY_MODULES:
        tree = ast.parse(inspect.getsource(module))
        imported: list[str] = []
        for node in tree.body:
            if isinstance(node, ast.ImportFrom) and node.module:
                imported.append(node.module)
        assert not any(
            name.startswith("parch.kinds.")
            and name != "parch.kinds.members"
            and name != "parch.kinds.seat"
            for name in imported
        )
        assert "parch.layouts.planner.painters" not in imported
        assert "parch.sections.page" not in imported


def test_strip_active_follows_the_family():
    assert strip_active("cover") == "Year"
    assert strip_active("annual") == "Year"
    assert strip_active("habits") == "Habit"
    assert strip_active("lined") == ""
    assert strip_active("engineering_front") == ""
    assert strip_active("bujo_key") == "Key"
    assert strip_active("collection") == "Col"
    assert family_strip_active("dotgrid") == strip_active("dotgrid")


def test_layout_paints_each_family():
    spec = Spec()
    pages = [
        CoverSection(spec).pages()[0],
        AnnualSection(spec).pages()[0],
        EngineeringPadSection(Spec(engineering_sheets=1)).pages()[0],
        BujoKeySection(spec).pages()[0],
    ]
    headed = {"annual", "bujo_key"}
    for page in pages:
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
        assert bool(slabs) is (page.kind in headed), page.kind

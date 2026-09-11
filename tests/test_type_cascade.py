from dataclasses import FrozenInstanceError

import pytest
from parch.books import YearPlanner
from parch.devices.nomad import NOMAD
from parch.fonts import JostRamp, ROOT_CONTEXT, TypeContext, TypeInk, TypePatch
from parch.layouts.planner import PlannerLayout
from parch.layouts.planner.layout import DAILY_BODY, MINI_BODY, WEEK_BODY
from parch.plotter import RecordingPlotter
from parch.spec import Spec


def test_role_map_merges_over_context():
    """Role-specified fields win; unspecified role fields inherit context."""
    ctx = TypeContext(
        body=TypePatch(family="jost", weight="heavy", size=3.0),
        chrome=TypePatch(size=20.0),
    )
    ramp = JostRamp()
    # cover_year pins every field — context cannot shrink it
    assert ramp.ink("cover_year", ctx) == TypeInk(family="jost", weight="heavy", size=42)
    assert ramp.ink("page_title", ctx) == TypeInk(family="jost", weight="medium", size=11)
    # body pins family+weight; size comes from context
    assert ramp.ink("body", ctx) == TypeInk(family="jost", weight="book", size=3.0)
    # chrome pins family+weight; size from context
    assert ramp.ink("chrome", ctx) == TypeInk(family="jost", weight="book", size=20.0)
    # default context (None) is ROOT
    assert ramp.ink("body") == TypeInk(family="jost", weight="book", size=8.5)
    assert ramp.ink("chrome") == TypeInk(family="jost", weight="book", size=7.4)


def test_incomplete_context_without_size_raises():
    with pytest.raises(ValueError, match="incomplete type ink"):
        JostRamp().ink("body", TypeContext())


def test_context_overlay_later_wins():
    root = ROOT_CONTEXT
    week = root.overlay(WEEK_BODY)
    daily = week.overlay(DAILY_BODY)
    mini = daily.overlay(MINI_BODY)
    assert week.body.size == 11.0
    assert daily.body.size == 7.6
    assert mini.body.size == 5.3
    # chrome inherits through overlays
    assert mini.chrome.size == 7.4


def test_layout_stack_push_pop_and_frozen_bind():
    layout = PlannerLayout()
    assert layout.snapshot() == ROOT_CONTEXT
    assert layout.bound().ink("body").size == 8.5

    layout.push(WEEK_BODY)
    week_bound = layout.bound()
    assert week_bound.ink("body").size == 11.0
    assert week_bound.ink("chrome").size == 7.4

    layout.push(DAILY_BODY)
    assert layout.bound().ink("body").size == 7.6
    # earlier bind is a frozen snapshot
    assert week_bound.ink("body").size == 11.0
    assert week_bound.context.body.size == 11.0

    layout.pop()
    assert layout.bound().ink("body").size == 11.0
    layout.pop()
    assert layout.snapshot() == ROOT_CONTEXT
    with pytest.raises(IndexError, match="root TypeContext"):
        layout.pop()


def test_layout_context_manager_pops_on_error():
    layout = PlannerLayout()
    with pytest.raises(RuntimeError, match="boom"):
        with layout.context(DAILY_BODY):
            assert layout.bound().ink("body").size == 7.6
            raise RuntimeError("boom")
    assert layout.snapshot() == ROOT_CONTEXT
    assert layout.bound().ink("body").size == 8.5


def test_layouts_do_not_share_a_stack():
    a = PlannerLayout()
    b = PlannerLayout()
    a.push(WEEK_BODY)
    assert a.bound().ink("body").size == 11.0
    assert b.bound().ink("body").size == 8.5


def test_type_context_is_frozen():
    ctx = TypeContext(body=TypePatch(size=8.5))
    with pytest.raises(FrozenInstanceError):
        ctx.body = TypePatch(size=1.0)  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        ctx.body.size = 1.0  # type: ignore[misc]


def test_no_threadlocals_or_contextvars():
    import parch.fonts.ramp as ramp_mod
    import parch.layouts.planner.layout as layout_mod

    assert "contextvars" not in ramp_mod.__dict__
    assert "contextvars" not in layout_mod.__dict__
    assert "threading" not in ramp_mod.__dict__
    assert "threading" not in layout_mod.__dict__


def _pages():
    return YearPlanner().pages(Spec(months=(1,), day=1, notes_pages=1))


def _paint(dest: str) -> RecordingPlotter:
    page = next(page for page in _pages() if page.dest == dest)
    plotter = RecordingPlotter()
    PlannerLayout().paint(page, plotter, NOMAD)
    return plotter


def _text_size(plotter: RecordingPlotter, content: str) -> float:
    op = next(op for op in plotter.ops if op[0] == "text" and op[2] == content)
    return float(op[3])


def _text_family(plotter: RecordingPlotter, content: str) -> object:
    return next(op for op in plotter.ops if op[0] == "text" and op[2] == content)[10]


def test_week_body_is_larger_than_daily_via_page_push():
    week = _paint("week-2026-W01")
    daily = _paint("2026-01-01")
    # week day numeral (29 Dec 2025 sits in W01) vs daily schedule hour
    assert _text_size(week, "29") == 11.0
    assert _text_family(week, "29") == "jost"
    assert _text_size(daily, " 7") == 7.6
    assert _text_family(daily, " 7") == "jost"
    assert _text_size(daily, " 7") < _text_size(week, "29")


def test_daily_mini_month_section_override():
    daily = _paint("2026-01-01")
    # page body (schedule hour) vs section push (mini-month day)
    assert _text_size(daily, " 7") == 7.6
    assert _text_size(daily, "20") == 5.3
    assert _text_family(daily, "20") == "jost"


def test_month_uses_root_body():
    month = _paint("month-2026-01")
    assert _text_size(month, "15") == 8.5
    assert _text_family(month, "15") == "jost"


def test_year_mini_month_uses_section_body():
    year = _paint("year-2026")
    assert _text_size(year, "15") == 5.3
    assert _text_family(year, "15") == "jost"


def test_header_chrome_still_resolves_through_bound_ramp():
    week = _paint("week-2026-W01")
    title = next(op for op in week.ops if op[0] == "text" and op[2] == "Week 01")
    assert title[3] == 11
    assert title[10] == "jost"
    meta = next(op for op in week.ops if op[0] == "text" and op[1].x > 90)
    # header meta is chrome (7.4), not the week body 11
    assert meta[3] == 7.4
    assert meta[10] == "jost"

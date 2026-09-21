"""PK11: every PageKind has one plan; strip and outline stay on that plan."""

from parch.books import YearPlanner
from parch.layouts.planner.kind_plan import kind_plan, page_kinds
from parch.spec import Spec

_RUN = frozenset(
    {
        "annual",
        "favorites",
        "my_100",
        "checkoff_365",
        "projects_index",
        "meetings_index",
        "tasks_index",
        "review_index",
        "bujo_key",
        "bujo_index",
        "future_log",
        "collection",
    }
)
_EACH = frozenset({"quarter", "month", "monthly_log"})
_BLEED = frozenset(
    {
        "cover",
        "engineering_front",
        "engineering_back",
        "steno",
        "dotgrid",
        "lined",
    }
)
_STRIPS = {
    "cover": "",
    "annual": "Year",
    "favorites": "Fav",
    "my_100": "100",
    "checkoff_365": "365",
    "projects_index": "Proj",
    "project": "Proj",
    "meetings_index": "Meet",
    "meeting": "Meet",
    "tasks_index": "Task",
    "task": "Task",
    "review_index": "Rev",
    "review": "Rev",
    "quarter": "Quar",
    "month": "Mon",
    "habits": "Habit",
    "weekly": "Week",
    "daily": "Day",
    "daily_notes": "Notes",
    "engineering_front": "",
    "engineering_back": "",
    "steno": "",
    "dotgrid": "",
    "lined": "",
    "bujo_key": "Key",
    "bujo_index": "Idx",
    "future_log": "Fut",
    "monthly_log": "Mon",
    "monthly_tasks": "Mon",
    "rapid_log": "Day",
    "collection": "Col",
}


def test_page_kinds_match_plan_table() -> None:
    assert set(page_kinds()) == set(_STRIPS)


def test_each_kind_plan_is_total() -> None:
    for kind in page_kinds():
        plan = kind_plan(kind)
        assert plan.strip == _STRIPS[kind]
        if kind in _BLEED:
            assert plan.frame == "bleed"
            assert plan.outline == "skip"
        else:
            assert plan.frame == "chrome"
        if kind in _RUN:
            assert plan.outline == "run"
        elif kind in _EACH:
            assert plan.outline == "each"
        elif kind not in _BLEED:
            assert plan.outline == "skip"


def test_annual_overlay_reads_the_plan() -> None:
    pages = YearPlanner().pages(Spec(notes_pages=1))
    annual = next(page for page in pages if page.kind == "annual")
    assert kind_plan(annual.kind).overlay(annual).meta == "Q1–Q4"
    assert kind_plan("cover").strip == ""

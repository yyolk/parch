"""PK4: PageKind StrEnum is the only closed set. list(PageKind) walks it."""

from parch.dotgrid import dotgrid_pages
from parch.layouts.planner.painters import strip_active
from parch.sections.cover import CoverSection
from parch.sections.page import PageKind
from parch.spec import Spec


def test_pagekind_iteration_is_the_closed_set():
    assert [kind.value for kind in PageKind] == [
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
    ]
    assert PageKind.DOTGRID is PageKind("dotgrid")
    assert PageKind.DOTGRID == "dotgrid"


def test_strip_active_walks_every_pagekind():
    labels = {kind: strip_active(kind) for kind in PageKind}
    assert set(labels) == set(PageKind)
    assert labels[PageKind.ANNUAL] == "Year"
    assert labels[PageKind.DOTGRID] == ""
    assert labels[PageKind.COVER] == "Year"
    assert all(isinstance(label, str) for label in labels.values())


def test_constructed_pages_store_enum_members():
    cover = CoverSection(Spec()).pages()[0]
    assert cover.kind is PageKind.COVER
    pad = dotgrid_pages(Spec(dotgrid_sheets=1))[0]
    assert pad.kind is PageKind.DOTGRID
    assert [page.kind for page in (cover, pad)] == ["cover", "dotgrid"]

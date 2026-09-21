"""Sealed page-kind catalog stays closed at import and in paint."""

import ast
from pathlib import Path

import pytest

import parch.sections.kinds as kinds
from parch.sections.kinds import KIND_CATALOG, Kind, PageKind

_TAGS = (
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
)


def test_catalog_matches_explicit_union() -> None:
    assert isinstance(KIND_CATALOG, tuple)
    assert frozenset(PageKind.__value__.__args__) == frozenset(KIND_CATALOG)
    assert tuple(cls.tag for cls in KIND_CATALOG) == _TAGS
    assert len({cls.tag for cls in KIND_CATALOG}) == len(KIND_CATALOG)


def test_kind_compares_as_its_tag() -> None:
    for cls in KIND_CATALOG:
        kind = cls()
        assert str(kind) == cls.tag
        assert kind == cls.tag
        assert cls.tag == kind
        assert [kind] == [cls.tag]
        assert {kind: "ok"}[cls.tag] == "ok"


def test_sealed_against_a_new_subclass() -> None:
    with pytest.raises(TypeError, match="sealed"):

        class Extra(Kind, tag="extra"):
            pass


def test_sealed_against_an_indirect_subclass() -> None:
    with pytest.raises(TypeError, match="directly"):

        class Sub(kinds.Cover, tag="subcover"):
            pass


def _matched_kind_classes(fn_name: str) -> set[str]:
    path = Path(__file__).resolve().parents[1] / "src/parch/layouts/planner/layout.py"
    tree = ast.parse(path.read_text())
    for node in tree.body:
        if not isinstance(node, ast.ClassDef) or node.name != "PlannerLayout":
            continue
        for item in node.body:
            if isinstance(item, ast.FunctionDef) and item.name == fn_name:
                found: set[str] = set()
                for sub in ast.walk(item):
                    if isinstance(sub, ast.MatchClass) and isinstance(
                        sub.cls, ast.Attribute
                    ):
                        found.add(sub.cls.attr)
                return found
    raise AssertionError(fn_name)


def test_paint_and_well_match_every_sealed_kind() -> None:
    names = {cls.__name__ for cls in KIND_CATALOG}
    assert names <= _matched_kind_classes("paint")
    assert names <= _matched_kind_classes("_paint_well")

"""PAGE_KIND_TABLE is the only page-kind list; generated aliases match it."""

import ast
from pathlib import Path
from typing import TypeAliasType, get_args

from parch.layouts.planner.painters import strip_active
from parch.sections.kind_table import (
    PAGE_KIND_TABLE,
    outline_kinds,
    page_face,
    render_page_kind_module,
)
from parch.sections.page_kind import PageFace, PageKind, WellKind

_ROOT = Path(__file__).resolve().parents[1]
_LAYOUT = _ROOT / "src" / "parch" / "layouts" / "planner" / "layout.py"

_OUTLINE_RUN = frozenset(
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
_OUTLINE_EACH = frozenset({"quarter", "month", "monthly_log"})


def _literal_args(alias: TypeAliasType) -> tuple[str, ...]:
    args = get_args(alias.__value__)
    assert all(isinstance(arg, str) for arg in args)
    return args


def _match_strings(fn_name: str) -> set[str]:
    tree = ast.parse(_LAYOUT.read_text())
    for node in tree.body:
        if not isinstance(node, ast.ClassDef) or node.name != "PlannerLayout":
            continue
        for item in node.body:
            if isinstance(item, ast.FunctionDef) and item.name == fn_name:
                found: set[str] = set()
                for stmt in item.body:
                    if isinstance(stmt, ast.Match):
                        for case in stmt.cases:
                            found |= _pattern_strings(case.pattern)
                return found
    raise AssertionError(f"{fn_name} not found")


def _pattern_strings(pattern: ast.pattern) -> set[str]:
    if isinstance(pattern, ast.MatchValue) and isinstance(pattern.value, ast.Constant):
        value = pattern.value.value
        return {value} if isinstance(value, str) else set()
    if isinstance(pattern, ast.MatchOr):
        found: set[str] = set()
        for child in pattern.patterns:
            found |= _pattern_strings(child)
        return found
    return set()


def test_generated_page_kind_module_matches_table():
    path = _ROOT / "src" / "parch" / "sections" / "page_kind.py"
    assert path.read_text() == render_page_kind_module()
    assert _literal_args(PageKind) == tuple(row.id for row in PAGE_KIND_TABLE)
    assert _literal_args(PageFace) == tuple(
        dict.fromkeys(row.face for row in PAGE_KIND_TABLE)
    )
    assert _literal_args(WellKind) == tuple(
        row.id for row in PAGE_KIND_TABLE if row.face == "well"
    )


def test_table_ids_are_unique_and_partitioned_by_face():
    ids = [row.id for row in PAGE_KIND_TABLE]
    assert len(ids) == len(set(ids)) == 31
    wells = {row.id for row in PAGE_KIND_TABLE if row.face == "well"}
    others = {row.id for row in PAGE_KIND_TABLE if row.face != "well"}
    assert wells.isdisjoint(others)
    assert wells | others == set(ids)
    assert len(wells) == 25


def test_strip_outline_and_face_follow_the_table():
    for row in PAGE_KIND_TABLE:
        assert strip_active(row.id) == row.strip
        assert page_face(row.id) == row.face
    assert strip_active("not-a-kind") == "Year"
    assert outline_kinds("run") == _OUTLINE_RUN
    assert outline_kinds("each") == _OUTLINE_EACH
    covered = outline_kinds("run") | outline_kinds("each") | outline_kinds("skip")
    assert covered == {row.id for row in PAGE_KIND_TABLE}


def test_paint_matches_cover_generated_aliases():
    assert _match_strings("paint") == set(_literal_args(PageFace))
    assert _match_strings("_paint_well") == set(_literal_args(WellKind))

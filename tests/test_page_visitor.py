"""Closed PageVisitor: visit_* matches PageKind, accept double-dispatches."""

import types
from collections.abc import Callable
from typing import get_args, override

import pytest

from parch.devices import NOMAD
from parch.layouts.planner.layout import PlannerLayout
from parch.plotter import RecordingPlotter
from parch.sections.annual import AnnualSection
from parch.sections.cover import CoverSection
from parch.sections.page import Page, PageKind
from parch.sections.visit import PageVisitor, accept
from parch.spec import Spec


def _kinds() -> tuple[PageKind, ...]:
    return get_args(PageKind.__value__)


def _page(kind: PageKind) -> Page:
    return Page(dest="d", kind=kind, title="", nav=(), components=())


def _recorder() -> PageVisitor[str]:
    def _exec(ns: dict[str, object]) -> None:
        def _bind(kind: str) -> Callable[[PageVisitor[str], Page], str]:
            def visit(_self: PageVisitor[str], _page: Page) -> str:
                return kind

            return visit

        for kind in _kinds():
            ns[f"visit_{kind}"] = _bind(kind)

    record = types.new_class("_Record", (PageVisitor[str],), exec_body=_exec)
    return record()


def test_visit_methods_are_the_pagekind_set() -> None:
    methods = {name.removeprefix("visit_") for name in PageVisitor.__abstractmethods__}
    assert methods == set(_kinds())


def test_accept_hits_the_matching_visit() -> None:
    visitor = _recorder()
    for kind in _kinds():
        page = _page(kind)
        assert accept(page, visitor) == kind
        assert page.accept(visitor) == kind


def test_partial_visitor_cannot_be_constructed() -> None:
    class _Partial(PageVisitor[None]):
        @override
        def visit_cover(self, page: Page) -> None:
            return None

    with pytest.raises(TypeError, match="abstract"):
        _Partial()


def test_accept_rejects_a_kind_outside_the_set() -> None:
    page = _page("cover")
    object.__setattr__(page, "kind", "nope")
    with pytest.raises(AssertionError):
        accept(page, _recorder())


def test_planner_paint_accepts_a_visitor(monkeypatch: pytest.MonkeyPatch) -> None:
    import parch.layouts.planner.layout as layout

    seen: list[str] = []
    real = layout.accept

    def spy(page: Page, visitor: PageVisitor[None]) -> None:
        seen.append(page.kind)
        assert type(visitor).__name__ == "_PaintVisitor"
        real(page, visitor)

    monkeypatch.setattr(layout, "accept", spy)
    cover = CoverSection(Spec()).pages()[0]
    plotter = RecordingPlotter()
    PlannerLayout().paint(cover, plotter, NOMAD)
    assert seen == ["cover"]
    assert "Year Book" in [op[2] for op in plotter.ops if op[0] == "text"]

    annual = AnnualSection(Spec()).pages()[0]
    ink = RecordingPlotter()
    PlannerLayout().paint(annual, ink, NOMAD)
    assert seen == ["cover", "annual"]
    assert any(op[0] == "rect" for op in ink.ops)

"""PK12: kind is derived from the component tuple, not stored on Page."""

from dataclasses import fields

from parch.books import YearPlanner
from parch.components import EngineeringPad
from parch.sections.engineering import EngineeringPadSection
from parch.sections.page import Page
from parch.sections.seating import seating_view
from parch.spec import Spec


def test_kind_is_not_a_field() -> None:
    assert "kind" not in {field.name for field in fields(Page)}


def test_engineering_faces_derive_two_kinds() -> None:
    pages = EngineeringPadSection(Spec(engineering_sheets=1)).pages()
    assert [page.kind for page in pages] == ["engineering_front", "engineering_back"]
    assert all(isinstance(page.components[0], EngineeringPad) for page in pages)


def test_annual_overlay_comes_from_the_grid() -> None:
    annual = next(
        page
        for page in YearPlanner().pages(Spec(notes_pages=1))
        if page.kind == "annual"
    )
    view = seating_view(annual.components, annual.dest)
    assert view.kind == "annual"
    assert view.overlay.meta == "Q1–Q4"
    assert view.frame == "chrome"
    assert view.outline == "run"

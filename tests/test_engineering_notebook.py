from pathlib import Path
from typing import Protocol

import pytest
from pypdf import PdfReader

from parch import ConfigError
from parch.books import (
    Book,
    EngineeringNotebook,
    ProjectsNotebook,
    YearPlanner,
    book_for,
)
from parch.components import CoverTitle, EngineeringPad
from parch.plotter import RecordingPlotter
from parch.press import press
from parch.spec import Spec


def test_book_is_protocol_not_abc():
    """Books match the surface; they do not inherit Book (not an ABC/plugin)."""
    assert issubclass(Book, Protocol)
    for cls in (YearPlanner, ProjectsNotebook, EngineeringNotebook):
        assert Book not in cls.__mro__
        book = cls()
        assert callable(book.pages)
        assert callable(book.plot)
        assert book.ramp is not None


def test_engineering_notebook_is_cover_then_duplex_pad():
    spec = Spec(book="engineering-notebook", engineering_sheets=2)
    pages = EngineeringNotebook().pages(spec)
    assert [page.kind for page in pages] == [
        "cover",
        "engineering_front",
        "engineering_back",
        "engineering_front",
        "engineering_back",
    ]
    assert {page.kind for page in pages} == {
        "cover",
        "engineering_front",
        "engineering_back",
    }
    assert len(pages) == 1 + 2 * spec.engineering_sheets

    cover = pages[0].components[0]
    assert isinstance(cover, CoverTitle)
    assert cover.cta_dest == spec.dest_for_engineering_pad(1, "front")
    assert cover.eyebrow == "Engineering"
    plotter = RecordingPlotter()
    EngineeringNotebook().plot(spec, plotter)
    texts = [op[2] for op in plotter.ops if op[0] == "text"]
    assert cover.eyebrow in texts
    assert cover.specs_lead == ""
    assert "Year Book" not in texts
    assert not any("monday weeks" in str(t).lower() for t in texts)
    assert pages[1].dest == spec.dest_for_engineering_pad(1, "front")
    assert pages[2].dest == spec.dest_for_engineering_pad(1, "back")
    front = pages[1].components[0]
    back = pages[2].components[0]
    assert isinstance(front, EngineeringPad)
    assert isinstance(back, EngineeringPad)
    assert front.face == "front"
    assert back.face == "back"
    assert all(page.nav == () for page in pages[1:])
    assert spec.year_dest not in {page.dest for page in pages}
    assert spec.projects_index_dest not in {page.dest for page in pages}


def test_press_selects_engineering_notebook_from_toml(tmp_path: Path):
    spec = Spec.from_path(Path("examples/engineering-notebook.toml"))
    assert spec.book == "engineering-notebook"
    assert spec.engineering_sheets == 12
    assert book_for(spec.book) is EngineeringNotebook
    assert book_for("year-planner") is YearPlanner
    assert book_for("projects-notebook") is ProjectsNotebook

    out = tmp_path / "engineering-notebook.pdf"
    press(spec, out)
    dests = {str(key).lstrip("/") for key in (PdfReader(out).named_destinations or {})}
    assert "cover" in dests
    assert spec.dest_for_engineering_pad(1, "front") in dests
    assert spec.dest_for_engineering_pad(1, "back") in dests
    assert spec.dest_for_engineering_pad(12, "front") in dests
    assert spec.dest_for_engineering_pad(12, "back") in dests
    assert spec.year_dest not in dests
    assert spec.projects_index_dest not in dests
    assert len(PdfReader(out).pages) == 1 + 2 * spec.engineering_sheets


def test_engineering_notebook_requires_sheets():
    with pytest.raises(ConfigError, match="engineering_sheets must be >= 1"):
        Spec(book="engineering-notebook")
    with pytest.raises(ConfigError, match="engineering_sheets must be >= 1"):
        Spec.from_mapping({"book": "engineering-notebook"})
    with pytest.raises(ConfigError, match="engineering-notebook"):
        book_for("meetings-notebook")

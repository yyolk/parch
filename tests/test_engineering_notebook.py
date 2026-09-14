from pathlib import Path

from pypdf import PdfReader

from parch.books import EngineeringNotebook, ProjectsNotebook, YearPlanner, book_for
from parch.components import CoverTitle, EngineeringPad
from parch.plotter import RecordingPlotter
from parch.press import press
from parch.sections.engineering import EngineeringPadSection, duplex_sheet
from parch.spec import Spec


def test_notebook_pages_are_cover_then_expanded_sheets():
    spec = Spec(book="engineering-notebook", engineering_sheets=2)
    pages = EngineeringNotebook().pages(spec)
    assert [page.kind for page in pages] == [
        "cover",
        "engineering_front",
        "engineering_back",
        "engineering_front",
        "engineering_back",
    ]
    assert [page.dest for page in pages] == [
        "cover",
        "engineering-2026-01-front",
        "engineering-2026-01-back",
        "engineering-2026-02-front",
        "engineering-2026-02-back",
    ]
    cover = pages[0].components[0]
    assert isinstance(cover, CoverTitle)
    assert cover.eyebrow == "Engineering"
    assert cover.specs_lead == ""
    assert cover.cta_dest == spec.dest_for_engineering_pad(1, "front")
    assert cover.subtitle == spec.title
    front = pages[1].components[0]
    back = pages[2].components[0]
    assert isinstance(front, EngineeringPad)
    assert front.face == "front"
    assert back.face == "back"
    assert front.sheet == back.sheet == 1
    assert front.sheets == 2
    assert pages[3].components[0].sheet == 2
    assert spec.year_dest not in {page.dest for page in pages}


def test_factory_composes_section_pages_for():
    spec = Spec(book="engineering-notebook", engineering_sheets=2)
    pad = EngineeringPadSection(spec)
    factory = EngineeringNotebook().pages(spec)
    assert factory[1:] == [
        *pad.pages_for(1),
        *pad.pages_for(2),
    ]
    assert pad.pages_for(1) == list(duplex_sheet(spec, 1))
    assert pad.pages() == [*pad.pages_for(1), *pad.pages_for(2)]


def test_notebook_cover_only_when_no_sheets():
    spec = Spec(book="engineering-notebook")
    pages = EngineeringNotebook().pages(spec)
    assert [page.kind for page in pages] == ["cover"]
    cover = pages[0].components[0]
    assert isinstance(cover, CoverTitle)
    assert cover.cta_dest == spec.cover_dest


def test_notebook_plot_skips_year_book_copy():
    spec = Spec(book="engineering-notebook", engineering_sheets=1)
    plotter = RecordingPlotter()
    EngineeringNotebook().plot(spec, plotter)
    texts = [op[2] for op in plotter.ops if op[0] == "text"]
    assert "Engineering" in texts
    assert "Year Book" not in texts
    assert "Subject" in texts
    assert not any("monday weeks" in str(t).lower() for t in texts)


def test_press_selects_engineering_notebook_from_toml(tmp_path: Path):
    spec = Spec.from_path(Path("examples/engineering-notebook.toml"))
    assert spec.book == "engineering-notebook"
    assert spec.engineering_sheets == 2
    assert spec.title == "Engineering notebook"
    assert book_for(spec.book) is EngineeringNotebook
    assert book_for("projects-notebook") is ProjectsNotebook
    assert book_for("year-planner") is YearPlanner

    out = tmp_path / "engineering-notebook.pdf"
    press(spec, out)
    reader = PdfReader(out)
    dests = {str(key).lstrip("/") for key in (reader.named_destinations or {})}
    assert len(reader.pages) == 1 + 2 * spec.engineering_sheets
    assert "cover" in dests
    assert spec.dest_for_engineering_pad(1, "front") in dests
    assert spec.dest_for_engineering_pad(1, "back") in dests
    assert spec.dest_for_engineering_pad(2, "front") in dests
    assert spec.dest_for_engineering_pad(2, "back") in dests
    assert spec.year_dest not in dests
    assert spec.projects_index_dest not in dests


def test_pad_only_toml_still_skips_cover(tmp_path: Path):
    spec = Spec.from_path(Path("examples/engineering-pad.toml"))
    assert spec.book == "year-planner"
    out = tmp_path / "engineering-pad.pdf"
    press(spec, out)
    dests = {str(key).lstrip("/") for key in (PdfReader(out).named_destinations or {})}
    assert len(PdfReader(out).pages) == 2
    assert "cover" not in dests

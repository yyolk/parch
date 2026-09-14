from pathlib import Path

from pypdf import PdfReader

from parch.books import EngineeringNotebook, ProjectsNotebook, YearPlanner, book_for
from parch.components import CoverTitle, EngineeringPad
from parch.plotter import RecordingPlotter
from parch.press import press
from parch.spec import Spec


def test_engineering_notebook_is_cover_then_duplex():
    spec = Spec(book="engineering-notebook", engineering_sheets=1)
    pages = EngineeringNotebook().pages(spec)
    assert [page.kind for page in pages] == [
        "cover",
        "engineering_front",
        "engineering_back",
    ]
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
    assert isinstance(pages[1].components[0], EngineeringPad)
    assert pages[1].components[0].face == "front"
    assert pages[2].components[0].face == "back"
    assert spec.year_dest not in {page.dest for page in pages}


def test_press_selects_engineering_notebook_from_toml(tmp_path: Path):
    spec = Spec.from_path(Path("examples/engineering-notebook.toml"))
    assert spec.book == "engineering-notebook"
    assert spec.engineering_sheets == 1
    assert book_for(spec.book) is EngineeringNotebook
    assert book_for("year-planner") is YearPlanner
    assert book_for("projects-notebook") is ProjectsNotebook

    out = tmp_path / "engineering-notebook.pdf"
    press(spec, out)
    dests = {str(key).lstrip("/") for key in (PdfReader(out).named_destinations or {})}
    assert "cover" in dests
    assert spec.dest_for_engineering_pad(1, "front") in dests
    assert spec.dest_for_engineering_pad(1, "back") in dests
    assert spec.year_dest not in dests
    assert spec.projects_index_dest not in dests
    assert len(PdfReader(out).pages) == 1 + 2 * spec.engineering_sheets

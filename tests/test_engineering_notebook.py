from pathlib import Path

from pypdf import PdfReader

from parch.books import EngineeringNotebook, ProjectsNotebook, YearPlanner, book_for
from parch.components import CoverTitle, EngineeringPad
from parch.plotter import RecordingPlotter
from parch.press import press
from parch.sections.engineering import EngineeringPadSection
from parch.sections.engineering_notebook import EngineeringNotebookSection
from parch.spec import Spec


def test_composite_is_cover_then_duplex_faces():
    spec = Spec(book="engineering-notebook", engineering_sheets=2, title="Engineering")
    section_pages = EngineeringNotebookSection(spec).pages()
    book_pages = EngineeringNotebook().pages(spec)
    assert book_pages == section_pages
    assert [page.kind for page in section_pages] == [
        "cover",
        "engineering_front",
        "engineering_back",
        "engineering_front",
        "engineering_back",
    ]
    assert [page.dest for page in section_pages] == [
        spec.cover_dest,
        spec.dest_for_engineering_pad(1, "front"),
        spec.dest_for_engineering_pad(1, "back"),
        spec.dest_for_engineering_pad(2, "front"),
        spec.dest_for_engineering_pad(2, "back"),
    ]
    pad_only = EngineeringPadSection(spec).pages()
    assert [page.kind for page in section_pages[1:]] == [page.kind for page in pad_only]
    cover = section_pages[0].components[0]
    assert isinstance(cover, CoverTitle)
    assert cover.eyebrow == "Engineering"
    assert cover.specs_lead == ""
    assert cover.cta_dest == spec.dest_for_engineering_pad(1, "front")
    assert cover.subtitle == "Engineering"
    front = section_pages[1].components[0]
    back = section_pages[2].components[0]
    assert isinstance(front, EngineeringPad)
    assert front.face == "front"
    assert back.face == "back"
    assert front.sheet == back.sheet == 1
    assert spec.year_dest not in {page.dest for page in section_pages}


def test_book_is_thin_shell_around_composite():
    spec = Spec(book="engineering-notebook", engineering_sheets=1)
    book = EngineeringNotebook()
    assert book.pages(spec) == EngineeringNotebookSection(spec).pages()
    plotter = RecordingPlotter()
    book.plot(spec, plotter)
    texts = [op[2] for op in plotter.ops if op[0] == "text"]
    assert "Engineering" in texts
    assert "Year Book" not in texts
    assert not any("monday weeks" in str(t).lower() for t in texts)
    assert "Subject" in texts
    assert "Date" in texts
    assert "Sheet" in texts


def test_press_selects_engineering_notebook_from_toml(tmp_path: Path):
    spec = Spec.from_path(Path("examples/engineering-notebook.toml"))
    assert spec.book == "engineering-notebook"
    assert spec.engineering_sheets == 2
    assert spec.title == "Engineering"
    assert book_for(spec.book) is EngineeringNotebook
    assert book_for("year-planner") is YearPlanner
    assert book_for("projects-notebook") is ProjectsNotebook

    out = tmp_path / "engineering-notebook.pdf"
    press(spec, out)
    reader = PdfReader(out)
    dests = {str(key).lstrip("/") for key in (reader.named_destinations or {})}
    assert spec.cover_dest in dests
    assert spec.dest_for_engineering_pad(1, "front") in dests
    assert spec.dest_for_engineering_pad(1, "back") in dests
    assert spec.dest_for_engineering_pad(2, "front") in dests
    assert spec.dest_for_engineering_pad(2, "back") in dests
    assert spec.year_dest not in dests
    assert spec.projects_index_dest not in dests
    assert len(reader.pages) == 1 + 2 * spec.engineering_sheets

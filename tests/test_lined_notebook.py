from pathlib import Path

from pypdf import PdfReader

from parch.books import LinedNotebook, book_for
from parch.components import CoverTitle, LinedPad
from parch.plotter import RecordingPlotter
from parch.press import press
from parch.spec import Spec


def test_lined_notebook_is_cover_then_lined_pages():
    spec = Spec(book="lined-notebook", lined_sheets=2, title="Lined")
    pages = LinedNotebook().pages(spec)
    assert [page.kind for page in pages] == ["cover", "lined", "lined"]
    assert len(pages) == 1 + spec.lined_sheets

    cover = pages[0].components[0]
    assert isinstance(cover, CoverTitle)
    assert cover.cta_dest == spec.dest_for_lined_pad(1)
    assert cover.display_title == "Lined"
    assert cover.specs_lead == ""

    plotter = RecordingPlotter()
    LinedNotebook().plot(spec, plotter)
    texts = [op[2] for op in plotter.ops if op[0] == "text"]
    assert cover.display_title in texts
    assert cover.cta_dest in plotter.links()
    assert "Year Book" not in texts
    assert not any("monday weeks" in str(t).lower() for t in texts)
    assert pages[1].dest == spec.dest_for_lined_pad(1)
    assert pages[2].dest == spec.dest_for_lined_pad(2)
    first = pages[1].components[0]
    assert isinstance(first, LinedPad)
    assert first.sheet == 1
    assert first.sheets == 2
    assert spec.year_dest not in {page.dest for page in pages}
    assert all(page.nav == () for page in pages[1:])


def test_press_selects_lined_notebook_from_toml(tmp_path: Path):
    spec = Spec.from_path(Path("examples/lined-notebook.toml"))
    assert spec.book == "lined-notebook"
    assert spec.lined_sheets == 12
    assert spec.device == "supernote-nomad"
    assert spec.title == "Lined"
    assert spec.outline is True
    assert book_for(spec.book) is LinedNotebook

    out = tmp_path / "lined-notebook.pdf"
    press(spec, out)
    dests = {str(key).lstrip("/") for key in (PdfReader(out).named_destinations or {})}
    assert "cover" in dests
    assert spec.dest_for_lined_pad(1) in dests
    assert spec.dest_for_lined_pad(12) in dests
    assert spec.year_dest not in dests
    assert spec.projects_index_dest not in dests
    assert spec.cover_dest in dests
    assert len(PdfReader(out).pages) == 1 + spec.lined_sheets

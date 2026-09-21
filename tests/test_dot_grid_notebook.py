from pathlib import Path

from pypdf import PdfReader

from parch.books import DotGridNotebook, book_for
from parch.components import CoverTitle, DotGridPad
from parch.plotter import RecordingPlotter
from parch.press import press
from parch.spec import Spec


def test_dot_grid_notebook_is_cover_then_clone_dot_pages():
    spec = Spec(book="dot-grid-notebook", dotgrid_sheets=2, title="Dot grid")
    pages = DotGridNotebook().pages(spec)
    assert [page.kind for page in pages] == ["cover", "dotgrid", "dotgrid"]
    assert len(pages) == 1 + spec.dotgrid_sheets

    cover = pages[0].components[0]
    assert isinstance(cover, CoverTitle)
    assert cover.cta_dest == spec.dest_for_dotgrid_pad(1)
    assert cover.display_title == "Dot grid"
    assert cover.specs_lead == ""

    plotter = RecordingPlotter()
    DotGridNotebook().plot(spec, plotter)
    texts = [op[2] for op in plotter.ops if op[0] == "text"]
    assert cover.display_title in texts
    assert cover.cta_dest in plotter.links()
    assert "Year Book" not in texts
    assert not any("monday weeks" in str(t).lower() for t in texts)
    assert pages[1].dest == spec.dest_for_dotgrid_pad(1)
    assert pages[2].dest == spec.dest_for_dotgrid_pad(2)
    first = pages[1].components[0]
    assert isinstance(first, DotGridPad)
    assert first.sheet == 1
    assert first.sheets == 2
    assert spec.year_dest not in {page.dest for page in pages}
    assert all(page.nav == () for page in pages[1:])


def test_press_selects_dot_grid_notebook_from_toml(tmp_path: Path):
    spec = Spec.from_path(Path("examples/dotgrid-notebook.toml"))
    assert spec.book == "dot-grid-notebook"
    assert spec.dotgrid_sheets == 12
    assert spec.device == "supernote-nomad"
    assert spec.title == "Dot grid"
    assert spec.outline is True
    assert book_for(spec.book) is DotGridNotebook

    out = tmp_path / "dotgrid-notebook.pdf"
    press(spec, out)
    dests = {str(key).lstrip("/") for key in (PdfReader(out).named_destinations or {})}
    assert "cover" in dests
    assert spec.dest_for_dotgrid_pad(1) in dests
    assert spec.dest_for_dotgrid_pad(12) in dests
    assert spec.year_dest not in dests
    assert spec.projects_index_dest not in dests
    assert spec.cover_dest in dests
    assert len(PdfReader(out).pages) == 1 + spec.dotgrid_sheets

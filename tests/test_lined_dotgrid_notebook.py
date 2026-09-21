from pathlib import Path

from pypdf import PdfReader

from parch.books import LinedDotGridNotebook, book_for
from parch.books.lined_dotgrid_notebook import alternating_lined_dotgrid_pages
from parch.components import CoverTitle, DotGridPad, LinedPad
from parch.plotter import RecordingPlotter
from parch.press import press
from parch.spec import Spec


def test_alternation_is_lined_then_dotgrid_and_reuses_helpers():
    spec = Spec(
        book="lined-dotgrid-notebook",
        lined_sheets=2,
        dotgrid_sheets=2,
    )
    pages = alternating_lined_dotgrid_pages(spec)
    assert [page.kind for page in pages] == ["lined", "dotgrid", "lined", "dotgrid"]
    assert [page.dest for page in pages] == [
        spec.dest_for_lined_pad(1),
        spec.dest_for_dotgrid_pad(1),
        spec.dest_for_lined_pad(2),
        spec.dest_for_dotgrid_pad(2),
    ]
    assert isinstance(pages[0].components[0], LinedPad)
    assert isinstance(pages[1].components[0], DotGridPad)


def test_alternation_appends_leftover_when_counts_differ():
    spec = Spec(
        book="lined-dotgrid-notebook",
        lined_sheets=3,
        dotgrid_sheets=1,
    )
    pages = alternating_lined_dotgrid_pages(spec)
    assert [page.kind for page in pages] == ["lined", "dotgrid", "lined", "lined"]
    assert pages[-1].dest == spec.dest_for_lined_pad(3)


def test_lined_dotgrid_notebook_is_cover_then_alternating_pages():
    spec = Spec(
        book="lined-dotgrid-notebook",
        lined_sheets=2,
        dotgrid_sheets=2,
        title="Lined / Dot grid",
    )
    pages = LinedDotGridNotebook().pages(spec)
    assert [page.kind for page in pages] == [
        "cover",
        "lined",
        "dotgrid",
        "lined",
        "dotgrid",
    ]
    assert len(pages) == 1 + spec.lined_sheets + spec.dotgrid_sheets

    cover = pages[0].components[0]
    assert isinstance(cover, CoverTitle)
    assert cover.cta_dest == spec.dest_for_lined_pad(1)
    assert cover.display_title == "Lined / Dot grid"
    assert cover.specs_lead == ""

    plotter = RecordingPlotter()
    LinedDotGridNotebook().plot(spec, plotter)
    texts = [op[2] for op in plotter.ops if op[0] == "text"]
    assert cover.display_title in texts
    assert cover.cta_dest in plotter.links()
    assert "Year Book" not in texts
    assert spec.year_dest not in {page.dest for page in pages}
    assert all(page.nav == () for page in pages[1:])


def test_press_selects_lined_dotgrid_notebook_from_toml(tmp_path: Path):
    spec = Spec.from_path(Path("examples/lined-dotgrid-notebook.toml"))
    assert spec.book == "lined-dotgrid-notebook"
    assert spec.lined_sheets == 6
    assert spec.dotgrid_sheets == 6
    assert spec.device == "supernote-nomad"
    assert spec.title == "Lined / Dot grid"
    assert spec.outline is True
    assert book_for(spec.book) is LinedDotGridNotebook

    out = tmp_path / "lined-dotgrid-notebook.pdf"
    press(spec, out)
    dests = {str(key).lstrip("/") for key in (PdfReader(out).named_destinations or {})}
    assert "cover" in dests
    assert spec.dest_for_lined_pad(1) in dests
    assert spec.dest_for_lined_pad(6) in dests
    assert spec.dest_for_dotgrid_pad(1) in dests
    assert spec.dest_for_dotgrid_pad(6) in dests
    assert spec.year_dest not in dests
    assert spec.cover_dest in dests
    assert len(PdfReader(out).pages) == 1 + spec.lined_sheets + spec.dotgrid_sheets

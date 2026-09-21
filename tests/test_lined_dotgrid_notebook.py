from pathlib import Path

from pypdf import PdfReader

from parch.books import LinedDotGridNotebook, book_for
from parch.components import CoverTitle
from parch.plotter import RecordingPlotter
from parch.press import press
from parch.spec import Spec


def test_notebook_is_cover_then_one_duplex_section():
    spec = Spec(
        book="lined-dotgrid-mix-notebook",
        lined_dotgrid_sheets=2,
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
    assert len(pages) == 1 + 2 * spec.lined_dotgrid_sheets

    cover = pages[0].components[0]
    assert isinstance(cover, CoverTitle)
    assert cover.cta_dest == spec.dest_for_duplex_pair_pad("lined-dotgrid", 1, "front")
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


def test_flip_only_cover_lands_on_dotgrid_front():
    spec = Spec(book="lined-dotgrid-mix-notebook", dotgrid_lined_sheets=1)
    pages = LinedDotGridNotebook().pages(spec)
    assert [page.kind for page in pages] == ["cover", "dotgrid", "lined"]
    cover = pages[0].components[0]
    assert cover.cta_dest == spec.dest_for_duplex_pair_pad("dotgrid-lined", 1, "front")


def test_press_selects_mix_notebook_from_toml(tmp_path: Path):
    spec = Spec.from_path(Path("examples/lined-dotgrid-mix-notebook.toml"))
    assert spec.book == "lined-dotgrid-mix-notebook"
    assert spec.lined_dotgrid_sheets == 6
    assert spec.dotgrid_lined_sheets == 0
    assert spec.lined_sheets == 0
    assert spec.dotgrid_sheets == 0
    assert spec.device == "supernote-nomad"
    assert spec.title == "Lined / Dot grid"
    assert spec.outline is True
    assert book_for(spec.book) is LinedDotGridNotebook

    out = tmp_path / "lined-dotgrid-mix-notebook.pdf"
    press(spec, out)
    dests = {str(key).lstrip("/") for key in (PdfReader(out).named_destinations or {})}
    assert "cover" in dests
    assert spec.dest_for_duplex_pair_pad("lined-dotgrid", 1, "front") in dests
    assert spec.dest_for_duplex_pair_pad("lined-dotgrid", 6, "back") in dests
    assert spec.year_dest not in dests
    assert spec.cover_dest in dests
    assert len(PdfReader(out).pages) == 1 + 2 * spec.lined_dotgrid_sheets

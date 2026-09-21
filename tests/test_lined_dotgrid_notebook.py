from pathlib import Path

from pypdf import PdfReader

from parch.books import LinedDotGridNotebook, book_for
from parch.components import CoverTitle, DotGridPad, LinedPad
from parch.plotter import RecordingPlotter
from parch.press import press
from parch.sections.lined_dot_grid import duplex_pair_pages
from parch.spec import Spec


def test_duplex_pair_pages_zips_by_sheet_when_both_types():
    spec = Spec(
        book="lined-dot-grid-mix-notebook",
        lined_dot_grid_sheets=2,
        dot_grid_lined_sheets=1,
    )
    pages = duplex_pair_pages(spec)
    assert [page.kind for page in pages] == [
        "lined",
        "dotgrid",
        "dotgrid",
        "lined",
        "lined",
        "dotgrid",
    ]
    assert [page.dest for page in pages] == [
        spec.dest_for_duplex_pair_pad("lined-dot-grid", 1, "front"),
        spec.dest_for_duplex_pair_pad("lined-dot-grid", 1, "back"),
        spec.dest_for_duplex_pair_pad("dot-grid-lined", 1, "front"),
        spec.dest_for_duplex_pair_pad("dot-grid-lined", 1, "back"),
        spec.dest_for_duplex_pair_pad("lined-dot-grid", 2, "front"),
        spec.dest_for_duplex_pair_pad("lined-dot-grid", 2, "back"),
    ]
    assert isinstance(pages[0].components[0], LinedPad)
    assert isinstance(pages[2].components[0], DotGridPad)


def test_duplex_pair_pages_either_type_alone():
    lined_front = Spec(book="lined-dot-grid-mix-notebook", lined_dot_grid_sheets=2)
    assert [page.kind for page in duplex_pair_pages(lined_front)] == [
        "lined",
        "dotgrid",
        "lined",
        "dotgrid",
    ]
    flipped = Spec(book="lined-dot-grid-mix-notebook", dot_grid_lined_sheets=1)
    assert [page.kind for page in duplex_pair_pages(flipped)] == ["dotgrid", "lined"]


def test_notebook_zips_both_types_after_cover():
    spec = Spec(
        book="lined-dot-grid-mix-notebook",
        lined_dot_grid_sheets=1,
        dot_grid_lined_sheets=1,
    )
    pages = LinedDotGridNotebook().pages(spec)
    assert [page.kind for page in pages] == [
        "cover",
        "lined",
        "dotgrid",
        "dotgrid",
        "lined",
    ]
    assert pages[1].dest == spec.dest_for_duplex_pair_pad("lined-dot-grid", 1, "front")
    assert pages[3].dest == spec.dest_for_duplex_pair_pad("dot-grid-lined", 1, "front")


def test_notebook_is_cover_then_duplex_pairs():
    spec = Spec(
        book="lined-dot-grid-mix-notebook",
        lined_dot_grid_sheets=2,
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
    assert len(pages) == 1 + 2 * spec.lined_dot_grid_sheets

    cover = pages[0].components[0]
    assert isinstance(cover, CoverTitle)
    assert cover.cta_dest == spec.dest_for_duplex_pair_pad("lined-dot-grid", 1, "front")
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
    spec = Spec(book="lined-dot-grid-mix-notebook", dot_grid_lined_sheets=1)
    cover = LinedDotGridNotebook().pages(spec)[0].components[0]
    assert cover.cta_dest == spec.dest_for_duplex_pair_pad("dot-grid-lined", 1, "front")


def test_alias_lined_dotgrid_notebook_is_the_mix_book():
    spec = Spec(book="lined-dotgrid-notebook", lined_dot_grid_sheets=1)
    assert spec.book == "lined-dot-grid-mix-notebook"
    assert book_for("lined-dotgrid-notebook") is LinedDotGridNotebook
    assert book_for("lined-dot-grid-mix-notebook") is LinedDotGridNotebook


def test_press_selects_mix_notebook_from_toml(tmp_path: Path):
    spec = Spec.from_path(Path("examples/lined-dot-grid-mix-notebook.toml"))
    assert spec.book == "lined-dot-grid-mix-notebook"
    assert spec.lined_dot_grid_sheets == 6
    assert spec.dot_grid_lined_sheets == 0
    assert spec.lined_sheets == 0
    assert spec.dotgrid_sheets == 0
    assert spec.device == "supernote-nomad"
    assert spec.title == "Lined / Dot grid"
    assert spec.outline is True
    assert book_for(spec.book) is LinedDotGridNotebook

    out = tmp_path / "lined-dot-grid-mix-notebook.pdf"
    press(spec, out)
    dests = {str(key).lstrip("/") for key in (PdfReader(out).named_destinations or {})}
    assert "cover" in dests
    assert spec.dest_for_duplex_pair_pad("lined-dot-grid", 1, "front") in dests
    assert spec.dest_for_duplex_pair_pad("lined-dot-grid", 6, "back") in dests
    assert spec.year_dest not in dests
    assert spec.cover_dest in dests
    assert len(PdfReader(out).pages) == 1 + 2 * spec.lined_dot_grid_sheets

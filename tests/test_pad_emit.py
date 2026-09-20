"""P8: sealed emit table — press walks (predicate, section_factory) rows."""

from pathlib import Path

from pypdf import PdfReader

from parch.plotter import RecordingPlotter
from parch.press import _PAD_EMIT, _emit_pad_pages, press
from parch.sections.engineering import EngineeringPadSection
from parch.sections.steno import StenoPadSection
from parch.spec import Spec


def _named_dests(reader: PdfReader) -> set[str]:
    raw = reader.named_destinations or {}
    return {str(key).lstrip("/") for key in raw}


def test_emit_table_is_sealed_engineering_then_steno():
    assert isinstance(_PAD_EMIT, tuple)
    assert len(_PAD_EMIT) == 2
    assert _PAD_EMIT[0].section_factory is EngineeringPadSection
    assert _PAD_EMIT[1].section_factory is StenoPadSection
    both = Spec(engineering_sheets=1, steno_sheets=1)
    assert _PAD_EMIT[0].predicate(both)
    assert _PAD_EMIT[1].predicate(both)
    empty = Spec()
    assert not _PAD_EMIT[0].predicate(empty)
    assert not _PAD_EMIT[1].predicate(empty)


def test_emit_walk_fires_both_sheet_counts():
    spec = Spec(engineering_sheets=1, steno_sheets=1)
    pages = _emit_pad_pages(spec)
    assert [page.kind for page in pages] == [
        "engineering_front",
        "engineering_back",
        "steno",
    ]
    assert [page.dest for page in pages] == [
        spec.dest_for_engineering_pad(1, "front"),
        spec.dest_for_engineering_pad(1, "back"),
        spec.dest_for_steno_pad(1),
    ]


def test_emit_walk_skips_zero_counts():
    assert _emit_pad_pages(Spec()) == []
    engineering = _emit_pad_pages(Spec(engineering_sheets=1))
    assert [page.kind for page in engineering] == [
        "engineering_front",
        "engineering_back",
    ]
    steno = _emit_pad_pages(Spec(steno_sheets=2))
    assert [page.kind for page in steno] == ["steno", "steno"]


def test_spec_from_mapping_accepts_both_pad_tables():
    spec = Spec.from_mapping({"engineering": {"sheets": 1}, "steno": {"sheets": 2}})
    assert spec.engineering_sheets == 1
    assert spec.steno_sheets == 2
    assert spec.book == "year-planner"


def test_example_pads_toml_is_both_counts_no_array_table():
    text = Path("examples/pads.toml").read_text(encoding="utf-8")
    assert "[[pads]]" not in text
    spec = Spec.from_path(Path("examples/pads.toml"))
    assert spec.engineering_sheets == 1
    assert spec.steno_sheets == 1
    assert spec.book == "year-planner"
    assert spec.title == "Pads"


def test_press_both_pads_is_engineering_then_steno(tmp_path: Path):
    spec = Spec(engineering_sheets=1, steno_sheets=1)
    plotter = RecordingPlotter()
    press(spec, tmp_path / "pads.pdf", plotter=plotter)
    assert plotter.dests() == [
        spec.dest_for_engineering_pad(1, "front"),
        spec.dest_for_engineering_pad(1, "back"),
        spec.dest_for_steno_pad(1),
    ]
    assert spec.cover_dest not in plotter.dests()
    assert spec.year_dest not in plotter.dests()


def test_press_both_pads_pdf_has_three_no_cover_pages(tmp_path: Path):
    spec = Spec.from_path(Path("examples/pads.toml"))
    out = tmp_path / "pads.pdf"
    press(spec, out)
    reader = PdfReader(out)
    assert len(reader.pages) == 3
    dests = _named_dests(reader)
    assert spec.dest_for_engineering_pad(1, "front") in dests
    assert spec.dest_for_engineering_pad(1, "back") in dests
    assert spec.dest_for_steno_pad(1) in dests
    assert spec.cover_dest not in dests
    assert spec.year_dest not in dests


def test_press_both_pads_skips_engineering_notebook_cover(tmp_path: Path):
    spec = Spec(
        book="engineering-notebook",
        engineering_sheets=1,
        steno_sheets=1,
    )
    plotter = RecordingPlotter()
    press(spec, tmp_path / "notebook-pads.pdf", plotter=plotter)
    assert plotter.dests() == [
        spec.dest_for_engineering_pad(1, "front"),
        spec.dest_for_engineering_pad(1, "back"),
        spec.dest_for_steno_pad(1),
    ]
    assert spec.cover_dest not in plotter.dests()


def test_press_both_pads_two_steno_sheets(tmp_path: Path):
    spec = Spec(engineering_sheets=1, steno_sheets=2)
    plotter = RecordingPlotter()
    press(spec, tmp_path / "pads.pdf", plotter=plotter)
    assert plotter.dests() == [
        spec.dest_for_engineering_pad(1, "front"),
        spec.dest_for_engineering_pad(1, "back"),
        spec.dest_for_steno_pad(1),
        spec.dest_for_steno_pad(2),
    ]

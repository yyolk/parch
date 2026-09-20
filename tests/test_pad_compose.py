"""P5: both pad sheet counts compose in press() without a Book."""

from pathlib import Path

from pypdf import PdfReader

from parch.plotter import RecordingPlotter
from parch.press import press
from parch.spec import Spec


def _named_dests(reader: PdfReader) -> set[str]:
    raw = reader.named_destinations or {}
    return {str(key).lstrip("/") for key in raw}


def test_spec_from_mapping_accepts_both_pad_tables():
    spec = Spec.from_mapping(
        {"engineering": {"sheets": 1}, "steno": {"sheets": 2}}
    )
    assert spec.engineering_sheets == 1
    assert spec.steno_sheets == 2
    assert spec.book == "year-planner"


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
    spec = Spec(engineering_sheets=1, steno_sheets=1)
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

"""P9: both pad sheet counts stitch as exclusive temp PDFs."""

from pathlib import Path

from pypdf import PdfReader

from parch.press import press
from parch.spec import Spec


def _named_dests(reader: PdfReader) -> dict[str, object]:
    raw = reader.named_destinations or {}
    return {str(key).lstrip("/"): dest for key, dest in raw.items()}


def _dest_page(reader: PdfReader, name: str) -> int:
    dests = _named_dests(reader)
    return reader.get_destination_page_number(dests[name])


def test_spec_from_mapping_accepts_both_pad_tables():
    spec = Spec.from_mapping({"engineering": {"sheets": 1}, "steno": {"sheets": 2}})
    assert spec.engineering_sheets == 1
    assert spec.steno_sheets == 2
    assert spec.book == "year-planner"


def test_press_both_pads_pdf_page_count_and_dests(tmp_path: Path):
    spec = Spec(engineering_sheets=1, steno_sheets=1)
    out = tmp_path / "pads.pdf"
    press(spec, out)
    reader = PdfReader(out)
    assert len(reader.pages) == 3
    dests = _named_dests(reader)
    front = spec.dest_for_engineering_pad(1, "front")
    back = spec.dest_for_engineering_pad(1, "back")
    steno = spec.dest_for_steno_pad(1)
    assert front in dests
    assert back in dests
    assert steno in dests
    assert spec.cover_dest not in dests
    assert spec.year_dest not in dests
    assert _dest_page(reader, front) == 0
    assert _dest_page(reader, back) == 1
    assert _dest_page(reader, steno) == 2


def test_press_both_pads_two_steno_sheets_shifts_dest_pages(tmp_path: Path):
    spec = Spec(engineering_sheets=1, steno_sheets=2)
    out = tmp_path / "pads.pdf"
    press(spec, out)
    reader = PdfReader(out)
    assert len(reader.pages) == 4
    dests = _named_dests(reader)
    assert spec.dest_for_engineering_pad(1, "front") in dests
    assert spec.dest_for_engineering_pad(1, "back") in dests
    assert spec.dest_for_steno_pad(1) in dests
    assert spec.dest_for_steno_pad(2) in dests
    assert _dest_page(reader, spec.dest_for_steno_pad(1)) == 2
    assert _dest_page(reader, spec.dest_for_steno_pad(2)) == 3


def test_press_example_pads_toml_stitches_three_pages(tmp_path: Path):
    spec = Spec.from_path(Path("examples/pads.toml"))
    out = tmp_path / "pads.pdf"
    press(spec, out)
    reader = PdfReader(out)
    assert spec.engineering_sheets == 1
    assert spec.steno_sheets == 1
    assert len(reader.pages) == 3
    dests = _named_dests(reader)
    assert spec.dest_for_engineering_pad(1, "front") in dests
    assert spec.dest_for_steno_pad(1) in dests
    assert spec.cover_dest not in dests


def test_press_both_pads_outline_stays_empty(tmp_path: Path):
    spec = Spec(engineering_sheets=1, steno_sheets=1, outline=True)
    out = tmp_path / "pads-outline.pdf"
    press(spec, out)
    reader = PdfReader(out)
    assert reader.outline == []
    dests = _named_dests(reader)
    assert spec.dest_for_engineering_pad(1, "front") in dests
    assert spec.dest_for_steno_pad(1) in dests


def test_press_engineering_notebook_plus_steno_skips_cover(tmp_path: Path):
    spec = Spec(
        book="engineering-notebook",
        engineering_sheets=1,
        steno_sheets=1,
    )
    out = tmp_path / "notebook-pads.pdf"
    press(spec, out)
    reader = PdfReader(out)
    dests = _named_dests(reader)
    assert spec.cover_dest not in dests
    assert spec.dest_for_engineering_pad(1, "front") in dests
    assert spec.dest_for_steno_pad(1) in dests
    assert len(reader.pages) == 3
    assert _dest_page(reader, spec.dest_for_engineering_pad(1, "front")) == 0
    assert _dest_page(reader, spec.dest_for_steno_pad(1)) == 2

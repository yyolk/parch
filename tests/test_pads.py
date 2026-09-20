"""P6: pad_pages concatenates engineering then steno; press plots that list."""

from pathlib import Path

from pypdf import PdfReader

from parch.pads import pad_pages
from parch.press import press
from parch.spec import Spec


def _named_dests(reader: PdfReader) -> set[str]:
    raw = reader.named_destinations or {}
    return {str(key).lstrip("/") for key in raw}


def test_pad_pages_empty_when_no_sheets():
    assert pad_pages(Spec()) == []


def test_pad_pages_concatenates_engineering_then_steno():
    spec = Spec(engineering_sheets=1, steno_sheets=2)
    pages = pad_pages(spec)
    assert [page.kind for page in pages] == [
        "engineering_front",
        "engineering_back",
        "steno",
        "steno",
    ]
    assert [page.dest for page in pages] == [
        spec.dest_for_engineering_pad(1, "front"),
        spec.dest_for_engineering_pad(1, "back"),
        spec.dest_for_steno_pad(1),
        spec.dest_for_steno_pad(2),
    ]
    assert all(page.nav == () for page in pages)


def test_pad_pages_is_just_engineering_when_steno_zero():
    spec = Spec(engineering_sheets=1)
    pages = pad_pages(spec)
    assert [page.kind for page in pages] == ["engineering_front", "engineering_back"]


def test_pad_pages_is_just_steno_when_engineering_zero():
    spec = Spec(steno_sheets=1)
    pages = pad_pages(spec)
    assert [page.kind for page in pages] == ["steno"]


def test_spec_from_mapping_accepts_both_pad_tables():
    spec = Spec.from_mapping({"engineering": {"sheets": 1}, "steno": {"sheets": 2}})
    assert spec.engineering_sheets == 1
    assert spec.steno_sheets == 2
    assert spec.book == "year-planner"


def test_example_pads_toml_is_both_counts():
    spec = Spec.from_path(Path("examples/pads.toml"))
    assert spec.engineering_sheets == 1
    assert spec.steno_sheets == 1
    assert spec.book == "year-planner"
    assert spec.device == "supernote-nomad"
    assert "[[pads]]" not in Path("examples/pads.toml").read_text()


def test_press_both_pads_one_pdf_no_cover(tmp_path: Path):
    spec = Spec.from_path(Path("examples/pads.toml"))
    out = tmp_path / "pads.pdf"
    press(spec, out)
    reader = PdfReader(out)
    assert len(reader.pages) == 3
    dests = _named_dests(reader)
    assert spec.dest_for_engineering_pad(1, "front") in dests
    assert spec.dest_for_engineering_pad(1, "back") in dests
    assert spec.dest_for_steno_pad(1) in dests
    assert spec.year_dest not in dests
    assert spec.cover_dest not in dests


def test_press_both_pads_skips_engineering_notebook_cover(tmp_path: Path):
    spec = Spec(
        book="engineering-notebook",
        engineering_sheets=1,
        steno_sheets=1,
    )
    out = tmp_path / "notebook-pads.pdf"
    press(spec, out)
    dests = _named_dests(PdfReader(out))
    assert spec.dest_for_engineering_pad(1, "front") in dests
    assert spec.dest_for_steno_pad(1) in dests
    assert spec.cover_dest not in dests

from pathlib import Path

from pypdf import PdfReader

from parch.press import press
from parch.sections.pads import PadBundleSection
from parch.spec import Spec


def test_bundle_empty_when_no_sheets():
    assert PadBundleSection(Spec()).pages() == []


def test_bundle_concatenates_engineering_then_steno():
    spec = Spec(engineering_sheets=1, steno_sheets=2)
    pages = PadBundleSection(spec).pages()
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


def test_bundle_is_just_engineering_when_steno_zero():
    spec = Spec(engineering_sheets=1)
    pages = PadBundleSection(spec).pages()
    assert [page.kind for page in pages] == ["engineering_front", "engineering_back"]


def test_bundle_is_just_steno_when_engineering_zero():
    spec = Spec(steno_sheets=1)
    pages = PadBundleSection(spec).pages()
    assert [page.kind for page in pages] == ["steno"]


def test_press_both_pads_one_pdf_no_cover(tmp_path: Path):
    spec = Spec(engineering_sheets=1, steno_sheets=1)
    out = tmp_path / "pads.pdf"
    press(spec, out)
    reader = PdfReader(out)
    assert len(reader.pages) == 3
    dests = {str(key).lstrip("/") for key in (reader.named_destinations or {})}
    assert spec.dest_for_engineering_pad(1, "front") in dests
    assert spec.dest_for_engineering_pad(1, "back") in dests
    assert spec.dest_for_steno_pad(1) in dests
    assert spec.year_dest not in dests
    assert spec.cover_dest not in dests

from pathlib import Path

import pytest
from pypdf import PdfReader

from parch import ConfigError
from parch.books import EngineeringNotebook, book_for
from parch.fonts.ramp import EffectiveRamp
from parch.pads import Composed, Engineering, Steno, compose, pad_for
from parch.plotter import RecordingPlotter
from parch.press import press
from parch.spec import Spec

MM_PER_INCH = 25.4


def _pt(mm: float) -> float:
    return mm / MM_PER_INCH * 72.0


def _named_dests(reader: PdfReader) -> set[str]:
    raw = reader.named_destinations or {}
    return {str(key).lstrip("/") for key in raw}


def test_press_routes_pad_only_through_compose():
    source = Path("src/parch/press.py").read_text(encoding="utf-8")
    assert "from parch.pads import compose" in source
    assert "StenoPadSection" not in source
    assert "EngineeringPadSection" not in source
    assert "if spec.steno_sheets > 0:" not in source


def test_pad_for_selects_engineering_or_steno():
    assert pad_for("engineering") is Engineering
    assert pad_for("steno") is Steno
    with pytest.raises(ConfigError, match="pad must be engineering or steno"):
        pad_for("steno-notebook")


def test_compose_none_keeps_book_press():
    assert compose(Spec()) is None
    notebook = Spec(book="engineering-notebook", engineering_sheets=1)
    assert compose(notebook) is None
    assert book_for(notebook.book) is EngineeringNotebook


def test_compose_single_kind_is_that_pad():
    eng = Spec(engineering_sheets=1)
    steno = Spec(steno_sheets=2)
    assert type(compose(eng)) is Engineering
    assert type(compose(steno)) is Steno
    assert [page.kind for page in compose(eng).pages(eng)] == [
        "engineering_front",
        "engineering_back",
    ]
    assert [page.kind for page in compose(steno).pages(steno)] == ["steno", "steno"]


def test_compose_stacks_engineering_then_steno():
    spec = Spec(engineering_sheets=1, steno_sheets=2)
    pad = compose(spec)
    assert type(pad) is Composed
    pages = pad.pages(spec)
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
    assert spec.cover_dest not in {page.dest for page in pages}
    assert all(page.nav == () for page in pages)


def test_compose_preserves_steno_on_non_planner_book():
    spec = Spec(book="projects-notebook", steno_sheets=1)
    assert type(compose(spec)) is Steno


def test_composed_plot_walks_one_ledger():
    spec = Spec(engineering_sheets=1, steno_sheets=1)
    plotter = RecordingPlotter()
    compose(spec, ramp=EffectiveRamp()).plot(spec, plotter)
    assert plotter.dests() == [
        spec.dest_for_engineering_pad(1, "front"),
        spec.dest_for_engineering_pad(1, "back"),
        spec.dest_for_steno_pad(1),
    ]
    assert spec.cover_dest not in plotter.dests()
    assert spec.year_dest not in plotter.dests()


def test_press_mixed_pad_is_one_pdf_without_cover(tmp_path: Path):
    spec = Spec.from_path(Path("examples/pad.toml"))
    assert spec.engineering_sheets == 1
    assert spec.steno_sheets == 1
    assert spec.book == "year-planner"
    assert spec.device == "supernote-nomad"
    out = tmp_path / "pad.pdf"
    press(spec, out)
    reader = PdfReader(out)
    assert len(reader.pages) == 3
    dests = _named_dests(reader)
    assert spec.dest_for_engineering_pad(1, "front") in dests
    assert spec.dest_for_engineering_pad(1, "back") in dests
    assert spec.dest_for_steno_pad(1) in dests
    assert spec.cover_dest not in dests
    assert spec.year_dest not in dests
    page = reader.pages[0]
    assert float(page.mediabox.width) == pytest.approx(_pt(118.87), abs=0.6)
    assert float(page.mediabox.height) == pytest.approx(_pt(158.5), abs=0.6)


def test_press_mixed_pad_scribe_geometry(tmp_path: Path):
    spec = Spec(device="kindle-scribe", engineering_sheets=1, steno_sheets=1)
    out = tmp_path / "pad-scribe.pdf"
    press(spec, out)
    page = PdfReader(out).pages[0]
    assert float(page.mediabox.width) == pytest.approx(_pt(157.48), abs=0.6)
    assert float(page.mediabox.height) == pytest.approx(_pt(209.97), abs=0.6)
    dests = _named_dests(PdfReader(out))
    assert spec.dest_for_engineering_pad(1, "front") in dests
    assert spec.dest_for_steno_pad(1) in dests
    assert spec.cover_dest not in dests

from pathlib import Path

import pytest
from pypdf import PdfReader

from parch import ConfigError
from parch.books import (
    EngineeringNotebook,
    Pad,
    ProjectsNotebook,
    YearPlanner,
    book_for,
)
from parch.components import EngineeringPad, StenoPad
from parch.plotter import RecordingPlotter
from parch.press import press
from parch.spec import Spec


def test_pad_book_emits_both_sections_without_cover():
    spec = Spec(book="pad", engineering_sheets=1, steno_sheets=2)
    pages = Pad().pages(spec)
    assert [page.kind for page in pages] == [
        "engineering_front",
        "engineering_back",
        "steno",
        "steno",
    ]
    assert "cover" not in {page.kind for page in pages}
    assert spec.cover_dest not in {page.dest for page in pages}
    assert spec.year_dest not in {page.dest for page in pages}
    assert all(page.nav == () for page in pages)

    assert pages[0].dest == spec.dest_for_engineering_pad(1, "front")
    assert isinstance(pages[0].components[0], EngineeringPad)
    assert pages[0].components[0].face == "front"
    assert pages[1].components[0].face == "back"
    assert pages[2].dest == spec.dest_for_steno_pad(1)
    assert isinstance(pages[2].components[0], StenoPad)
    assert pages[2].components[0].sheet == 1
    assert pages[3].dest == spec.dest_for_steno_pad(2)


def test_pad_book_one_kind_only():
    eng = Pad().pages(Spec(book="pad", engineering_sheets=1))
    assert [page.kind for page in eng] == ["engineering_front", "engineering_back"]
    steno = Pad().pages(Spec(book="pad", steno_sheets=1))
    assert [page.kind for page in steno] == ["steno"]


def test_book_for_selects_pad():
    spec = Spec(book="pad", engineering_sheets=1, steno_sheets=1)
    assert spec.book == "pad"
    assert book_for(spec.book) is Pad
    assert book_for("year-planner") is YearPlanner
    assert book_for("projects-notebook") is ProjectsNotebook
    assert book_for("engineering-notebook") is EngineeringNotebook


def test_spec_pad_allows_both_sheet_counts():
    spec = Spec(book="pad", engineering_sheets=2, steno_sheets=3)
    assert spec.engineering_sheets == 2
    assert spec.steno_sheets == 3
    mapped = Spec.from_mapping(
        {
            "book": "pad",
            "engineering": {"sheets": 2},
            "steno": {"sheets": 3},
        }
    )
    assert mapped.book == "pad"
    assert mapped.engineering_sheets == 2
    assert mapped.steno_sheets == 3
    with pytest.raises(ConfigError, match="cannot both be set"):
        Spec(steno_sheets=1, engineering_sheets=1)
    with pytest.raises(ConfigError, match="pad requires"):
        Spec(book="pad")
    with pytest.raises(ConfigError, match="book must be"):
        Spec.from_mapping({"book": "pads"})


def test_press_pad_book_skips_short_circuits(tmp_path: Path):
    spec = Spec(book="pad", engineering_sheets=1, steno_sheets=1)
    out = tmp_path / "pads.pdf"
    press(spec, out)
    reader = PdfReader(out)
    assert len(reader.pages) == 3
    dests = {str(key).lstrip("/") for key in (reader.named_destinations or {})}
    assert spec.dest_for_engineering_pad(1, "front") in dests
    assert spec.dest_for_engineering_pad(1, "back") in dests
    assert spec.dest_for_steno_pad(1) in dests
    assert spec.cover_dest not in dests
    assert spec.year_dest not in dests


def test_press_selects_pad_from_toml(tmp_path: Path):
    spec = Spec.from_path(Path("examples/pads.toml"))
    assert spec.book == "pad"
    assert spec.engineering_sheets == 1
    assert spec.steno_sheets == 1
    assert spec.title == "Pads"
    assert book_for(spec.book) is Pad

    out = tmp_path / "pads.toml.pdf"
    press(spec, out)
    dests = {str(key).lstrip("/") for key in (PdfReader(out).named_destinations or {})}
    assert spec.dest_for_engineering_pad(1, "front") in dests
    assert spec.dest_for_steno_pad(1) in dests
    assert "cover" not in dests
    assert len(PdfReader(out).pages) == 3


def test_pad_book_outline_empty_when_enabled():
    spec = Spec(book="pad", engineering_sheets=1, steno_sheets=1, outline=True)
    plotter = RecordingPlotter()
    Pad().plot(spec, plotter)
    assert plotter.outlines() == []
    dests = plotter.dests()
    assert spec.dest_for_engineering_pad(1, "front") in dests
    assert spec.dest_for_steno_pad(1) in dests
    assert spec.cover_dest not in dests


def test_pad_book_plot_ticks_each_page(monkeypatch):
    ticks: list[tuple[int, int, str]] = []
    monkeypatch.setattr(
        "parch.books.protocol.render_progress",
        lambda i, n, label: ticks.append((i, n, label)),
    )
    spec = Spec(book="pad", engineering_sheets=1, steno_sheets=1)
    book = Pad()
    pages = book.pages(spec)
    book.plot(spec, RecordingPlotter())
    assert [tick[0] for tick in ticks] == list(range(1, len(pages) + 1))
    assert all(tick[1] == len(pages) for tick in ticks)
    assert [tick[2] for tick in ticks] == [
        "engineering_front",
        "engineering_back",
        "steno",
    ]

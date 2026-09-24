"""Duplex lined/dotgrid pad: front+back per sheet. Pad-only, no cover."""

from pathlib import Path

import pytest
from pypdf import PdfReader

from parch import ConfigError
from parch.components import DotGridPad, LinedPad
from parch.devices.registry import NOMAD
from parch.layouts.planner import PlannerLayout
from parch.layouts.planner.painters import CLONE_DOT, RULE, RULE_C
from parch.plotter import RecordingPlotter
from parch.press import press
from parch.sections.lined_dotgrid import LinedDotGridPadSection
from parch.spec import Spec


def _rules(plotter: RecordingPlotter) -> list[tuple]:
    return [
        op
        for op in plotter.ops
        if op[0] == "line"
        and op[5] == pytest.approx(RULE)
        and op[6] == pytest.approx(RULE_C)
        and op[2] == pytest.approx(op[4])
    ]


def _dots(plotter: RecordingPlotter) -> list[tuple]:
    return [
        op
        for op in plotter.ops
        if op[0] == "rect"
        and op[3]
        and not op[2]
        and op[1].w == pytest.approx(CLONE_DOT)
        and op[1].h == pytest.approx(CLONE_DOT)
    ]


def test_section_emits_duplex_pair_per_sheet_lined_front():
    spec = Spec(lined_dotgrid_sheets=2)
    pages = LinedDotGridPadSection(spec).pages()
    assert [page.kind for page in pages] == ["lined", "dotgrid", "lined", "dotgrid"]
    assert [page.dest for page in pages] == [
        "lined-dotgrid-2026-01-front",
        "lined-dotgrid-2026-01-back",
        "lined-dotgrid-2026-02-front",
        "lined-dotgrid-2026-02-back",
    ]
    front = pages[0].components[0]
    back = pages[1].components[0]
    assert isinstance(front, LinedPad)
    assert isinstance(back, DotGridPad)
    assert front.sheet == back.sheet == 1
    assert front.sheets == back.sheets == 2
    assert pages[0].nav == ()
    assert pages[1].nav == ()


def test_section_emits_flipped_pair_dotgrid_front():
    spec = Spec(dotgrid_lined_sheets=1)
    pages = LinedDotGridPadSection(spec, order="dotgrid-lined").pages()
    assert [page.kind for page in pages] == ["dotgrid", "lined"]
    assert [page.dest for page in pages] == [
        "dotgrid-lined-2026-01-front",
        "dotgrid-lined-2026-01-back",
    ]
    assert isinstance(pages[0].components[0], DotGridPad)
    assert isinstance(pages[1].components[0], LinedPad)


def test_section_empty_when_no_sheets():
    assert LinedDotGridPadSection(Spec()).pages() == []
    assert LinedDotGridPadSection(Spec(), order="dotgrid-lined").pages() == []


def test_spec_duplex_dests_and_toml():
    spec = Spec(lined_dotgrid_sheets=1)
    assert spec.dest_for_duplex_pair_pad("lined-dotgrid", 1, "front") == (
        "lined-dotgrid-2026-01-front"
    )
    assert spec.dest_for_duplex_pair_pad("lined-dotgrid", 1, "back") == (
        "lined-dotgrid-2026-01-back"
    )
    example = Spec.from_path(Path("examples/lined-dotgrid-pad.toml"))
    assert example.lined_dotgrid_sheets == 1
    assert example.dotgrid_lined_sheets == 0
    assert example.lined_sheets == 0
    assert example.dotgrid_sheets == 0
    assert example.book == "year-planner"
    assert "year =" not in Path("examples/lined-dotgrid-pad.toml").read_text()
    flipped = Spec.from_path(Path("examples/dotgrid-lined-pad.toml"))
    assert flipped.dotgrid_lined_sheets == 1
    assert flipped.lined_dotgrid_sheets == 0
    assert Spec.from_mapping({"lined-dotgrid": {"sheets": 2}}).lined_dotgrid_sheets == 2
    assert Spec.from_mapping({"dotgrid-lined": {"sheets": 3}}).dotgrid_lined_sheets == 3
    with pytest.raises(ConfigError, match="lined_dotgrid_sheets must be 0–100"):
        Spec(lined_dotgrid_sheets=101)
    with pytest.raises(ConfigError, match="dotgrid_lined_sheets must be 0–100"):
        Spec(dotgrid_lined_sheets=101)
    with pytest.raises(ConfigError, match="front or back"):
        spec.dest_for_duplex_pair_pad("lined-dotgrid", 1, "verso")
    with pytest.raises(ConfigError, match="lined-dotgrid or dotgrid-lined"):
        spec.dest_for_duplex_pair_pad("not-a-pair-order", 1, "front")
    with pytest.raises(ConfigError, match="lined_dotgrid_sheets must be >= 1"):
        Spec().dest_for_duplex_pair_pad("lined-dotgrid", 1, "front")
    with pytest.raises(ConfigError, match="duplex pair sheet out of range"):
        spec.dest_for_duplex_pair_pad("lined-dotgrid", 2, "front")


def test_cannot_set_both_duplex_orders():
    with pytest.raises(
        ConfigError,
        match="cannot set both lined_dotgrid_sheets and dotgrid_lined_sheets",
    ):
        Spec(lined_dotgrid_sheets=1, dotgrid_lined_sheets=1)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"engineering_sheets": 1},
        {"steno_sheets": 1},
        {"dotgrid_sheets": 1},
        {"perspective_sheets": 1},
    ],
)
def test_year_planner_rejects_duplex_mixed_with_other_pads(kwargs):
    with pytest.raises(
        ConfigError,
        match="year-planner cannot mix duplex lined/dotgrid sheets with other",
    ):
        Spec(lined_dotgrid_sheets=1, **kwargs)


def test_layout_front_is_lined_back_is_dotgrid():
    spec = Spec(lined_dotgrid_sheets=1)
    front, back = LinedDotGridPadSection(spec).pages()
    front_ink = RecordingPlotter()
    back_ink = RecordingPlotter()
    PlannerLayout().paint(front, front_ink, NOMAD)
    PlannerLayout().paint(back, back_ink, NOMAD)
    assert _rules(front_ink)
    assert not _dots(front_ink)
    assert _dots(back_ink)
    assert not _rules(back_ink)


def test_layout_flipped_front_is_dotgrid_back_is_lined():
    spec = Spec(dotgrid_lined_sheets=1)
    front, back = LinedDotGridPadSection(spec, order="dotgrid-lined").pages()
    front_ink = RecordingPlotter()
    back_ink = RecordingPlotter()
    PlannerLayout().paint(front, front_ink, NOMAD)
    PlannerLayout().paint(back, back_ink, NOMAD)
    assert _dots(front_ink)
    assert not _rules(front_ink)
    assert _rules(back_ink)
    assert not _dots(back_ink)


def test_press_example_toml_is_duplex_pair_without_cover(tmp_path: Path):
    out = tmp_path / "lined-dotgrid-pad.pdf"
    spec = Spec.from_path(Path("examples/lined-dotgrid-pad.toml"))
    press(spec, out)
    reader = PdfReader(out)
    assert len(reader.pages) == 2
    dests = {str(key).lstrip("/") for key in (reader.named_destinations or {})}
    assert spec.dest_for_duplex_pair_pad("lined-dotgrid", 1, "front") in dests
    assert spec.dest_for_duplex_pair_pad("lined-dotgrid", 1, "back") in dests
    assert spec.year_dest not in dests
    assert spec.cover_dest not in dests


def test_press_records_lined_front_then_dotgrid_back(tmp_path: Path):
    spec = Spec(lined_dotgrid_sheets=1)
    plotter = RecordingPlotter()
    press(spec, tmp_path / "pair.pdf", plotter=plotter)
    assert plotter.dests() == [
        spec.dest_for_duplex_pair_pad("lined-dotgrid", 1, "front"),
        spec.dest_for_duplex_pair_pad("lined-dotgrid", 1, "back"),
    ]
    assert spec.cover_dest not in plotter.dests()


def test_press_records_flipped_order(tmp_path: Path):
    spec = Spec(dotgrid_lined_sheets=1)
    plotter = RecordingPlotter()
    press(spec, tmp_path / "flipped.pdf", plotter=plotter)
    assert plotter.dests() == [
        spec.dest_for_duplex_pair_pad("dotgrid-lined", 1, "front"),
        spec.dest_for_duplex_pair_pad("dotgrid-lined", 1, "back"),
    ]

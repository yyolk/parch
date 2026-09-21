"""Pad sheet counts compose in press() without a Book or cover notebook."""

from pathlib import Path

import pytest

from parch import ConfigError
from parch.plotter import RecordingPlotter
from parch.press import press
from parch.spec import Spec


def test_spec_from_mapping_accepts_both_pad_tables():
    spec = Spec.from_mapping({"engineering": {"sheets": 1}, "steno": {"sheets": 2}})
    assert spec.engineering_sheets == 1
    assert spec.steno_sheets == 2
    assert spec.book == "year-planner"
    example = Spec.from_path(Path("examples/pads.toml"))
    assert example.engineering_sheets == 1
    assert example.steno_sheets == 1
    assert example.book == "year-planner"
    assert "year =" not in Path("examples/pads.toml").read_text()


def test_spec_from_mapping_accepts_dot_as_third_pad_table():
    spec = Spec.from_mapping(
        {
            "engineering": {"sheets": 1},
            "steno": {"sheets": 2},
            "dot": {"sheets": 3},
        }
    )
    assert spec.engineering_sheets == 1
    assert spec.steno_sheets == 2
    assert spec.dot_sheets == 3
    assert spec.book == "year-planner"
    example = Spec.from_path(Path("examples/dot-grid-pad.toml"))
    assert example.dot_sheets == 2
    assert example.book == "year-planner"


def test_engineering_notebook_rejects_steno_sheets():
    with pytest.raises(
        ConfigError, match="engineering-notebook cannot set steno_sheets"
    ):
        Spec(book="engineering-notebook", engineering_sheets=1, steno_sheets=1)


def test_engineering_notebook_rejects_dot_sheets():
    with pytest.raises(ConfigError, match="engineering-notebook cannot set dot_sheets"):
        Spec(book="engineering-notebook", engineering_sheets=1, dot_sheets=1)


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


def test_press_three_pads_is_engineering_then_steno_then_dot(tmp_path: Path):
    spec = Spec(engineering_sheets=1, steno_sheets=1, dot_sheets=2)
    plotter = RecordingPlotter()
    press(spec, tmp_path / "pads.pdf", plotter=plotter)
    assert plotter.dests() == [
        spec.dest_for_engineering_pad(1, "front"),
        spec.dest_for_engineering_pad(1, "back"),
        spec.dest_for_steno_pad(1),
        spec.dest_for_dot_pad(1),
        spec.dest_for_dot_pad(2),
    ]
    assert spec.cover_dest not in plotter.dests()
    assert spec.year_dest not in plotter.dests()

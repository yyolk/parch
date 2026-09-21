"""P5: both pad sheet counts compose in press() without a Book."""

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


def test_engineering_notebook_rejects_steno_sheets():
    with pytest.raises(
        ConfigError, match="engineering-notebook cannot set steno_sheets"
    ):
        Spec(book="engineering-notebook", engineering_sheets=1, steno_sheets=1)


def test_engineering_notebook_rejects_dotgrid_sheets():
    with pytest.raises(
        ConfigError, match="engineering-notebook cannot set dotgrid_sheets"
    ):
        Spec(book="engineering-notebook", engineering_sheets=1, dotgrid_sheets=1)


def test_dotgrid_notebook_rejects_engineering_sheets():
    with pytest.raises(
        ConfigError, match="dotgrid-notebook cannot set engineering_sheets"
    ):
        Spec(book="dotgrid-notebook", dotgrid_sheets=1, engineering_sheets=1)


def test_dotgrid_notebook_rejects_steno_sheets():
    with pytest.raises(ConfigError, match="dotgrid-notebook cannot set steno_sheets"):
        Spec(book="dotgrid-notebook", dotgrid_sheets=1, steno_sheets=1)


def test_engineering_notebook_rejects_lined_sheets():
    with pytest.raises(
        ConfigError, match="engineering-notebook cannot set lined_sheets"
    ):
        Spec(book="engineering-notebook", engineering_sheets=1, lined_sheets=1)


def test_dotgrid_notebook_rejects_lined_sheets():
    with pytest.raises(ConfigError, match="dotgrid-notebook cannot set lined_sheets"):
        Spec(book="dotgrid-notebook", dotgrid_sheets=1, lined_sheets=1)


def test_lined_notebook_rejects_engineering_sheets():
    with pytest.raises(
        ConfigError, match="lined-notebook cannot set engineering_sheets"
    ):
        Spec(book="lined-notebook", lined_sheets=1, engineering_sheets=1)


def test_lined_notebook_rejects_steno_sheets():
    with pytest.raises(ConfigError, match="lined-notebook cannot set steno_sheets"):
        Spec(book="lined-notebook", lined_sheets=1, steno_sheets=1)


def test_lined_notebook_rejects_dotgrid_sheets():
    with pytest.raises(ConfigError, match="lined-notebook cannot set dotgrid_sheets"):
        Spec(book="lined-notebook", lined_sheets=1, dotgrid_sheets=1)


def test_lined_dotgrid_notebook_rejects_engineering_sheets():
    with pytest.raises(
        ConfigError, match="lined-dotgrid-mix-notebook cannot set engineering_sheets"
    ):
        Spec(
            book="lined-dotgrid-mix-notebook",
            lined_dotgrid_sheets=1,
            engineering_sheets=1,
        )


def test_lined_dotgrid_notebook_rejects_steno_sheets():
    with pytest.raises(
        ConfigError, match="lined-dotgrid-mix-notebook cannot set steno_sheets"
    ):
        Spec(
            book="lined-dotgrid-mix-notebook",
            lined_dotgrid_sheets=1,
            steno_sheets=1,
        )


def test_lined_dotgrid_mix_notebook_rejects_single_sided_pad_sheets():
    with pytest.raises(
        ConfigError, match="lined-dotgrid-mix-notebook cannot set lined_sheets"
    ):
        Spec(book="lined-dotgrid-mix-notebook", lined_dotgrid_sheets=1, lined_sheets=1)
    with pytest.raises(
        ConfigError, match="lined-dotgrid-mix-notebook cannot set dotgrid_sheets"
    ):
        Spec(
            book="lined-dotgrid-mix-notebook",
            lined_dotgrid_sheets=1,
            dotgrid_sheets=1,
        )


def test_lined_dotgrid_mix_notebook_accepts_exactly_one_duplex_type():
    either = Spec(book="lined-dotgrid-mix-notebook", lined_dotgrid_sheets=1)
    assert either.lined_dotgrid_sheets == 1
    flipped = Spec(book="lined-dotgrid-mix-notebook", dotgrid_lined_sheets=2)
    assert flipped.dotgrid_lined_sheets == 2
    with pytest.raises(
        ConfigError,
        match="cannot set both lined_dotgrid_sheets and dotgrid_lined_sheets",
    ):
        Spec(
            book="lined-dotgrid-mix-notebook",
            lined_dotgrid_sheets=1,
            dotgrid_lined_sheets=1,
        )


def test_engineering_notebook_rejects_duplex_pair_sheets():
    with pytest.raises(
        ConfigError, match="engineering-notebook cannot set lined_dotgrid_sheets"
    ):
        Spec(book="engineering-notebook", engineering_sheets=1, lined_dotgrid_sheets=1)


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

"""P7: leftover sheet ints compose; ``pads`` is order-only."""

import tomllib
from pathlib import Path

import pytest
from pypdf import PdfReader

from parch import ConfigError
from parch.plotter import RecordingPlotter
from parch.press import pages_from_pads, press
from parch.spec import Spec


def _named_dests(reader: PdfReader) -> set[str]:
    raw = reader.named_destinations or {}
    return {str(key).lstrip("/") for key in raw}


def test_omit_pads_is_engineering_then_steno():
    spec = Spec(engineering_sheets=1, steno_sheets=1)
    assert spec.pads == ("engineering", "steno")
    assert Spec.from_mapping(
        {"engineering": {"sheets": 1}, "steno": {"sheets": 1}}
    ).pads == ("engineering", "steno")
    example = Spec.from_path(Path("examples/pads.toml"))
    assert example.pads == ("engineering", "steno")
    assert example.engineering_sheets == 1
    assert example.steno_sheets == 1
    assert "pads" not in tomllib.loads(Path("examples/pads.toml").read_text())


def test_pads_list_is_order_only():
    spec = Spec.from_mapping(
        {
            "pads": ["steno", "engineering"],
            "engineering": {"sheets": 1},
            "steno": {"sheets": 2},
        }
    )
    assert spec.pads == ("steno", "engineering")
    assert spec.engineering_sheets == 1
    assert spec.steno_sheets == 2
    prefix = Spec(engineering_sheets=1, steno_sheets=1, pads=("steno",))
    assert prefix.pads == ("steno", "engineering")


def test_pads_closed_list():
    with pytest.raises(ConfigError, match="pads must be a list"):
        Spec.from_mapping({"pads": "engineering"})
    with pytest.raises(ConfigError, match="pads must not be empty"):
        Spec.from_mapping({"pads": []})
    with pytest.raises(ConfigError, match="pads entries must be strings"):
        Spec.from_mapping({"pads": [1]})
    with pytest.raises(ConfigError, match="pad kind must be engineering or steno"):
        Spec.from_mapping({"pads": ["legal"]})
    with pytest.raises(ConfigError, match="duplicate pad kind steno"):
        Spec.from_mapping({"pads": ["steno", "steno"]})
    with pytest.raises(ConfigError, match="pads entries must be strings"):
        Spec.from_mapping({"pads": [{"kind": "engineering", "sheets": 1}]})


def test_pages_from_pads_reads_leftover_sheet_tables():
    default = Spec(engineering_sheets=1, steno_sheets=1)
    assert [page.kind for page in pages_from_pads(default)] == [
        "engineering_front",
        "engineering_back",
        "steno",
    ]
    reversed_order = Spec(
        engineering_sheets=1, steno_sheets=1, pads=("steno", "engineering")
    )
    pages = pages_from_pads(reversed_order)
    assert [page.kind for page in pages] == [
        "steno",
        "engineering_front",
        "engineering_back",
    ]
    assert [page.dest for page in pages] == [
        reversed_order.dest_for_steno_pad(1),
        reversed_order.dest_for_engineering_pad(1, "front"),
        reversed_order.dest_for_engineering_pad(1, "back"),
    ]


def test_press_both_pads_default_order(tmp_path: Path):
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


def test_press_both_pads_reversed_order(tmp_path: Path):
    spec = Spec(engineering_sheets=1, steno_sheets=1, pads=("steno", "engineering"))
    plotter = RecordingPlotter()
    press(spec, tmp_path / "pads.pdf", plotter=plotter)
    assert plotter.dests() == [
        spec.dest_for_steno_pad(1),
        spec.dest_for_engineering_pad(1, "front"),
        spec.dest_for_engineering_pad(1, "back"),
    ]


def test_press_example_toml_is_three_no_cover_pages(tmp_path: Path):
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
        pads=("steno", "engineering"),
    )
    plotter = RecordingPlotter()
    press(spec, tmp_path / "notebook-pads.pdf", plotter=plotter)
    assert plotter.dests() == [
        spec.dest_for_steno_pad(1),
        spec.dest_for_engineering_pad(1, "front"),
        spec.dest_for_engineering_pad(1, "back"),
    ]
    assert spec.cover_dest not in plotter.dests()


def test_to_toml_roundtrips_pads_order():
    spec = Spec(engineering_sheets=1, steno_sheets=2, pads=("steno", "engineering"))
    loaded = Spec.from_mapping(spec.to_mapping())
    assert loaded == spec
    dumped = spec.to_toml()
    assert 'pads = ["steno", "engineering"]' in dumped
    assert Spec.from_mapping(tomllib.loads(dumped)) == spec

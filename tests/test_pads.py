from pathlib import Path

import pytest
from pypdf import PdfReader

from parch import ConfigError
from parch.plotter import RecordingPlotter
from parch.press import pages_from_pad_rows, press
from parch.spec import PadRow, Spec


def test_example_pads_table_is_ordered_engineering_then_steno():
    spec = Spec.from_path(Path("examples/pads.toml"))
    assert spec.pads == (
        PadRow("engineering", 1),
        PadRow("steno", 1),
    )
    assert spec.engineering_sheets == 1
    assert spec.steno_sheets == 1
    assert spec.book == "year-planner"
    assert spec.pad_rows() == spec.pads
    assert "year =" not in Path("examples/pads.toml").read_text()
    assert spec.dest_for_engineering_pad(1, "front") == "engineering-2026-01-front"
    assert spec.dest_for_steno_pad(1) == "steno-2026-01"


def test_inline_pads_array_of_tables():
    spec = Spec.from_mapping(
        {
            "pads": [
                {"kind": "steno", "sheets": 2},
                {"kind": "engineering", "sheets": 1},
            ]
        }
    )
    assert spec.pads == (PadRow("steno", 2), PadRow("engineering", 1))
    assert spec.steno_sheets == 2
    assert spec.engineering_sheets == 1
    assert spec.pad_rows()[0].kind == "steno"


def test_leftover_exclusive_ints_still_rejected():
    with pytest.raises(ConfigError, match="cannot both be set"):
        Spec(steno_sheets=1, engineering_sheets=1)
    with pytest.raises(ConfigError, match="cannot both be set"):
        Spec.from_mapping({"engineering": {"sheets": 1}, "steno": {"sheets": 1}})


def test_leftover_ints_synthesize_one_pad_row():
    assert Spec(engineering_sheets=2).pad_rows() == (PadRow("engineering", 2),)
    assert Spec(steno_sheets=3).pad_rows() == (PadRow("steno", 3),)
    assert Spec().pad_rows() == ()
    notebook = Spec(book="engineering-notebook", engineering_sheets=1)
    assert notebook.pad_rows() == ()


def test_pads_cannot_combine_with_leftover_tables():
    with pytest.raises(ConfigError, match="cannot be combined"):
        Spec.from_mapping(
            {
                "pads": [{"kind": "engineering", "sheets": 1}],
                "engineering": {"sheets": 1},
            }
        )
    with pytest.raises(ConfigError, match="cannot be combined"):
        Spec.from_mapping(
            {
                "pads": [{"kind": "steno", "sheets": 1}],
                "steno_sheets": 1,
            }
        )


def test_pads_closed_table_and_sheet_counts():
    with pytest.raises(ConfigError, match="pads must be an array"):
        Spec.from_mapping({"pads": {"kind": "engineering", "sheets": 1}})
    with pytest.raises(ConfigError, match="must be a table"):
        Spec.from_mapping({"pads": ["engineering"]})
    with pytest.raises(ConfigError, match="unknown pads key"):
        Spec.from_mapping({"pads": [{"kind": "engineering", "sheets": 1, "holes": 2}]})
    with pytest.raises(ConfigError, match="needs kind"):
        Spec.from_mapping({"pads": [{"sheets": 1}]})
    with pytest.raises(ConfigError, match="needs sheets"):
        Spec.from_mapping({"pads": [{"kind": "engineering"}]})
    with pytest.raises(ConfigError, match="kind must be engineering or steno"):
        Spec.from_mapping({"pads": [{"kind": "legal", "sheets": 1}]})
    with pytest.raises(ConfigError, match="must be an integer"):
        Spec.from_mapping({"pads": [{"kind": "steno", "sheets": True}]})
    with pytest.raises(ConfigError, match="sheets must be 1–100"):
        Spec(pads=(PadRow("engineering", 0),))
    with pytest.raises(ConfigError, match='pads requires book = "year-planner"'):
        Spec(
            book="engineering-notebook",
            pads=(PadRow("engineering", 1),),
        )


def test_pages_from_pad_rows_follows_table_order():
    spec = Spec(pads=(PadRow("steno", 1), PadRow("engineering", 1)))
    pages = pages_from_pad_rows(spec, spec.pad_rows())
    assert [page.kind for page in pages] == [
        "steno",
        "engineering_front",
        "engineering_back",
    ]
    assert [page.dest for page in pages] == [
        spec.dest_for_steno_pad(1),
        spec.dest_for_engineering_pad(1, "front"),
        spec.dest_for_engineering_pad(1, "back"),
    ]


def test_duplicate_kind_rows_keep_unique_dests():
    spec = Spec(
        pads=(
            PadRow("engineering", 1),
            PadRow("steno", 1),
            PadRow("engineering", 1),
        )
    )
    assert spec.engineering_sheets == 2
    pages = pages_from_pad_rows(spec, spec.pads)
    assert [page.kind for page in pages] == [
        "engineering_front",
        "engineering_back",
        "steno",
        "engineering_front",
        "engineering_back",
    ]
    dests = [page.dest for page in pages]
    assert dests == [
        spec.dest_for_engineering_pad(1, "front"),
        spec.dest_for_engineering_pad(1, "back"),
        spec.dest_for_steno_pad(1),
        spec.dest_for_engineering_pad(2, "front"),
        spec.dest_for_engineering_pad(2, "back"),
    ]
    assert len(dests) == len(set(dests))


def test_press_example_toml_composes_three_no_cover_pages(tmp_path: Path):
    out = tmp_path / "pads.pdf"
    spec = Spec.from_path(Path("examples/pads.toml"))
    press(spec, out)
    reader = PdfReader(out)
    assert len(reader.pages) == 3
    dests = {str(key).lstrip("/") for key in (reader.named_destinations or {})}
    assert spec.dest_for_engineering_pad(1, "front") in dests
    assert spec.dest_for_engineering_pad(1, "back") in dests
    assert spec.dest_for_steno_pad(1) in dests
    assert spec.cover_dest not in dests
    assert spec.year_dest not in dests


def test_press_pads_ticks_each_composed_page(tmp_path: Path, monkeypatch):
    ticks: list[tuple[int, int, str]] = []
    monkeypatch.setattr(
        "parch.books.protocol.render_progress",
        lambda i, n, label: ticks.append((i, n, label)),
    )
    spec = Spec(pads=(PadRow("engineering", 1), PadRow("steno", 1)))
    press(spec, tmp_path / "pads.pdf", plotter=RecordingPlotter())
    assert ticks == [
        (1, 3, "engineering_front"),
        (2, 3, "engineering_back"),
        (3, 3, "steno"),
    ]

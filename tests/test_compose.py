"""Composable TOML — sealed starter ⊕ overlay / extends / include."""

from pathlib import Path

import pytest

from parch import ConfigError
from parch.fonts import OVERLAY_SCHEMA_VERSION, TypeOverlay, TypePatch
from parch.press import _load_spec, main
from parch.spec import Spec, compose_table, merge_tables

_NOMAD = Path("examples/nomad.toml")
_LOCAL = Path("examples/nomad-local.toml")


def test_merge_tables_deep_and_list_replace():
    base = {
        "year": 2026,
        "title": "Year planner",
        "daily": {"notes_pages": 1, "priority_rows": 6},
        "months": [1, 2, 3],
    }
    overlay = {
        "title": "Local overlay",
        "daily": {"notes_pages": 0},
        "months": [7, 8],
    }
    merged = merge_tables(base, overlay)
    assert merged["year"] == 2026
    assert merged["title"] == "Local overlay"
    assert merged["daily"] == {"notes_pages": 0, "priority_rows": 6}
    assert merged["months"] == [7, 8]
    assert base["daily"]["notes_pages"] == 1
    assert overlay["daily"]["notes_pages"] == 0


def test_merge_tables_drops_compose_keys():
    merged = merge_tables(
        {"extends": "a.toml", "year": 2026},
        {"include": "b.toml", "title": "x"},
    )
    assert merged == {"year": 2026, "title": "x"}


def test_merge_tables_month_replaces_inherited_months():
    merged = merge_tables({"months": {"from": 1, "to": 12}, "year": 2026}, {"month": 1})
    assert merged == {"year": 2026, "month": 1}
    back = merge_tables({"month": 1, "year": 2026}, {"months": [3, 5]})
    assert back == {"year": 2026, "months": [3, 5]}


def test_merge_tables_favorites_bool_replaces_pages():
    merged = merge_tables({"favorites_pages": 0}, {"favorites": True})
    assert merged == {"favorites": True}


def test_from_mapping_rejects_unresolved_compose_keys():
    with pytest.raises(ConfigError, match="extends is only valid in a TOML file"):
        Spec.from_mapping({"extends": "nomad.toml", "year": 2026})
    with pytest.raises(ConfigError, match="include is only valid in a TOML file"):
        Spec.from_mapping({"include": "nomad.toml"})


def test_compose_identity_on_stock_nomad():
    direct = compose_table(_NOMAD)
    assert "extends" not in direct
    assert "include" not in direct
    stock = Spec.from_path(_NOMAD)
    assert stock.year == 2026
    assert stock.months == tuple(range(1, 13))
    assert stock.notes_pages == 1
    assert stock.title == "Year planner"
    assert stock.outline is True
    assert stock.project_index_pages == 3
    assert stock.type_overlay == TypeOverlay()


def test_example_local_extends_sealed_starter():
    spec = Spec.from_path(_LOCAL)
    assert spec.year == 2026
    assert spec.device == "supernote-nomad"
    assert spec.months == (1,)
    assert spec.title == "Local overlay"
    assert spec.notes_pages == 0
    assert spec.outline is True
    assert spec.project_index_pages == 3
    assert spec.schedule_hours == tuple(range(7, 17))
    assert spec.type_overlay == TypeOverlay(
        schema_version=OVERLAY_SCHEMA_VERSION,
        chrome=TypePatch(size=9.6, weight="bold"),
    )
    stock = Spec.from_path(_NOMAD)
    assert stock.months == tuple(range(1, 13))
    assert stock.title == "Year planner"
    assert stock.notes_pages == 1
    assert stock.type_overlay == TypeOverlay()


def test_cli_overlay_flag_matches_extends(tmp_path: Path):
    overlay = tmp_path / "delta.toml"
    overlay.write_text(
        'month = 1\ntitle = "CLI overlay"\n[daily]\nnotes_pages = 0\n',
        encoding="utf-8",
    )
    via_flag = _load_spec(
        str(_NOMAD),
        year=None,
        month=None,
        overlays=[str(overlay)],
    )
    assert via_flag.months == (1,)
    assert via_flag.title == "CLI overlay"
    assert via_flag.notes_pages == 0
    assert via_flag.outline is True
    assert via_flag.project_index_pages == 3


def test_cli_repeatable_overlays_later_win(tmp_path: Path):
    first = tmp_path / "a.toml"
    first.write_text('month = 1\ntitle = "first"\n', encoding="utf-8")
    second = tmp_path / "b.toml"
    second.write_text('title = "second"\n', encoding="utf-8")
    spec = _load_spec(
        str(_NOMAD),
        year=None,
        month=None,
        overlays=[str(first), str(second)],
    )
    assert spec.months == (1,)
    assert spec.title == "second"
    assert spec.outline is True


def test_cli_year_flag_wins_after_overlay(tmp_path: Path):
    overlay = tmp_path / "year.toml"
    overlay.write_text("year = 2027\nmonth = 1\n", encoding="utf-8")
    spec = _load_spec(
        str(_NOMAD),
        year=2028,
        month=None,
        overlays=[str(overlay)],
    )
    assert spec.year == 2028
    assert spec.months == (1,)


def test_cli_overlay_on_device_token(tmp_path: Path):
    overlay = tmp_path / "jan.toml"
    overlay.write_text("month = 1\nnotes_pages = 0\n", encoding="utf-8")
    spec = _load_spec(
        "kindle-scribe",
        year=None,
        month=None,
        overlays=[str(overlay)],
    )
    assert spec.device == "kindle-scribe"
    assert spec.months == (1,)
    assert spec.notes_pages == 0


def test_cli_overlay_missing_file():
    with pytest.raises(ConfigError, match="overlay file not found"):
        _load_spec(str(_NOMAD), year=None, month=None, overlays=["missing-local.toml"])


def test_include_string_and_list(tmp_path: Path):
    a = tmp_path / "a.toml"
    a.write_text('year = 2026\ntitle = "A"\n', encoding="utf-8")
    b = tmp_path / "b.toml"
    b.write_text('title = "B"\nmonth = 1\n', encoding="utf-8")
    via_string = tmp_path / "via-string.toml"
    via_string.write_text(
        'include = "a.toml"\ndevice = "kindle-scribe"\n', encoding="utf-8"
    )
    via_list = tmp_path / "via-list.toml"
    via_list.write_text(
        'include = ["a.toml", "b.toml"]\ndevice = "kindle-scribe"\n',
        encoding="utf-8",
    )
    stringed = Spec.from_path(via_string)
    assert stringed.year == 2026
    assert stringed.title == "A"
    assert stringed.device == "kindle-scribe"
    assert stringed.months == tuple(range(1, 13))
    listed = Spec.from_path(via_list)
    assert listed.year == 2026
    assert listed.title == "B"
    assert listed.months == (1,)
    assert listed.device == "kindle-scribe"


def test_include_relative_to_origin(tmp_path: Path):
    nested = tmp_path / "starters"
    nested.mkdir()
    (nested / "base.toml").write_text(
        'year = 2026\ntitle = "Nested"\nmonths = { from = 1, to = 12 }\n',
        encoding="utf-8",
    )
    child = tmp_path / "job.toml"
    child.write_text('extends = "starters/base.toml"\nmonth = 3\n', encoding="utf-8")
    spec = Spec.from_path(child)
    assert spec.title == "Nested"
    assert spec.months == (3,)


def test_include_missing_is_loud(tmp_path: Path):
    orphan = tmp_path / "orphan.toml"
    orphan.write_text('extends = "nope.toml"\n', encoding="utf-8")
    with pytest.raises(ConfigError, match="include not found: nope.toml"):
        Spec.from_path(orphan)


def test_include_and_extends_together_fail(tmp_path: Path):
    both = tmp_path / "both.toml"
    both.write_text('extends = "a.toml"\ninclude = "b.toml"\n', encoding="utf-8")
    with pytest.raises(ConfigError, match="use extends or include, not both"):
        Spec.from_path(both)


def test_extends_rejects_array(tmp_path: Path):
    bad = tmp_path / "bad.toml"
    bad.write_text('extends = ["a.toml", "b.toml"]\n', encoding="utf-8")
    with pytest.raises(ConfigError, match="extends must be a single path string"):
        Spec.from_path(bad)


def test_include_empty_array_fails(tmp_path: Path):
    empty = tmp_path / "empty.toml"
    empty.write_text("include = []\n", encoding="utf-8")
    with pytest.raises(ConfigError, match="include must not be empty"):
        Spec.from_path(empty)


def test_include_cycle(tmp_path: Path):
    one = tmp_path / "one.toml"
    two = tmp_path / "two.toml"
    one.write_text('extends = "two.toml"\n', encoding="utf-8")
    two.write_text('extends = "one.toml"\n', encoding="utf-8")
    with pytest.raises(ConfigError, match="TOML include cycle"):
        Spec.from_path(one)


def test_include_self_cycle(tmp_path: Path):
    loop = tmp_path / "loop.toml"
    loop.write_text('include = "loop.toml"\n', encoding="utf-8")
    with pytest.raises(ConfigError, match="TOML include cycle"):
        Spec.from_path(loop)


def test_cli_press_overlay_and_extends_match(tmp_path: Path, monkeypatch):
    seen: list[Spec] = []

    def fake_press(spec, output, **_kwargs):
        seen.append(spec)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(b"%PDF-1.4\n")
        return output

    monkeypatch.setattr("parch.press.press", fake_press)
    out_flag = tmp_path / "flag.pdf"
    assert (
        main(
            [
                "press",
                str(_NOMAD),
                "--overlay",
                str(_LOCAL),
                "-o",
                str(out_flag),
            ]
        )
        == 0
    )
    out_extends = tmp_path / "extends.pdf"
    assert main(["press", str(_LOCAL), "-o", str(out_extends)]) == 0
    assert len(seen) == 2
    assert seen[0].months == (1,)
    assert seen[0].title == "Local overlay"
    assert seen[0].notes_pages == 0
    assert seen[0].type_overlay.chrome == TypePatch(size=9.6, weight="bold")
    assert seen[1] == seen[0]


def test_cli_overlay_missing_exits_2(tmp_path: Path, capsys):
    out = tmp_path / "nope.pdf"
    assert (
        main(
            [
                "press",
                str(_NOMAD),
                "--overlay",
                str(tmp_path / "missing.toml"),
                "-o",
                str(out),
            ]
        )
        == 2
    )
    assert "overlay file not found" in capsys.readouterr().err
    assert not out.exists()


def test_cli_help_mentions_overlay(capsys):
    with pytest.raises(SystemExit) as exc:
        main(["--help"])
    assert exc.value.code == 0
    help_text = capsys.readouterr().out
    assert "--overlay" in help_text
    assert "extends" in help_text
    assert "include" in help_text


def test_press_example_local_is_january(tmp_path: Path):
    from pypdf import PdfReader

    out = tmp_path / "local.pdf"
    assert main(["press", str(_LOCAL), "-o", str(out)]) == 0
    dests = {str(key).lstrip("/") for key in (PdfReader(out).named_destinations or {})}
    assert "2026-01-01" in dests
    assert "2026-01-31" in dests
    assert "2026-02-01" not in dests
    assert out.is_file() and out.stat().st_size > 0

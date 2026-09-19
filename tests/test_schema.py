import json
import tomllib
from pathlib import Path

import pytest

from parch import ConfigError
from parch.devices.registry import _KNOWN
from parch.fonts.ramp import _WEIGHTS, OVERLAY_SCHEMA_VERSION, TYPE_STEPS
from parch.press import main
from parch.schema import (
    SCHEMA_COMMENT,
    SCHEMA_DIRECTIVE,
    SCHEMA_FILENAME,
    dump_schema,
    spec_schema,
    write_init,
    write_schema,
)
from parch.spec import _BOOKS, _WEEK_STARTS, Spec

EXAMPLES = tuple(sorted(Path("examples").glob("*.toml")))


def _properties(node: dict) -> dict:
    props = dict(node.get("properties") or {})
    for alt in node.get("oneOf") or []:
        props.update(_properties(alt))
    return props


def _assert_mapping_documented(data: dict, node: dict, path: str = "$") -> None:
    allowed = _properties(node)
    extra = set(data) - set(allowed)
    assert not extra, f"undocumented keys at {path}: {sorted(extra)}"
    for key, value in data.items():
        child = allowed[key]
        if isinstance(value, dict):
            _assert_mapping_documented(value, child, f"{path}.{key}")


def test_dump_schema_is_draft07_object():
    payload = json.loads(dump_schema())
    assert payload["$schema"] == "http://json-schema.org/draft-07/schema#"
    assert payload["title"] == "parch Spec"
    assert payload["type"] == "object"
    assert payload["additionalProperties"] is False
    assert dump_schema().endswith("\n")


def test_schema_documents_preferred_and_leftover_keys():
    props = spec_schema()["properties"]
    preferred = {
        "year",
        "device",
        "week_start",
        "months",
        "title",
        "book",
        "outline",
        "favorites",
        "my_100",
        "checkoff_365",
        "daily",
        "habits",
        "projects",
        "meetings",
        "tasks",
        "engineering",
        "steno",
        "bujo",
        "typography",
    }
    leftover = {
        "month",
        "notes_pages",
        "habit_columns",
        "habit_rows",
        "priority_rows",
        "project_cards",
        "project_tickets",
        "project_index_pages",
        "meeting_index_rows",
        "task_rows",
        "engineering_sheets",
        "steno_sheets",
        "favorites_pages",
        "daily_notes",
        "$schema",
    }
    assert preferred <= set(props)
    assert leftover <= set(props)
    for name, node in props.items():
        assert node.get("description"), f"{name} needs a description"
        assert node.get("markdownDescription"), f"{name} needs markdownDescription"


def test_schema_enums_match_runtime_closed_sets():
    props = spec_schema()["properties"]
    assert set(props["device"]["enum"]) == set(_KNOWN)
    assert set(props["book"]["enum"]) == set(_BOOKS)
    assert set(props["week_start"]["enum"]) == set(_WEEK_STARTS)
    overlay = props["typography"]["properties"]["overlay"]
    assert overlay["required"] == ["schema_version"]
    assert overlay["properties"]["schema_version"]["const"] == OVERLAY_SCHEMA_VERSION
    assert set(TYPE_STEPS) <= set(overlay["properties"])
    chrome = overlay["properties"]["chrome"]
    assert set(chrome["properties"]["weight"]["enum"]) == set(_WEIGHTS)
    assert chrome["additionalProperties"] is False


def test_example_toml_keys_are_in_schema():
    schema = spec_schema()
    for path in EXAMPLES:
        data = Spec.from_path(path)  # examples must still parse
        assert isinstance(data, Spec)
        table = tomllib.loads(path.read_text(encoding="utf-8"))
        _assert_mapping_documented(table, schema, path.name)


def test_write_schema_file(tmp_path: Path):
    dest = write_schema(tmp_path / "out.json")
    assert dest == tmp_path / "out.json"
    assert json.loads(dest.read_text(encoding="utf-8"))["title"] == "parch Spec"
    nested = write_schema(tmp_path / "dir")
    assert nested == tmp_path / "dir" / SCHEMA_FILENAME


def test_write_init_tiny_toml_with_schema_comment(tmp_path: Path):
    toml_path, schema_path = write_init(tmp_path)
    text = toml_path.read_text(encoding="utf-8")
    assert toml_path.name == "spec.toml"
    assert schema_path.name == SCHEMA_FILENAME
    assert text.startswith(SCHEMA_DIRECTIVE)
    assert SCHEMA_COMMENT in text.splitlines()
    assert '#$ schema = "spec.schema.json"' in text
    spec = Spec.from_path(toml_path)
    assert spec.year == 2026
    assert spec.device == "supernote-nomad"
    assert spec.week_start == "monday"
    assert spec.months == tuple(range(1, 13))
    assert spec.title == "Year planner"
    assert spec.book == "year-planner"


def test_write_init_named_toml(tmp_path: Path):
    dest = tmp_path / "planner.toml"
    toml_path, schema_path = write_init(dest)
    assert toml_path == dest
    assert schema_path == tmp_path / SCHEMA_FILENAME


def test_write_init_refuses_overwrite(tmp_path: Path):
    write_init(tmp_path)
    with pytest.raises(ConfigError, match="refusing to overwrite"):
        write_init(tmp_path)
    toml_path, _schema = write_init(tmp_path, force=True)
    assert toml_path.is_file()


def test_cli_schema_stdout(capsys):
    assert main(["schema"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["title"] == "parch Spec"
    assert "year" in payload["properties"]


def test_cli_schema_output_file(tmp_path: Path, capsys):
    dest = tmp_path / SCHEMA_FILENAME
    assert main(["schema", "-o", str(dest)]) == 0
    assert capsys.readouterr().out.strip() == str(dest)
    assert json.loads(dest.read_text(encoding="utf-8"))["title"] == "parch Spec"


def test_cli_init(tmp_path: Path, capsys, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert main(["init"]) == 0
    out = capsys.readouterr().out.splitlines()
    assert Path(out[0]).name == "spec.toml"
    assert Path(out[1]).name == SCHEMA_FILENAME
    text = Path("spec.toml").read_text(encoding="utf-8")
    assert "#$ schema =" in text
    assert Spec.from_path(Path("spec.toml")).device == "supernote-nomad"


def test_cli_init_refuses_existing(tmp_path: Path, capsys, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert main(["init"]) == 0
    assert main(["init"]) == 2
    assert "refusing to overwrite" in capsys.readouterr().err
    assert main(["init", "--force"]) == 0

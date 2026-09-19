import tomllib
from dataclasses import replace
from datetime import time
from pathlib import Path

from tomlrange import Clock

from parch.init import _STARTER_HEADER, main, starter_toml, write_starter
from parch.press import main as press_main
from parch.spec import Spec


def test_starter_toml_round_trips_to_spec_defaults():
    text = starter_toml()
    loaded = Spec.from_mapping(tomllib.loads(text))
    assert loaded == Spec()
    assert loaded == Spec.from_mapping({})


def test_starter_toml_follows_replaced_spec_fields():
    spec = replace(
        Spec(),
        year=2027,
        device="kindle-scribe",
        week_start="sunday",
        months=(3, 4, 5),
        notes_pages=1,
        habit_columns=8,
        priority_rows=5,
        project_cards=2,
        project_tickets=6,
        project_index_pages=2,
        meeting_index_rows=12,
        task_rows=4,
        outline=True,
        schedule=Clock.parse({"from": time(9, 0), "to": time(17, 0)}),
    )
    loaded = Spec.from_mapping(tomllib.loads(starter_toml(spec)))
    assert loaded.year == 2027
    assert loaded.device == "kindle-scribe"
    assert loaded.week_start == "sunday"
    assert loaded.months == (3, 4, 5)
    assert loaded.notes_pages == 1
    assert loaded.habit_columns == 8
    assert loaded.priority_rows == 5
    assert loaded.project_cards == 2
    assert loaded.project_tickets == 6
    assert loaded.project_index_pages == 2
    assert loaded.meeting_index_rows == 12
    assert loaded.task_rows == 4
    assert loaded.outline is True
    assert loaded.schedule.as_tuple() == (time(9, 0), time(17, 0))


def test_starter_toml_is_shared_serializer():
    """Init is a thin header plus ``Spec.to_toml`` — no private f-string blob."""
    assert starter_toml() == _STARTER_HEADER + Spec().to_toml()
    spec = replace(Spec(), year=2027, months=(1, 3))
    assert starter_toml(spec) == _STARTER_HEADER + spec.to_toml()


def test_starter_toml_has_thin_header_and_live_keys():
    text = starter_toml()
    assert text.startswith("# parch starter")
    spec = Spec()
    assert f"year = {spec.year}" in text
    assert f'device = "{spec.device}"' in text
    assert f"months = {{ from = {spec.months[0]}, to = {spec.months[-1]} }}" in text
    table = spec.schedule.as_table()
    assert (
        f"schedule = {{ from = {table['from'].strftime('%H:%M:%S')}, "
        f"to = {table['to'].strftime('%H:%M:%S')} }}"
    ) in text
    # Shared dump spells optional extras as live keys at Spec() defaults.
    assert "favorites = false" in text
    assert "[engineering]" in text
    assert "[bujo]" in text


def test_starter_toml_emits_list_for_gapped_months():
    text = starter_toml(replace(Spec(), months=(1, 3)))
    assert "months = [1, 3]" in text
    assert Spec.from_mapping(tomllib.loads(text)).months == (1, 3)


def test_starter_module_avoids_questionary():
    source = Path("src/parch/init.py").read_text(encoding="utf-8")
    assert "import questionary" not in source
    assert "from questionary" not in source


def test_starter_module_does_not_reimplement_toml():
    source = Path("src/parch/init.py").read_text(encoding="utf-8")
    assert "def _toml_str" not in source
    assert "def _months_toml" not in source
    assert "spec.to_toml()" in source


def test_cli_init_stdout(capsys):
    assert main([]) == 0
    out = capsys.readouterr().out
    assert Spec.from_mapping(tomllib.loads(out)) == Spec()
    assert out.lstrip().startswith("#")


def test_cli_init_writes_file(tmp_path: Path, capsys):
    dest = tmp_path / "planner.toml"
    assert main(["-o", str(dest)]) == 0
    assert capsys.readouterr().out.strip() == str(dest)
    assert Spec.from_path(dest) == Spec()


def test_cli_init_refuses_existing_file(tmp_path: Path, capsys):
    dest = tmp_path / "planner.toml"
    dest.write_text("year = 1999\n", encoding="utf-8")
    assert main(["-o", str(dest)]) == 2
    assert "exists" in capsys.readouterr().err
    assert dest.read_text(encoding="utf-8") == "year = 1999\n"


def test_cli_init_force_overwrites(tmp_path: Path):
    dest = tmp_path / "planner.toml"
    dest.write_text("year = 1999\n", encoding="utf-8")
    assert main(["-o", str(dest), "--force"]) == 0
    assert Spec.from_path(dest) == Spec()


def test_write_starter_round_trips(tmp_path: Path):
    dest = write_starter(tmp_path / "job.toml")
    assert Spec.from_path(dest) == Spec()


def test_press_verb_dispatches_init(capsys):
    assert press_main(["init"]) == 0
    out = capsys.readouterr().out
    assert Spec.from_mapping(tomllib.loads(out)) == Spec()


def test_cli_init_help(capsys):
    try:
        main(["--help"])
    except SystemExit as exc:
        assert exc.code == 0
    out = capsys.readouterr().out
    assert "parch init" in out
    assert "Spec defaults" in out
    assert "prompts" in out

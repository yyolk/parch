"""parch init: flags-only profile picker. Never prompts."""

import sys
import tomllib
from pathlib import Path

import pytest

from parch.init import PROFILE_NAMES, init_profile, overlay_profile, profile_text
from parch.press import main
from parch.spec import Spec

REPO = Path(__file__).resolve().parents[1]
EXAMPLE_FOR_PROFILE = {
    "nomad": REPO / "examples" / "nomad.toml",
    "scribe": REPO / "examples" / "scribe.toml",
    "bujo": REPO / "examples" / "nomad-bujo.toml",
    "extras": REPO / "examples" / "nomad-extras.toml",
}


def test_baked_profiles_match_examples():
    for name, example in EXAMPLE_FOR_PROFILE.items():
        assert profile_text(name) == example.read_text(encoding="utf-8")


@pytest.mark.parametrize("name", PROFILE_NAMES)
def test_init_writes_profile_toml_to_cwd(tmp_path: Path, name: str):
    dest = init_profile(name, cwd=tmp_path)
    assert dest == tmp_path / f"{name}.toml"
    assert dest.is_file()
    spec = Spec.from_path(dest)
    baked = Spec.from_mapping(tomllib.loads(profile_text(name)))
    assert spec == baked


def test_cli_init_nomad_to_cwd(tmp_path: Path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    assert main(["init", "--profile", "nomad"]) == 0
    out = capsys.readouterr().out.strip()
    dest = tmp_path / "nomad.toml"
    assert Path(out) == dest
    spec = Spec.from_path(dest)
    assert spec.device == "supernote-nomad"
    assert spec.year == 2026
    assert spec.book == "year-planner"
    assert spec.favorites_pages == 0
    assert spec.my_100 is False
    assert spec.checkoff_365 is False


def test_cli_init_year_and_device_flags(tmp_path: Path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    assert main(["init", "--profile", "bujo", "--year", "2027", "--device", "scribe"]) == 0
    dest = tmp_path / "bujo.toml"
    assert Path(capsys.readouterr().out.strip()) == dest
    text = dest.read_text(encoding="utf-8")
    data = tomllib.loads(text)
    assert data["year"] == 2027
    assert data["device"] == "scribe"
    assert data["book"] == "bullet-journal"
    assert "Draft book" in text
    spec = Spec.from_path(dest)
    assert spec.year == 2027
    assert spec.device == "scribe"
    assert spec.book == "bullet-journal"


def test_cli_init_scribe_and_extras_fields(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert main(["init", "--profile", "scribe"]) == 0
    scribe = Spec.from_path(tmp_path / "scribe.toml")
    assert scribe.device == "kindle-scribe"
    assert scribe.book == "year-planner"

    assert main(["init", "--profile", "extras"]) == 0
    extras = Spec.from_path(tmp_path / "extras.toml")
    assert extras.favorites_pages == 1
    assert extras.my_100 is True
    assert extras.checkoff_365 is True
    assert extras.months == (1,)
    assert extras.notes_pages == 0


def test_cli_refuses_overwrite(tmp_path: Path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    dest = tmp_path / "nomad.toml"
    dest.write_text("keep\n", encoding="utf-8")
    assert main(["init", "--profile", "nomad"]) == 2
    err = capsys.readouterr().err
    assert "already exists" in err
    assert dest.read_text(encoding="utf-8") == "keep\n"


def test_cli_unknown_device(tmp_path: Path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    assert main(["init", "--profile", "nomad", "--device", "ipad"]) == 2
    err = capsys.readouterr().err
    assert "unknown device" in err
    assert not (tmp_path / "nomad.toml").exists()


def test_cli_bad_year(tmp_path: Path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    assert main(["init", "--profile", "nomad", "--year", "0"]) == 2
    assert "year must be between 1 and 9999" in capsys.readouterr().err
    assert not (tmp_path / "nomad.toml").exists()


def test_cli_requires_profile(capsys):
    with pytest.raises(SystemExit) as exc:
        main(["init"])
    assert exc.value.code == 2
    err = capsys.readouterr().err
    assert "--profile" in err


def test_cli_help_is_flags_only(capsys):
    with pytest.raises(SystemExit) as exc:
        main(["init", "--help"])
    assert exc.value.code == 0
    out = capsys.readouterr().out
    assert "never prompts" in out
    assert "--profile" in out
    assert "--year" in out
    assert "--device" in out
    for name in PROFILE_NAMES:
        assert name in out
    assert "questionary" not in out.lower()


def test_never_calls_input(tmp_path: Path, monkeypatch):
    def boom(prompt: object = "") -> str:
        raise AssertionError(f"init must not prompt; got {prompt!r}")

    monkeypatch.setattr("builtins.input", boom)
    monkeypatch.chdir(tmp_path)
    assert main(["init", "--profile", "nomad", "--year", "2028"]) == 0
    assert Spec.from_path(tmp_path / "nomad.toml").year == 2028


def test_questionary_is_not_a_dependency():
    assert "questionary" not in sys.modules
    import parch.init as init_mod

    assert "questionary" not in sys.modules
    assert not hasattr(init_mod, "questionary")
    pyproject = (REPO / "pyproject.toml").read_text(encoding="utf-8")
    assert "questionary" not in pyproject


def test_overlay_profile_keeps_neighbors():
    text = profile_text("nomad")
    written = overlay_profile(text, year=2027, device="kindle-scribe")
    assert "notes_pages = 1 keeps the year artifact smaller" in written
    assert "year = 2027" in written
    assert 'device = "kindle-scribe"' in written
    assert written.count("year = ") == 1
    assert written.count("device = ") == 1

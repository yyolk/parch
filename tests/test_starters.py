import subprocess
import zipfile
from pathlib import Path

import pytest

from parch import ConfigError
from parch.press import main
from parch.spec import Spec
from parch.starters import STARTERS, starter_bytes, write_starter

_REPO = Path(__file__).resolve().parents[1]


def _example(name: str) -> bytes:
    return (_REPO / "examples" / f"{name}.toml").read_bytes()


def test_starter_bytes_match_examples():
    for name in sorted(STARTERS):
        assert starter_bytes(name) == _example(name)


def test_init_writes_nomad(tmp_path: Path, capsys: pytest.CaptureFixture[str]):
    dest = tmp_path / "job.toml"
    assert main(["init", str(dest)]) == 0
    assert dest.read_bytes() == _example("nomad")
    assert capsys.readouterr().out.strip() == str(dest)
    spec = Spec.from_path(dest)
    assert spec.device == "supernote-nomad"
    assert spec.year == 2026
    assert spec.title == "Year planner"


def test_init_default_path(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.chdir(tmp_path)
    assert main(["init"]) == 0
    dest = tmp_path / "parch.toml"
    assert dest.read_bytes() == _example("nomad")
    assert capsys.readouterr().out.strip() == "parch.toml"


def test_init_refuses_overwrite(tmp_path: Path, capsys: pytest.CaptureFixture[str]):
    dest = tmp_path / "job.toml"
    dest.write_text("nope\n", encoding="utf-8")
    assert main(["init", str(dest)]) == 2
    assert "overwrite" in capsys.readouterr().err
    assert dest.read_text(encoding="utf-8") == "nope\n"


def test_init_creates_parent_dirs(tmp_path: Path):
    dest = tmp_path / "nested" / "planner.toml"
    assert main(["init", str(dest)]) == 0
    assert dest.is_file()


def test_write_starter_unknown_name(tmp_path: Path):
    with pytest.raises(ConfigError, match="unknown starter"):
        write_starter(tmp_path / "x.toml", name="missing")


def test_init_help(capsys: pytest.CaptureFixture[str]):
    with pytest.raises(SystemExit) as exc:
        main(["init", "--help"])
    assert exc.value.code == 0
    out = capsys.readouterr().out
    assert "parch init" in out
    assert "Nomad" in out


def test_wheel_init_without_checkout(tmp_path: Path):
    dist = tmp_path / "dist"
    work = tmp_path / "work"
    venv = tmp_path / "venv"
    dist.mkdir()
    work.mkdir()
    subprocess.run(
        ["uv", "build", "--wheel", "--out-dir", str(dist)],
        check=True,
        cwd=_REPO,
    )
    wheels = list(dist.glob("*.whl"))
    assert len(wheels) == 1
    with zipfile.ZipFile(wheels[0]) as zf:
        names = set(zf.namelist())
        assert "parch/starters/nomad.toml" in names
        assert "parch/starters/scribe.toml" in names
        assert zf.read("parch/starters/nomad.toml") == _example("nomad")
        assert zf.read("parch/starters/scribe.toml") == _example("scribe")

    subprocess.run(["uv", "venv", str(venv), "--python", "3.14"], check=True)
    subprocess.run(
        [
            "uv",
            "pip",
            "install",
            "--python",
            str(venv / "bin" / "python"),
            str(wheels[0]),
        ],
        check=True,
    )
    dest = work / "parch.toml"
    completed = subprocess.run(
        [str(venv / "bin" / "parch"), "init", str(dest)],
        check=True,
        cwd=work,
        capture_output=True,
        text=True,
    )
    assert dest.read_bytes() == _example("nomad")
    assert completed.stdout.strip() == str(dest)

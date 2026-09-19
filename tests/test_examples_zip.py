"""Pack examples/*.toml into parch-examples.zip."""

import subprocess
import sys
import zipfile
from pathlib import Path

import pytest

from parch import ConfigError
from parch.services.examples_zip import (
    EXAMPLES_ZIP_NAME,
    arcname_for,
    example_tomls,
    examples_dir,
    main,
    starter_name,
    starters_from_zip,
    write_examples_zip,
)


def test_examples_dir_requires_examples(tmp_path: Path):
    with pytest.raises(ConfigError, match="examples/ not found"):
        examples_dir(tmp_path)


def test_example_tomls_are_repo_starters():
    names = [path.name for path in example_tomls()]
    assert "nomad.toml" in names
    assert "scribe.toml" in names
    assert names == sorted(names)
    assert all(name.endswith(".toml") for name in names)


def test_write_examples_zip_members_match_files(tmp_path: Path):
    dest = tmp_path / EXAMPLES_ZIP_NAME
    assert write_examples_zip(dest) == dest
    assert dest.is_file() and dest.stat().st_size > 0
    with zipfile.ZipFile(dest) as zf:
        names = zf.namelist()
    expected = [arcname_for(path) for path in example_tomls()]
    assert names == expected
    packed = starters_from_zip(dest.read_bytes())
    for path in example_tomls():
        assert packed[path.stem] == path.read_bytes()


def test_starters_from_zip_rejects_empty():
    with pytest.raises(ConfigError, match="empty"):
        starters_from_zip(b"")


def test_starters_from_zip_rejects_not_a_zip():
    with pytest.raises(ConfigError, match="not a zip"):
        starters_from_zip(b"not-a-zip")


def test_starters_from_zip_rejects_duplicate_stems(tmp_path: Path):
    dest = tmp_path / "dup.zip"
    with zipfile.ZipFile(dest, "w") as zf:
        zf.writestr("examples/nomad.toml", "year = 2026\n")
        zf.writestr("nomad.toml", "year = 2027\n")
    with pytest.raises(ConfigError, match="duplicate starter 'nomad'"):
        starters_from_zip(dest.read_bytes())


def test_starter_name_ignores_non_toml():
    assert starter_name("examples/nomad.toml") == "nomad"
    assert starter_name("nomad.toml") == "nomad"
    assert starter_name("examples/README.md") is None
    assert starter_name("examples/.hidden.toml") is None


def test_module_writes_default_zip(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    # examples/ lives in the repo; point cwd at a tree that has it.
    repo = Path(__file__).resolve().parents[1]
    monkeypatch.chdir(repo)
    dest = tmp_path / "out.zip"
    assert main(["-o", str(dest)]) == 0
    assert dest.is_file()
    assert "examples/nomad.toml" in zipfile.ZipFile(dest).namelist()


def test_module_prints_path(tmp_path: Path, capsys, monkeypatch):
    repo = Path(__file__).resolve().parents[1]
    monkeypatch.chdir(repo)
    dest = tmp_path / EXAMPLES_ZIP_NAME
    proc = subprocess.run(
        [sys.executable, "-m", "parch.services.examples_zip", "-o", str(dest)],
        capture_output=True,
        text=True,
        cwd=repo,
    )
    assert proc.returncode == 0
    assert proc.stdout.strip() == str(dest)

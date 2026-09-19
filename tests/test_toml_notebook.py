import tomllib
from pathlib import Path

import pytest

from parch import ConfigError
from parch.press import main
from parch.spec import Spec
from parch.toml_notebook import (
    KEY_DOCS,
    MANAGED_PREFIX,
    annotate,
    documented_paths,
    explain_text,
    minimal_toml,
    present_paths,
    unknown_paths,
    write_init,
)


def test_minimal_toml_is_year_and_device():
    text = minimal_toml()
    assert text == 'year = 2026\ndevice = "supernote-nomad"\n'
    spec = Spec.from_mapping({"year": 2026, "device": "supernote-nomad"})
    assert spec.book == "year-planner"
    assert spec.months == tuple(range(1, 13))


def test_minimal_toml_engineering_notebook_includes_sheets():
    text = minimal_toml(book="engineering-notebook", device="nomad")
    assert 'book = "engineering-notebook"' in text
    assert "[engineering]" in text
    assert "sheets = 1" in text
    loaded = Spec.from_mapping(
        {
            "year": 2026,
            "device": "nomad",
            "book": "engineering-notebook",
            "engineering": {"sheets": 1},
        }
    )
    assert loaded.engineering_sheets == 1


def test_minimal_toml_rejects_unknown_book():
    with pytest.raises(ConfigError, match="book must be"):
        minimal_toml(book="meetings-notebook")


def test_minimal_toml_rejects_unknown_device():
    with pytest.raises(ConfigError, match="unknown device"):
        minimal_toml(device="remarkable")


def test_annotate_documents_only_present_keys():
    raw = 'year = 2026\ndevice = "supernote-nomad"\n'
    written = annotate(raw)
    assert f"{MANAGED_PREFIX} {KEY_DOCS['year']}" in written
    assert f"{MANAGED_PREFIX} {KEY_DOCS['device']}" in written
    assert "week_start" not in written
    assert "book" not in written
    assert documented_paths(written) == ("year", "device")


def test_annotate_is_idempotent():
    raw = 'year = 2026\ndevice = "supernote-nomad"\noutline = true\n'
    once = annotate(raw)
    twice = annotate(once)
    assert twice == once
    assert once.count(MANAGED_PREFIX) == 3


def test_annotate_keeps_user_comments_and_values():
    raw = (
        "# my planner\n"
        "year = 2027  # leap?\n"
        'device = "kindle-scribe"\n'
        "months = { from = 4, to = 6 }\n"
    )
    written = annotate(raw)
    assert "# my planner" in written
    assert "year = 2027  # leap?" in written
    assert 'device = "kindle-scribe"' in written
    assert "months = { from = 4, to = 6 }" in written
    assert written.index("# my planner") < written.index(f"{MANAGED_PREFIX} {KEY_DOCS['year']}")
    assert written.index(f"{MANAGED_PREFIX} {KEY_DOCS['year']}") < written.index(
        "year = 2027"
    )


def test_annotate_refreshes_stale_managed_comment():
    raw = (
        f"{MANAGED_PREFIX} stale year blurb\n"
        "year = 2026\n"
        "# keep me\n"
        'device = "supernote-nomad"\n'
    )
    written = annotate(raw)
    assert "stale year blurb" not in written
    assert f"{MANAGED_PREFIX} {KEY_DOCS['year']}" in written
    assert "# keep me" in written
    assert written.count(MANAGED_PREFIX) == 2


def test_annotate_grows_when_user_adds_a_key():
    seed = annotate('year = 2026\ndevice = "supernote-nomad"\n')
    grown = seed.rstrip() + "\noutline = true\n"
    written = annotate(grown)
    assert f"{MANAGED_PREFIX} {KEY_DOCS['outline']}" in written
    assert documented_paths(written) == ("year", "device", "outline")
    # prior managed comments stay; we do not rewrite the year/device block
    assert seed.splitlines()[0] in written.splitlines()


def test_annotate_skips_unknown_keys():
    raw = 'year = 2026\nflavor = "mint"\n'
    written = annotate(raw)
    assert "flavor" in present_paths(written)
    assert "flavor" in unknown_paths(written)
    assert "flavor" not in documented_paths(written)
    flavor_line = next(
        line for line in written.splitlines() if line.startswith("flavor")
    )
    idx = written.splitlines().index(flavor_line)
    if idx:
        assert MANAGED_PREFIX not in written.splitlines()[idx - 1]


def test_annotate_table_and_dotted_schedule(tmp_path: Path):
    raw = (
        "[daily]\n"
        "schedule = { from = 07:00:00, to = 16:00:00 }\n"
        "notes_pages = 1\n"
        "\n"
        "[daily.schedule]\n"
        "from = 09:00:00\n"
        "to = 17:00:00\n"
        "step = 30\n"
    )
    written = annotate(raw)
    assert f"{MANAGED_PREFIX} {KEY_DOCS['daily']}" in written
    assert f"{MANAGED_PREFIX} {KEY_DOCS['daily.schedule']}" in written
    assert f"{MANAGED_PREFIX} {KEY_DOCS['daily.notes_pages']}" in written
    assert f"{MANAGED_PREFIX} {KEY_DOCS['daily.schedule.from']}" in written
    assert f"{MANAGED_PREFIX} {KEY_DOCS['daily.schedule.to']}" in written
    assert f"{MANAGED_PREFIX} {KEY_DOCS['daily.schedule.step']}" in written
    path = tmp_path / "sched.toml"
    path.write_text(written, encoding="utf-8")
    spec = Spec.from_path(path)
    assert spec.schedule_hours == tuple(range(9, 18))
    assert spec.notes_pages == 1


def test_annotate_months_header_form():
    raw = "[months]\nfrom = 1\nto = 12\n"
    written = annotate(raw)
    assert f"{MANAGED_PREFIX} {KEY_DOCS['months']}" in written
    assert f"{MANAGED_PREFIX} {KEY_DOCS['months.from']}" in written
    assert f"{MANAGED_PREFIX} {KEY_DOCS['months.to']}" in written
    assert Spec.from_mapping({"months": {"from": 1, "to": 12}}).months == tuple(
        range(1, 13)
    )


def test_annotate_preserves_example_values():
    path = Path("examples/nomad.toml")
    raw = path.read_text(encoding="utf-8")
    before = Spec.from_path(path)
    written = annotate(raw)
    assert "Nomad year planner walk" in written
    assert "year = 2026" in written
    assert "notes_pages = 1" in written
    assert "schedule = { from = 07:00:00, to = 16:00:00 }" in written
    assert Spec.from_mapping(tomllib.loads(written)) == before
    assert path.read_text(encoding="utf-8") == raw


def test_annotate_typography_overlay_steps():
    raw = Path("examples/nomad-typo-overlay.toml").read_text(encoding="utf-8")
    before = Spec.from_path(Path("examples/nomad-typo-overlay.toml"))
    written = annotate(raw)
    assert Spec.from_mapping(tomllib.loads(written)) == before
    assert "typography.overlay" in documented_paths(written)
    assert "typography.overlay.chrome" in documented_paths(written)
    assert "typography.overlay.chrome.size" in documented_paths(written)
    assert "typography.overlay.display.weight" in documented_paths(written)


def test_explain_text_lists_present_docs_only():
    text = annotate('year = 2026\nflavor = "mint"\n')
    body = explain_text(text)
    assert "year" in body
    assert KEY_DOCS["year"] in body
    assert "device" not in body
    assert "undocumented keys: flavor" in body


def test_write_init_refuses_overwrite(tmp_path: Path):
    path = tmp_path / "parch.toml"
    write_init(path)
    with pytest.raises(ConfigError, match="refusing to overwrite"):
        write_init(path)
    write_init(path, force=True, year=2027, annotate_keys=True)
    text = path.read_text(encoding="utf-8")
    assert "year = 2027" in text
    assert MANAGED_PREFIX in text


def test_cli_init_writes_tiny_file(tmp_path: Path, capsys):
    out = tmp_path / "job.toml"
    assert main(["init", "-o", str(out)]) == 0
    assert capsys.readouterr().out.strip() == str(out)
    assert out.read_text(encoding="utf-8") == 'year = 2026\ndevice = "supernote-nomad"\n'


def test_cli_init_annotate_and_book(tmp_path: Path):
    out = tmp_path / "eng.toml"
    assert (
        main(
            [
                "init",
                "-o",
                str(out),
                "--book",
                "engineering-notebook",
                "--annotate",
            ]
        )
        == 0
    )
    text = out.read_text(encoding="utf-8")
    assert MANAGED_PREFIX in text
    assert Spec.from_path(out).book == "engineering-notebook"
    assert Spec.from_path(out).engineering_sheets == 1


def test_cli_init_force_and_refuse(tmp_path: Path, capsys):
    out = tmp_path / "job.toml"
    out.write_text("year = 2026\n", encoding="utf-8")
    assert main(["init", "-o", str(out)]) == 2
    assert "refusing to overwrite" in capsys.readouterr().err
    assert main(["init", "-o", str(out), "--force", "--year", "2028"]) == 0
    assert "year = 2028" in out.read_text(encoding="utf-8")


def test_cli_doctor_annotates_and_validates(tmp_path: Path, capsys):
    spec = tmp_path / "job.toml"
    spec.write_text('year = 2026\ndevice = "nomad"\noutline = true\n', encoding="utf-8")
    assert main(["doctor", str(spec)]) == 0
    out = capsys.readouterr().out
    assert "annotated" in out
    assert "3 keys" in out
    assert "ok: year-planner 2026 nomad" in out
    text = spec.read_text(encoding="utf-8")
    assert MANAGED_PREFIX in text
    assert main(["doctor", str(spec)]) == 0
    again = capsys.readouterr().out
    assert "already documented" in again


def test_cli_doctor_default_parch_toml(tmp_path: Path, capsys, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "parch.toml").write_text("year = 2026\n", encoding="utf-8")
    assert main(["doctor"]) == 0
    assert "ok: year-planner 2026" in capsys.readouterr().out
    assert MANAGED_PREFIX in (tmp_path / "parch.toml").read_text(encoding="utf-8")


def test_cli_doctor_missing_file(tmp_path: Path, capsys, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert main(["doctor"]) == 2
    assert "spec file not found" in capsys.readouterr().err


def test_cli_doctor_invalid_toml(tmp_path: Path, capsys):
    spec = tmp_path / "bad.toml"
    spec.write_text("year = [\n", encoding="utf-8")
    assert main(["doctor", str(spec)]) == 2
    assert "invalid TOML" in capsys.readouterr().err
    assert spec.read_text(encoding="utf-8") == "year = [\n"


def test_cli_doctor_invalid_spec_still_annotates(tmp_path: Path, capsys):
    spec = tmp_path / "bad.toml"
    spec.write_text("week_start = true\n", encoding="utf-8")
    assert main(["doctor", str(spec)]) == 2
    err = capsys.readouterr().err
    assert "week_start must be monday or sunday" in err
    assert MANAGED_PREFIX in spec.read_text(encoding="utf-8")


def test_cli_explain_prints_docs(tmp_path: Path, capsys):
    spec = tmp_path / "job.toml"
    spec.write_text('year = 2026\ndevice = "scribe"\n', encoding="utf-8")
    assert main(["explain", str(spec)]) == 0
    out = capsys.readouterr().out
    assert KEY_DOCS["year"] in out
    assert KEY_DOCS["device"] in out
    assert "ok: year-planner 2026 scribe" in out
    assert MANAGED_PREFIX in spec.read_text(encoding="utf-8")


def test_cli_init_help():
    with pytest.raises(SystemExit) as exited:
        main(["init", "--help"])
    assert exited.value.code == 0


def test_cli_doctor_help():
    with pytest.raises(SystemExit) as exited:
        main(["doctor", "--help"])
    assert exited.value.code == 0


def test_cli_explain_help():
    with pytest.raises(SystemExit) as exited:
        main(["explain", "--help"])
    assert exited.value.code == 0


def test_no_questionary_import():
    import parch.toml_notebook as notebook

    assert "questionary" not in dir(notebook)
    source = Path("src/parch/toml_notebook.py").read_text(encoding="utf-8")
    assert "questionary" not in source
    lock = Path("pyproject.toml").read_text(encoding="utf-8")
    assert "questionary" not in lock

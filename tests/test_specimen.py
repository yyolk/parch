"""Specimen catalog: device listing, HTML index, dest → page map."""

import shutil
import subprocess
from pathlib import Path

import pytest

from parch import ConfigError
from parch.press import main
from parch.specimen import (
    CATALOG_DEVICE_IDS,
    GALLERY_GROUPS,
    GALLERY_STEMS,
    PROJECTS_STEMS,
    SAMPLE_STEMS,
    catalog_dest,
    catalog_index_html,
    projects_dests,
    projects_page_numbers,
    projects_specimen_spec,
    resolve_commit_sha,
    sample_dests,
    sample_page_numbers,
    specimen_index_html,
    specimen_spec,
    specimens_dest,
    steno_dests,
    steno_page_numbers,
    steno_specimen_spec,
    write_catalog_index,
    write_device_index,
)


def test_catalog_index_html_is_device_list(snapshot):
    html = catalog_index_html(["supernote-nomad"])
    assert html == snapshot
    assert "<figure>" not in html
    assert ".png" not in html
    assert "<script" not in html


def test_catalog_device_ids_are_sealed():
    assert CATALOG_DEVICE_IDS == ("supernote-nomad", "kindle-scribe")


def test_gallery_stems_follow_groups():
    assert GALLERY_STEMS == tuple(
        stem for _sid, _title, stems in GALLERY_GROUPS for stem in stems
    )


def test_catalog_index_html_lists_both_devices(snapshot):
    html = catalog_index_html(CATALOG_DEVICE_IDS)
    assert html == snapshot
    assert html.index("supernote-nomad") < html.index("kindle-scribe")


def test_specimen_index_html_is_png_gallery(snapshot):
    html = specimen_index_html("supernote-nomad")
    assert html == snapshot
    assert "<script" not in html
    assert html.count("<figure>") == len(GALLERY_STEMS)
    assert html.count("<a href=") == 1 + len(GALLERY_GROUPS)
    for stem in GALLERY_STEMS:
        assert f'href="{stem}.png"' not in html


def test_specimen_index_html_section_anchors(snapshot):
    html = specimen_index_html("kindle-scribe")
    assert html == snapshot
    assert html.index('href="#year-planner"') < html.index('id="year-planner"')
    assert html.index('id="year-planner"') < html.index('id="engineering-notebook"')
    assert html.index('id="projects-notebook"') < html.index('id="steno-pad"')


def test_write_indexes(tmp_path: Path):
    device_dir = specimens_dest(tmp_path, "supernote-nomad")
    index = write_device_index(device_dir, "supernote-nomad")
    assert index == device_dir / "index.html"
    root = catalog_dest(tmp_path)
    catalog = write_catalog_index(root, ("supernote-nomad", "kindle-scribe"))
    assert catalog == root / "index.html"
    html = catalog.read_text(encoding="utf-8")
    assert 'href="supernote-nomad/"' in html
    assert 'href="kindle-scribe/"' in html
    sha = resolve_commit_sha()
    if sha:
        assert f'href="https://github.com/yyolk/parch/commit/{sha}"' in html
        assert f">{sha[:7]}<" in html
        device_html = index.read_text(encoding="utf-8")
        assert f">{sha[:7]}<" in device_html


def test_resolve_commit_sha_prefers_explicit(monkeypatch):
    monkeypatch.setenv("GITHUB_SHA", "a" * 40)
    assert resolve_commit_sha("c" * 40) == "c" * 40


def test_resolve_commit_sha_prefers_github_sha(monkeypatch):
    monkeypatch.setenv("GITHUB_SHA", "b" * 40)

    def boom(*_args, **_kwargs):
        raise AssertionError("should not call git")

    monkeypatch.setattr("parch.specimen.subprocess.run", boom)
    assert resolve_commit_sha() == "b" * 40


def test_resolve_commit_sha_falls_back_to_git(monkeypatch):
    monkeypatch.delenv("GITHUB_SHA", raising=False)

    def fake_run(cmd, **_kwargs):
        assert cmd[-2:] == ["rev-parse", "HEAD"]
        return subprocess.CompletedProcess(cmd, 0, stdout="d" * 40 + "\n", stderr="")

    monkeypatch.setattr("parch.specimen.shutil.which", lambda _name: "/usr/bin/git")
    monkeypatch.setattr("parch.specimen.subprocess.run", fake_run)
    assert resolve_commit_sha() == "d" * 40


def test_resolve_commit_sha_omits_when_unavailable(monkeypatch):
    monkeypatch.delenv("GITHUB_SHA", raising=False)
    monkeypatch.setattr("parch.specimen.shutil.which", lambda _name: None)
    assert resolve_commit_sha() is None


def test_specimen_index_html_commit_footer(monkeypatch):
    monkeypatch.delenv("GITHUB_REPOSITORY", raising=False)
    sha = "abcdef1234567890"
    html = specimen_index_html("supernote-nomad", commit=sha)
    assert (
        f'<footer><a href="https://github.com/yyolk/parch/commit/{sha}">abcdef1</a></footer>'
        in html
    )


def test_catalog_index_html_commit_footer(monkeypatch):
    monkeypatch.setenv("GITHUB_REPOSITORY", "acme/planner")
    sha = "1234567890abcdef"
    html = catalog_index_html(["supernote-nomad"], commit=sha)
    assert (
        f'<footer><a href="https://github.com/acme/planner/commit/{sha}">1234567</a></footer>'
        in html
    )
    assert "<figure>" not in html


def test_specimen_index_html_omits_footer_without_commit():
    html = specimen_index_html("kindle-scribe")
    assert "<footer>" not in html
    assert "github.com/" not in html


def test_sample_dests_and_pages_for_january(snapshot):
    spec = specimen_spec("supernote-nomad")
    assert spec.months == (1,)
    assert spec.notes_pages == 1
    dests = sample_dests(spec)
    assert dests == snapshot(name="dests")
    numbers = sample_page_numbers(spec)
    assert numbers == snapshot(name="pages")
    assert set(numbers) == set(SAMPLE_STEMS)
    assert all(page >= 1 for page in numbers.values())
    assert len(set(numbers.values())) == len(SAMPLE_STEMS)


def test_projects_dests_and_pages(snapshot):
    spec = projects_specimen_spec("kindle-scribe")
    assert spec.book == "projects-notebook"
    assert spec.device == "kindle-scribe"
    dests = projects_dests(spec)
    assert dests == snapshot(name="dests")
    assert dests["projects-index"] == spec.projects_index_dest
    assert dests["projects-project-1"] == spec.dest_for_project(1)
    numbers = projects_page_numbers(spec)
    assert numbers == snapshot(name="pages")
    assert set(numbers) == set(PROJECTS_STEMS)


def test_steno_dests_and_pages(snapshot):
    spec = steno_specimen_spec("supernote-nomad")
    assert spec.steno_sheets == 1
    dests = steno_dests(spec)
    assert dests == snapshot(name="dests")
    assert dests["steno"] == spec.dest_for_steno_pad(1)
    numbers = steno_page_numbers(spec)
    assert numbers == snapshot(name="pages")


def test_specimen_cli_help(capsys):
    with pytest.raises(SystemExit) as exc:
        main(["specimen", "--help"])
    assert exc.value.code == 0
    out = capsys.readouterr().out
    assert "specimen" in out
    assert "--workdir" in out
    assert "Omit to press every catalog device" in out
    assert "--commit" in out


def test_specimen_rejects_unknown_device_before_press(
    tmp_path: Path, capsys, monkeypatch
):
    def boom(*_args, **_kwargs):
        raise AssertionError("should not press")

    monkeypatch.setattr("parch.press.press", boom)
    assert main(["specimen", "unknown-slate", "-w", str(tmp_path)]) == 2
    assert "unknown device" in capsys.readouterr().err
    assert not (tmp_path / "specimens").exists()


def test_specimen_spec_rejects_unknown_device():
    with pytest.raises(ConfigError, match="unknown device"):
        specimen_spec("unknown-slate")


def test_specimen_omitted_device_builds_full_catalog(tmp_path: Path, monkeypatch):
    seen: dict[str, object] = {}

    def fake_build(workdir, device_ids=None, **kwargs):
        seen["workdir"] = workdir
        seen["device_ids"] = device_ids
        seen["commit"] = kwargs.get("commit")
        dest = Path(workdir) / "specimens"
        dest.mkdir(parents=True)
        return dest

    monkeypatch.setattr("parch.specimen.build_catalog", fake_build)
    assert main(["specimen", "-w", str(tmp_path)]) == 0
    assert seen["device_ids"] is None
    assert seen["workdir"] == str(tmp_path)
    assert seen["commit"] is None


def test_specimen_cli_passes_commit(tmp_path: Path, monkeypatch):
    seen: dict[str, object] = {}

    def fake_build(workdir, device_ids=None, **kwargs):
        seen["commit"] = kwargs.get("commit")
        dest = Path(workdir) / "specimens"
        dest.mkdir(parents=True)
        return dest

    monkeypatch.setattr("parch.specimen.build_catalog", fake_build)
    assert main(["specimen", "-w", str(tmp_path), "--commit", "abc1234deadbeef"]) == 0
    assert seen["commit"] == "abc1234deadbeef"


def test_write_specimens_presses_notebooks_and_steno(tmp_path: Path, monkeypatch):
    from parch.specimen import write_specimens

    presses: list[object] = []

    def fake_press(spec, output, **_kwargs):
        presses.append(spec)
        output.write_bytes(b"%PDF")
        return output

    def fake_render(_pdf, _page, dest, **_kwargs):
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(b"png")
        return dest

    monkeypatch.setattr("parch.press.press", fake_press)
    monkeypatch.setattr("parch.specimen.render_page_png", fake_render)
    dest = tmp_path / "nomad"
    write_specimens(dest, "supernote-nomad")
    assert any(spec.book == "year-planner" for spec in presses)
    assert any(spec.book == "engineering-notebook" for spec in presses)
    assert any(spec.book == "projects-notebook" for spec in presses)
    assert any(spec.steno_sheets == 1 for spec in presses)
    html = (dest / "index.html").read_text(encoding="utf-8")
    for stem in GALLERY_STEMS:
        assert (dest / f"{stem}.png").is_file()
        assert f'src="{stem}.png"' in html
    for section_id, title, _stems in GALLERY_GROUPS:
        assert f'<section id="{section_id}">' in html
        assert f"<h2>{title}</h2>" in html
        assert f'href="#{section_id}"' in html
    sha = resolve_commit_sha()
    if sha:
        assert f">{sha[:7]}<" in html
        assert f"github.com/yyolk/parch/commit/{sha}" in html


def test_build_catalog_lists_both_devices(tmp_path: Path, monkeypatch):
    from parch.specimen import build_catalog

    written: list[str] = []

    def fake_write(dest: Path, device_id: str, **_kwargs):
        written.append(device_id)
        dest.mkdir(parents=True)
        (dest / "index.html").write_text("x", encoding="utf-8")
        return dest

    monkeypatch.setattr("parch.specimen.write_specimens", fake_write)
    root = build_catalog(tmp_path)
    assert written == list(CATALOG_DEVICE_IDS)
    assert root == tmp_path / "specimens"
    html = (root / "index.html").read_text(encoding="utf-8")
    assert 'href="supernote-nomad/"' in html
    assert 'href="kindle-scribe/"' in html
    sha = resolve_commit_sha()
    if sha:
        assert f">{sha[:7]}<" in html


@pytest.mark.skipif(
    shutil.which("pdftoppm") is None, reason="pdftoppm (poppler-utils) required"
)
def test_write_specimens_png_catalog(tmp_path: Path):
    from parch.specimen import build_device_catalog

    dest = build_device_catalog(tmp_path, "supernote-nomad")
    assert (dest / "cover.png").stat().st_size > 0
    assert (dest / "index.html").is_file()
    root = catalog_dest(tmp_path) / "index.html"
    assert root.is_file()
    assert 'href="supernote-nomad/"' in root.read_text(encoding="utf-8")
    assert list(dest.glob("*.pdf")) == []
    html = (dest / "index.html").read_text(encoding="utf-8")
    assert 'src="cover.png"' in html
    assert 'href="cover.png"' not in html
    assert "<script" not in html
    assert '<input type="checkbox" id="cover">' in html
    assert "figure>input:checked+label img{width:auto;max-width:100%}" in html
    for stem in GALLERY_STEMS:
        assert (dest / f"{stem}.png").stat().st_size > 0
        assert f'src="{stem}.png"' in html
    for section_id, title, _stems in GALLERY_GROUPS:
        assert f'<section id="{section_id}">' in html
        assert f"<h2>{title}</h2>" in html
        assert f'href="#{section_id}"' in html
    sha = resolve_commit_sha()
    if sha:
        assert f">{sha[:7]}<" in html
        assert f">{sha[:7]}<" in root.read_text(encoding="utf-8")


def test_build_device_catalog_uses_canonical_id(tmp_path: Path, monkeypatch):
    from parch.specimen import build_device_catalog

    seen: dict[str, object] = {}

    def fake_write(dest: Path, device_id: str, **_kwargs):
        seen["dest"] = dest
        seen["device_id"] = device_id
        dest.mkdir(parents=True)
        (dest / "index.html").write_text("x", encoding="utf-8")
        return dest

    monkeypatch.setattr("parch.specimen.write_specimens", fake_write)
    out = build_device_catalog(tmp_path, "nomad")
    assert seen["device_id"] == "supernote-nomad"
    assert out == tmp_path / "specimens" / "supernote-nomad"
    root = catalog_dest(tmp_path) / "index.html"
    assert 'href="supernote-nomad/"' in root.read_text(encoding="utf-8")

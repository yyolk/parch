"""Specimen catalog: device listing, HTML index, dest → page map."""

import shutil
from pathlib import Path

import pytest

from parch import ConfigError
from parch.press import main
from parch.specimen import (
    SAMPLE_STEMS,
    catalog_dest,
    catalog_index_html,
    sample_dests,
    sample_page_numbers,
    specimen_index_html,
    specimen_spec,
    specimens_dest,
    write_catalog_index,
    write_device_index,
)


def test_catalog_index_html_is_device_list():
    html = catalog_index_html(["supernote-nomad"])
    assert 'href="supernote-nomad/"' in html
    assert "<figure>" not in html
    assert ".png" not in html
    assert "<script" not in html


def test_specimen_index_html_is_png_gallery():
    html = specimen_index_html("supernote-nomad")
    assert "supernote-nomad" in html
    assert "<script" not in html
    assert 'href="../"' in html
    assert html.count("<figure>") == len(SAMPLE_STEMS)
    assert html.count("<a href=") == 1  # specimens parent link only
    assert "figure>input:checked+label img{width:auto;max-width:100%}" in html
    for stem in SAMPLE_STEMS:
        assert f'src="{stem}.png"' in html
        assert f'href="{stem}.png"' not in html
        assert (
            f'<figure><input type="checkbox" id="{stem}">'
            f'<label for="{stem}"><img src="{stem}.png" alt="{stem}"></label>'
        ) in html


def test_write_indexes(tmp_path: Path):
    device_dir = specimens_dest(tmp_path, "supernote-nomad")
    index = write_device_index(device_dir, "supernote-nomad")
    assert index == device_dir / "index.html"
    root = catalog_dest(tmp_path)
    catalog = write_catalog_index(root, ("supernote-nomad",))
    assert catalog == root / "index.html"
    html = catalog.read_text(encoding="utf-8")
    assert 'href="supernote-nomad/"' in html


def test_sample_dests_and_pages_for_january():
    spec = specimen_spec("supernote-nomad")
    assert spec.months == (1,)
    assert spec.notes_pages == 1
    dests = sample_dests(spec)
    assert dests["cover"] == "cover"
    assert dests["annual"] == "year-2026"
    assert dests["projects"] == "projects-index-2026-01"
    assert dests["project-1"] == "projects-2026-01"
    assert dests["meetings"] == "meetings-index-2026"
    assert dests["meeting-1"] == "meeting-2026-01"
    assert dests["tasks"] == "tasks-index-2026-Q1"
    assert dests["tasks-w01"] == "tasks-2026-W01"
    assert dests["review"] == "review-index-2026"
    assert dests["review-w01"] == "review-2026-W01"
    assert dests["quarterly-q1"] == "quarter-2026-Q1"
    assert dests["monthly-jan"] == "month-2026-01"
    assert dests["habits-jan"] == "month-2026-01-habits"
    assert dests["weekly-w01"] == "week-2026-W01"
    assert dests["daily-jan1"] == "2026-01-01"
    assert dests["notes-jan1"] == "2026-01-01-notes-1"
    numbers = sample_page_numbers(spec)
    assert set(numbers) == set(SAMPLE_STEMS)
    assert numbers["cover"] == 1
    assert numbers["annual"] == 2
    assert all(page >= 1 for page in numbers.values())
    assert len(set(numbers.values())) == len(SAMPLE_STEMS)


def test_specimen_cli_help(capsys):
    with pytest.raises(SystemExit) as exc:
        main(["specimen", "--help"])
    assert exc.value.code == 0
    out = capsys.readouterr().out
    assert "specimen" in out
    assert "--workdir" in out


def test_specimen_rejects_unknown_device_before_press(tmp_path: Path, capsys, monkeypatch):
    def boom(*_args, **_kwargs):
        raise AssertionError("should not press")

    monkeypatch.setattr("parch.press.press", boom)
    assert main(["specimen", "kindle-scribe", "-w", str(tmp_path)]) == 2
    assert "unknown device" in capsys.readouterr().err
    assert not (tmp_path / "specimens").exists()


def test_specimen_spec_rejects_unknown_device():
    with pytest.raises(ConfigError, match="unknown device"):
        specimen_spec("kindle-scribe")


@pytest.mark.skipif(shutil.which("pdftoppm") is None, reason="pdftoppm (poppler-utils) required")
def test_write_specimens_png_catalog(tmp_path: Path):
    from parch.specimen import build_device_catalog

    dest = build_device_catalog(tmp_path, "supernote-nomad")
    assert (dest / "cover.png").stat().st_size > 0
    assert not (dest / "cover-full.png").exists()
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
    for stem in SAMPLE_STEMS:
        assert (dest / f"{stem}.png").is_file()
        assert not (dest / f"{stem}-full.png").exists()


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

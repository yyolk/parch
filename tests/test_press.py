from pathlib import Path

import pytest
from pypdf import PdfReader

from parch.fonts import PROOF_PROFILE, TypePatch
from parch.press import _load_spec, main, press
from parch.spec import Spec

MM_PER_INCH = 25.4


def _pt(mm: float) -> float:
    return mm / MM_PER_INCH * 72.0


def _named_dests(reader: PdfReader) -> set[str]:
    raw = reader.named_destinations or {}
    return {str(key).lstrip("/") for key in raw}


def _link_count(reader: PdfReader) -> int:
    count = 0
    for page in reader.pages:
        annots = page.get("/Annots")
        if annots is None:
            continue
        for annot in annots:
            obj = annot.get_object()
            if obj.get("/Subtype") == "/Link":
                count += 1
    return count


def test_press_year_pdf(tmp_path: Path):
    out = tmp_path / "mvp.pdf"
    press(Spec(notes_pages=1), out)
    assert out.is_file() and out.stat().st_size > 0

    reader = PdfReader(out)
    # cover + annual + index + 8 leaves + meeting index + 16 dests + 4 task indexes + 53 task dests + review index + 53 review dests + 4 quarters + 12 months + 12 habits + 53 weeks + 365 days + 365 notes
    assert len(reader.pages) == 950

    page = reader.pages[0]
    assert float(page.mediabox.width) == pytest.approx(_pt(118.87), abs=0.6)
    assert float(page.mediabox.height) == pytest.approx(_pt(158.5), abs=0.6)

    dests = _named_dests(reader)
    assert "cover" in dests
    assert "year-2026" in dests
    assert "projects-2026" not in dests
    assert "projects-index-2026-01" in dests
    assert "projects-2026-01" in dests
    assert "projects-2026-08" in dests
    assert "meetings-index-2026" in dests
    assert "meeting-2026-01" in dests
    assert "meeting-2026-16" in dests
    assert "tasks-index-2026-Q1" in dests
    assert "tasks-2026-W01" in dests
    assert "tasks-2026-W53" in dests
    assert "review-index-2026" in dests
    assert "review-2026-W01" in dests
    assert "review-2026-W53" in dests
    assert "quarter-2026-Q1" in dests
    assert "quarter-2026-Q4" in dests
    assert "month-2026-01" in dests
    assert "month-2026-07" in dests
    assert "month-2026-07-habits" in dests
    assert "month-2026-12" in dests
    assert "month-2026-12-habits" in dests
    assert "week-2026-W01" in dests
    assert "week-2026-W53" in dests
    assert "2026-01-01" in dests
    assert "2026-07-15" in dests
    assert "2026-12-31" in dests
    assert "2026-07-15-notes-1" in dests
    assert _link_count(reader) >= 365


def test_cli_press_toml(tmp_path: Path):
    spec = tmp_path / "job.toml"
    spec.write_text(
        'year = 2026\ndevice = "supernote-nomad"\nmonth = 1\nnotes_pages = 1\n',
        encoding="utf-8",
    )
    out = tmp_path / "job.pdf"
    assert main(["press", str(spec), "-o", str(out)]) == 0
    assert out.is_file()
    dests = _named_dests(PdfReader(out))
    assert "2026-01-01" in dests
    assert "2026-01-31" in dests


def test_cli_load_keeps_toml_overlay_under_month_flag():
    spec = _load_spec("examples/mvp-typo-overlay.toml", year=None, month=1)
    assert spec.months == (1,)
    assert spec.type_overlay.chrome == TypePatch(size=9.6, weight="bold")
    assert spec.type_overlay.display == TypePatch(size=48, weight="heavy")
    assert spec.project_index_pages == 3


def test_cli_rejects_unknown_typography(tmp_path: Path, capsys):
    spec = tmp_path / "bad.toml"
    spec.write_text(
        "year = 2026\nmonth = 1\n[typography.overlay]\nschema_version = 1\n"
        "[typography.overlay.cover_year]\nsize = 48\n",
        encoding="utf-8",
    )
    out = tmp_path / "bad.pdf"
    assert main(["press", str(spec), "-o", str(out)]) == 2
    err = capsys.readouterr().err
    assert "unknown step 'cover_year'" in err
    assert not out.exists()


def test_cli_unknown_weight_fails(tmp_path: Path, capsys):
    spec = tmp_path / "hair.toml"
    spec.write_text(
        "year = 2026\nmonth = 1\n[typography.overlay]\nschema_version = 1\n"
        '[typography.overlay.chrome]\nweight = "hairline"\n',
        encoding="utf-8",
    )
    assert main(["press", str(spec), "-o", str(tmp_path / "hair.pdf")]) == 2
    assert "bad weight 'hairline'" in capsys.readouterr().err


def test_cli_version_mismatch_fails(tmp_path: Path, capsys):
    spec = tmp_path / "ver.toml"
    spec.write_text(
        "year = 2026\nmonth = 1\n[typography.overlay]\nschema_version = 99\n"
        "[typography.overlay.chrome]\nsize = 8.6\n",
        encoding="utf-8",
    )
    assert main(["press", str(spec), "-o", str(tmp_path / "ver.pdf")]) == 2
    assert "schema_version" in capsys.readouterr().err


def test_cli_proof_verb_selects_proof_profile(monkeypatch, tmp_path: Path):
    seen: dict[str, object] = {}

    def fake_press(spec, output, **kwargs):
        seen["proof"] = kwargs.get("proof", False)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(b"%PDF-1.4\n")
        return output

    monkeypatch.setattr("parch.press.press", fake_press)
    out = tmp_path / "proof.pdf"
    assert main(["proof", "supernote-nomad", "-o", str(out)]) == 0
    assert seen["proof"] is True


def test_cli_press_proof_flag_selects_proof_profile(monkeypatch, tmp_path: Path):
    seen: dict[str, object] = {}

    def fake_press(spec, output, **kwargs):
        seen["proof"] = kwargs.get("proof", False)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(b"%PDF-1.4\n")
        return output

    monkeypatch.setattr("parch.press.press", fake_press)
    out = tmp_path / "flag.pdf"
    assert main(["press", "supernote-nomad", "--proof", "-o", str(out)]) == 0
    assert seen["proof"] is True


def test_cli_press_without_proof_stays_device_only(monkeypatch, tmp_path: Path):
    seen: dict[str, object] = {}

    def fake_press(spec, output, **kwargs):
        seen["proof"] = kwargs.get("proof", False)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(b"%PDF-1.4\n")
        return output

    monkeypatch.setattr("parch.press.press", fake_press)
    out = tmp_path / "plain.pdf"
    assert main(["press", "supernote-nomad", "-o", str(out)]) == 0
    assert seen["proof"] is False


def test_cli_proof_verb_plus_flag_stays_true(monkeypatch, tmp_path: Path):
    seen: dict[str, object] = {}

    def fake_press(spec, output, **kwargs):
        seen["proof"] = kwargs.get("proof", False)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(b"%PDF-1.4\n")
        return output

    monkeypatch.setattr("parch.press.press", fake_press)
    out = tmp_path / "both.pdf"
    assert main(["proof", "supernote-nomad", "--proof", "-o", str(out)]) == 0
    assert seen["proof"] is True
    assert PROOF_PROFILE.overlay.display is None


def test_cli_press_scribe_id_is_known(monkeypatch, tmp_path: Path):
    seen: dict[str, object] = {}

    def fake_press(spec, output, **kwargs):
        seen["device"] = spec.device
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(b"%PDF-1.4\n")
        return output

    monkeypatch.setattr("parch.press.press", fake_press)
    out = tmp_path / "scribe.pdf"
    assert main(["press", "kindle-scribe", "-o", str(out)]) == 0
    assert seen["device"] == "kindle-scribe"
    assert main(["press", "scribe", "-o", str(out)]) == 0
    assert seen["device"] == "scribe"


def test_press_scribe_page_geometry(tmp_path: Path):
    out = tmp_path / "scribe.pdf"
    assert main(["press", "examples/scribe.toml", "-o", str(out)]) == 0
    page = PdfReader(out).pages[0]
    assert float(page.mediabox.width) == pytest.approx(_pt(157.48), abs=0.6)
    assert float(page.mediabox.height) == pytest.approx(_pt(209.97), abs=0.6)

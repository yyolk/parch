from pathlib import Path

import pytest
from pypdf import PdfReader

from parch.press import main, press
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
    # cover + annual + index + 8 leaves + meeting index + 16 dests + 4 quarters + 12 months + 12 habits + 53 weeks + 365 days + 365 notes
    assert len(reader.pages) == 839

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
        'year = 2026\ndevice = "supernote-nomad"\nmonth = 1\nday = 5\nnotes_pages = 1\n',
        encoding="utf-8",
    )
    out = tmp_path / "job.pdf"
    assert main(["press", str(spec), "-o", str(out)]) == 0
    assert out.is_file()
    dests = _named_dests(PdfReader(out))
    assert "2026-01-01" in dests
    assert "2026-01-31" in dests

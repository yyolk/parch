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


def test_press_mvp_pdf(tmp_path: Path):
    out = tmp_path / "mvp.pdf"
    press(Spec(), out)
    assert out.is_file() and out.stat().st_size > 0

    reader = PdfReader(out)
    assert len(reader.pages) == 5

    page = reader.pages[0]
    assert float(page.mediabox.width) == pytest.approx(_pt(118.87), abs=0.6)
    assert float(page.mediabox.height) == pytest.approx(_pt(158.5), abs=0.6)

    dests = _named_dests(reader)
    assert "cover" in dests
    assert "month-2026-01" in dests
    assert "2026-01-05" in dests
    assert "2026-01-05-notes-1" in dests
    assert "2026-01-05-notes-2" in dests
    assert _link_count(reader) >= 1


def test_cli_press_toml(tmp_path: Path):
    spec = tmp_path / "job.toml"
    spec.write_text('year = 2026\ndevice = "supernote-nomad"\nmonth = 1\nday = 5\n', encoding="utf-8")
    out = tmp_path / "job.pdf"
    assert main(["press", str(spec), "-o", str(out)]) == 0
    assert out.is_file()
    assert len(PdfReader(out).pages) == 5

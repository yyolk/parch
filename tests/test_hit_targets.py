"""PDF link annots: Contents mark is a square; each MOS tab is one cell."""

import pytest
from pypdf import PdfReader
from pypdf.generic import DictionaryObject, IndirectObject

from parch.config import load
from parch.services.generate import Generate
from parch.services.preview_svg import sample_page_numbers
from parch.toml_config import parse_toml
from tests.helpers import base_config, load_default
from tests.test_toml_omit_sections import compile_pdf
from tests.toml_fixtures import omit_toml_sections, short_january

NOMAD = base_config("supernote-nomad")
PAPER = base_config("158x210")


def _links(page):
    rows = []
    for annot in page.get("/Annots") or []:
        obj = annot.get_object() if isinstance(annot, IndirectObject) else annot
        if not isinstance(obj, DictionaryObject) or obj.get("/Subtype") != "/Link":
            continue
        x1, y1, x2, y2 = (float(v) for v in obj["/Rect"])
        rows.append((abs(x2 - x1), abs(y2 - y1), min(x1, x2), min(y1, y2)))
    return rows


def _annual_page(reader: PdfReader):
    # Cover, Contents, then Annual on the shipped 158×210 / Nomad jobs.
    return reader.pages[2]


def _calendar_year_dto():
    text = omit_toml_sections(
        PAPER.read_text(encoding="utf-8"),
        ["quarterly", "weekly", "daily", "daily_notes"],
    )
    return parse_toml(text, source="hit-year.toml")


def test_contents_mark_link_is_square(tmp_path):
    dto = short_january(load(PAPER))
    typst = Generate(i18n=load_default()).generate(dto)
    pdf, stderr = compile_pdf(typst, tmp_path / "mark", device="158x210")
    assert pdf.is_file(), stderr
    links = _links(_annual_page(PdfReader(str(pdf))))
    squares = [row for row in links if abs(row[0] - row[1]) < 0.5 and row[0] > 20]
    assert len(squares) == 1
    width, height, _x, _y = squares[0]
    assert width == pytest.approx(height, abs=0.01)
    assert 25 < width < 50


def test_mos_tab_links_are_one_cell_each(tmp_path):
    typst = Generate(i18n=load_default()).generate(_calendar_year_dto())
    pdf, stderr = compile_pdf(typst, tmp_path / "mos", device="158x210")
    assert pdf.is_file(), stderr
    links = _links(_annual_page(PdfReader(str(pdf))))
    mos = [row for row in links if row[2] < 8]
    assert len(mos) == 12
    heights = sorted(row[1] for row in mos)
    widths = sorted(row[0] for row in mos)
    assert heights[0] == pytest.approx(heights[-1], abs=0.05)
    assert widths[0] == pytest.approx(widths[-1], abs=0.05)
    assert 24 < widths[0] < 32
    assert 20 < heights[0] < 40
    ys = sorted(row[3] for row in mos)
    for prev, nxt in zip(ys, ys[1:]):
        assert nxt == pytest.approx(prev + heights[0], abs=1.0)


def test_nomad_topband_chips_are_equal_cells(tmp_path):
    dto = short_january(load(NOMAD))
    typst = Generate(i18n=load_default()).generate(dto)
    pdf, stderr = compile_pdf(typst, tmp_path / "topband")
    assert pdf.is_file(), stderr
    page = _annual_page(PdfReader(str(pdf)))
    height = float(page.mediabox.height)
    links = _links(page)
    top_y = max(row[3] for row in links)
    strip = [row for row in links if abs(row[3] - top_y) < 3]
    assert len(strip) >= 6
    widths = sorted(row[0] for row in strip)
    heights = sorted(row[1] for row in strip)
    assert widths[0] == pytest.approx(widths[-1], abs=2.0)
    assert heights[0] == pytest.approx(heights[-1], abs=2.0)
    assert 18 < widths[0] < 70


def test_nomad_calendar_day_cells_are_link_annots(tmp_path):
    """Live Jan 1–14 days are PDF links on annual, quarterly, and daily mini-cal."""
    dto = short_january(load(NOMAD))
    typst = Generate(i18n=load_default()).generate(dto)
    pdf, stderr = compile_pdf(typst, tmp_path / "nomad-days")
    assert pdf.is_file(), stderr
    reader = PdfReader(str(pdf))
    pages = sample_page_numbers(
        typst,
        year=2026,
        week_id="2026W01",
        jan1="2026-01-01",
        stems=("annual", "quarterly-q1", "daily-jan1"),
    )
    annual = _links(reader.pages[pages["annual"] - 1])
    days = [row for row in annual if 10 < row[0] < 20 and 6 < row[1] < 12]
    assert len(days) >= 14
    quarterly = _links(reader.pages[pages["quarterly-q1"] - 1])
    qdays = [row for row in quarterly if 10 < row[0] < 20 and 5 < row[1] < 12]
    assert len(qdays) >= 14
    daily = _links(reader.pages[pages["daily-jan1"] - 1])
    mini = [row for row in daily if 12 < row[0] < 22 and 5 < row[1] < 9]
    assert len(mini) >= 14
    tempo = [row for row in daily if row[0] > 80 and 10 < row[1] < 16]
    assert len(tempo) >= 3


def test_nomad_daily_tempo_and_weekly_day_are_link_annots(tmp_path):
    """Daily Jan/Q tempo and weekly Day chip must be live PDF links."""
    dto = short_january(load(NOMAD))
    typst = Generate(i18n=load_default()).generate(dto)
    pdf, stderr = compile_pdf(typst, tmp_path / "nomad-tempo-day")
    assert pdf.is_file(), stderr
    reader = PdfReader(str(pdf))
    pages = sample_page_numbers(
        typst,
        year=2026,
        week_id="2026W01",
        jan1="2026-01-01",
        stems=("daily-jan1", "weekly-w01"),
    )
    daily = _links(reader.pages[pages["daily-jan1"] - 1])
    tempo = [row for row in daily if row[0] > 80 and 10 < row[1] < 16]
    assert len(tempo) >= 3
    top_y = max(row[3] for row in daily)
    strip = [row for row in daily if abs(row[3] - top_y) < 3]
    assert len(strip) >= 6
    weekly = _links(reader.pages[pages["weekly-w01"] - 1])
    wtop = max(row[3] for row in weekly)
    wstrip = [row for row in weekly if abs(row[3] - wtop) < 3]
    assert len(wstrip) >= 6

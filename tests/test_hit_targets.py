"""PDF link annots: Contents mark is a square; each MOS tab is one cell."""

import pytest
from pypdf import PdfReader
from pypdf.generic import DictionaryObject, IndirectObject

from parch.config import load
from parch.services.generate import Generate
from parch.toml_config import parse_toml
from tests.helpers import base_config, load_default
from tests.test_toml_omit_sections import compile_pdf
from tests.toml_fixtures import omit_toml_sections, short_january

NOMAD = base_config("supernote-nomad")


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
    # Cover, Contents, then Annual on the shipped Nomad job.
    return reader.pages[2]


def _calendar_year_dto():
    text = omit_toml_sections(
        NOMAD.read_text(encoding="utf-8"),
        ["quarterly", "weekly", "daily", "daily_notes"],
    )
    return parse_toml(text, source="hit-year.toml")


def test_contents_mark_link_is_square(tmp_path):
    dto = short_january(load(NOMAD))
    typst = Generate(i18n=load_default()).generate(dto)
    pdf, stderr = compile_pdf(typst, tmp_path / "mark")
    assert pdf.is_file(), stderr
    links = _links(_annual_page(PdfReader(str(pdf))))
    squares = [row for row in links if abs(row[0] - row[1]) < 0.5 and row[0] > 20]
    assert len(squares) == 1
    width, height, _x, _y = squares[0]
    assert width == pytest.approx(height, abs=0.01)
    assert 28 < width < 36


def test_mos_tab_links_are_one_cell_each(tmp_path):
    typst = Generate(i18n=load_default()).generate(_calendar_year_dto())
    pdf, stderr = compile_pdf(typst, tmp_path / "mos")
    assert pdf.is_file(), stderr
    links = _links(_annual_page(PdfReader(str(pdf))))
    mos = [row for row in links if row[2] < 8]
    assert len(mos) == 12
    heights = sorted(row[1] for row in mos)
    widths = sorted(row[0] for row in mos)
    assert heights[0] == pytest.approx(heights[-1], abs=0.05)
    assert widths[0] == pytest.approx(widths[-1], abs=0.05)
    assert 18 < widths[0] < 26
    assert 20 < heights[0] < 40
    ys = sorted(row[3] for row in mos)
    for prev, nxt in zip(ys, ys[1:]):
        assert nxt == pytest.approx(prev + heights[0], abs=1.0)

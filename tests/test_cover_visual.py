"""Raster check that the Nomad cover matches locked 00-cover well rhythm."""


from PIL import Image

from parch.services.generate import Generate
from parch.toml_config import parse_toml
from tests.test_toml_omit_sections import SECTIONS, compile_pdf
from tests.toml_fixtures import omit_toml_sections
from tests.visual import full_width_bands, ink_bbox, raster_page
from tests.helpers import base_config, load_default

NOMAD = base_config("supernote-nomad")
_DPI = 200
_OTHERS = [name for name in SECTIONS if name != "cover"]


def _generate(dto) -> str:
    return Generate(i18n=load_default()).generate(dto)


def test_cover_year_matches_locked_well(tmp_path):
    text = omit_toml_sections(NOMAD.read_text(encoding="utf-8"), _OTHERS)
    dto = parse_toml(text, source="visual-cover.toml")
    typst = _generate(dto)
    pdf, stderr = compile_pdf(typst, tmp_path / "cover")
    assert pdf.is_file() and pdf.stat().st_size > 0, stderr
    png = raster_page(pdf, 1, tmp_path / "cover.png", dpi=_DPI)
    with Image.open(png) as src:
        height = src.size[1]
    box = ink_bbox(png)
    assert box is not None
    _x0, y0, _x1, y1 = box
    # Locked 00-cover: v(1fr) year v(1.15fr). Not the old 1fr/2fr upper third.
    assert height * 0.32 < y0 < height * 0.50, (box, height)
    assert height * 0.48 < y1 < height * 0.68, (box, height)
    # No phantom page-shell hair under the toolbar when strip is none.
    top = int(_DPI * 10 / 25.4)
    bands = full_width_bands(png, x0_frac=0.04, coverage=0.7)
    assert all(band_y0 > top for band_y0, _y1, _t in bands), (bands, top)

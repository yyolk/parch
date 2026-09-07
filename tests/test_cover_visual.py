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


def _center_ink_bands(png, *, dark: int = 80) -> list[tuple[int, int]]:
    """Coalesce dark rows in the center 30% (year digits + 42mm rules)."""
    with Image.open(png) as src:
        im = src.convert("L")
        width, height = im.size
        pixels = im.load()
    x0, x1 = int(width * 0.35), int(width * 0.65)
    rows = [
        y
        for y in range(height)
        if any(pixels[x, y] <= dark for x in range(x0, x1))
    ]
    bands: list[tuple[int, int]] = []
    i = 0
    while i < len(rows):
        start = end = rows[i]
        i += 1
        while i < len(rows) and rows[i] == end + 1:
            end = rows[i]
            i += 1
        bands.append((start, end))
    return bands


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
    cluster = _center_ink_bands(png)
    assert len(cluster) >= 3, cluster
    year, rule1, rule2 = cluster[0], cluster[1], cluster[2]
    mm = lambda px: px / _DPI * 25.4
    year_to_rules = mm(rule1[0] - year[1] - 1)
    rule_to_rule = mm(rule2[0] - rule1[1] - 1)
    assert 3.2 <= year_to_rules <= 5.0, (year_to_rules, cluster)
    assert 0.45 <= rule_to_rule <= 1.0, (rule_to_rule, cluster)

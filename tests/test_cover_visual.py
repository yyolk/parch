"""Raster check that the Nomad cover matches the 2026-09-07 bake."""


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
    # No phantom page-shell hair under the toolbar when strip is none.
    top = int(_DPI * 10 / 25.4)
    bands = full_width_bands(png, x0_frac=0.04, coverage=0.7)
    assert all(band_y0 > top for band_y0, _y1, _t in bands), (bands, top)
    cluster = _center_ink_bands(png)
    assert len(cluster) >= 3, cluster
    year, rule1, rule2 = cluster[0], cluster[1], cluster[2]
    year_mid = (year[0] + year[1]) / 2 / height
    rules_mid = (rule1[0] + rule2[1]) / 2 / height
    mm = lambda px: px / _DPI * 25.4
    rule_to_rule = mm(rule2[0] - rule1[1] - 1)
    # Year optically centered on the full page; rules straddle lower third.
    assert 0.46 <= year_mid <= 0.54, (year_mid, cluster)
    assert 0.63 <= rules_mid <= 0.70, (rules_mid, cluster)
    assert 5.0 <= rule_to_rule <= 6.2, (rule_to_rule, cluster)

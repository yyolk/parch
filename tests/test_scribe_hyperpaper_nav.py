"""Scribe-family Hyperpaper nav exploration. Nomad stays on mos_strip."""

import pytest
from pypdf import PdfReader

from parch.config import load
from parch.devices import (
    KINDLE_SCRIBE,
    KINDLE_SCRIBE_11,
    KINDLE_SCRIBE_COLORSOFT,
    SCRIBE_FAMILY_IDS,
    SUPERNOTE_NOMAD,
    is_scribe_family,
)
from parch.models.device import DEVICE_SCALE, device_page_margin, device_scale
from parch.mos.preamble import Preamble, render_device_typ
from parch.mos.scribe_nav import (
    INDEX_SKIP,
    RAIL_EDGE_CLEAR,
    RAIL_LABELS,
    RAIL_PAD,
    RAIL_SKIP,
    rail_section_names,
    scribe_hyperpaper_nav,
    section_dest_id,
    section_name_for_page_id,
)
from parch.mos.configurator import Configurator
from parch.services.generate import Generate
from parch.services.preview_svg import sample_page_numbers
from parch.toml_config import apply_hand
from tests.helpers import base_config, load_default
from tests.toml_fixtures import short_january
from tests.test_toml_omit_sections import compile_pdf
from tests.visual import header_rail_adjacent_ink_x, raster_page


def _generate(stem: str, *, extras: bool = False, hand: str | None = None) -> str:
    dto = short_january(load(base_config(stem, extras=extras)))
    if hand is not None:
        dto = apply_hand(dto, hand)
    return Generate(i18n=load_default()).generate(dto)


def _pages(typst: str) -> list[str]:
    return typst.split("#pagebreak()")


def _page_with(typst: str, needle: str) -> str:
    for page in _pages(typst):
        if needle in page:
            return page
    raise AssertionError(f"no page matching {needle!r}")


def test_scribe_family_ids_and_aliases():
    assert SCRIBE_FAMILY_IDS == {
        "kindle-scribe",
        "kindle-scribe-11",
        "kindle-scribe-colorsoft",
    }
    assert is_scribe_family("kindle-scribe")
    assert is_scribe_family("scribe")
    assert is_scribe_family("scribe-11")
    assert is_scribe_family("colorsoft")
    assert not is_scribe_family("supernote-nomad")
    assert not is_scribe_family("nomad")
    assert not is_scribe_family("158x210")
    assert not is_scribe_family("remarkable-1")


def test_scribe_scale_lock_keeps_toolbar_none():
    for device in (KINDLE_SCRIBE, KINDLE_SCRIBE_11, KINDLE_SCRIBE_COLORSOFT):
        assert device.toolbar_edge == "none"
        assert device.toolbar_clearance == "0mm"
        assert device.writing_clearance == "0mm"
        assert device.mos_width == "11mm"
        scale = device.scale()
        assert DEVICE_SCALE[device.id] == scale
        assert device_scale(device.id) == scale
        margin = device_page_margin(scale)
        assert margin["top"] == "0mm"
        assert margin["right"] == "0mm"
        assert "26.25mm" not in margin.values()
        assert "27.94mm" not in margin.values()
        typ = render_device_typ(device)
        assert "#let toolbar-edge = none\n" in typ
        assert "#let toolbar-clearance = 0mm\n" in typ
        assert "#let writing-clearance = 0mm\n" in typ
        assert "#let mos-width = 11mm\n" in typ
    assert SUPERNOTE_NOMAD.writing_clearance == "4mm"
    assert SUPERNOTE_NOMAD.mos_width == "8mm"
    assert SUPERNOTE_NOMAD.toolbar_clearance == "8mm"


def test_scribe_hyperpaper_nav_is_device_gated():
    scribe = Configurator(load(base_config("kindle-scribe")))
    nomad = Configurator(load(base_config("supernote-nomad")))
    paper = Configurator(load(base_config("158x210")))
    assert scribe_hyperpaper_nav(scribe) is True
    assert scribe_hyperpaper_nav(Configurator(load(base_config("kindle-scribe-11")))) is True
    assert scribe_hyperpaper_nav(Configurator(load(base_config("kindle-scribe-colorsoft")))) is True
    assert scribe_hyperpaper_nav(nomad) is False
    assert scribe_hyperpaper_nav(paper) is False


def test_rail_maps_enabled_sections_and_skips_chrome():
    dto = load(base_config("kindle-scribe", extras=True))
    cfg = Configurator(dto)
    names = rail_section_names(cfg)
    assert "cover" not in names
    assert "index" not in names
    assert "colophon" not in names
    assert names[0] == "annual"
    assert "daily_notes" in names
    assert "projects" in names
    assert "meetings" in names
    assert RAIL_LABELS["daily_notes"] == "Notes"
    assert section_dest_id("annual", cfg) == "annual"
    assert section_dest_id("daily_notes", cfg).startswith("daily-note-")
    assert section_name_for_page_id("annual") == "annual"
    assert section_name_for_page_id("2026W01") == "weekly"
    assert section_name_for_page_id("2026-01-01") == "daily"
    assert section_name_for_page_id("month-2026-01-01") == "monthly"
    assert INDEX_SKIP == {"cover", "index", "daily_notes"}
    assert RAIL_SKIP == {"cover", "index", "colophon"}


_HOME_CHIP = (
    "padded_link(<index>, box(inset: (x: 1.5mm, y: 0.8mm), "
    "stroke: regular_stroke, [Contents]))"
)
_CONTENT_NEEDLES = (
    "2026<annual>",
    "Week 1 <2026W01>",
    "January<month-2026-01-01>",
    "text(size: h1)[1 <2026-01-01>]",
)


def test_scribe_content_pages_use_section_rail_and_nav_header():
    typst = _generate("kindle-scribe")
    assert "#let nav_header = nav_header.with(height: 10mm, air: 5mm, stroke: regular_stroke)" in typst
    assert "#let section_rail = section_rail.with(stroke: regular_stroke, turn: 270deg, pad: 4mm)" in typst
    annual = _page_with(typst, "2026<annual>")
    assert "#mos_frame(\n  left," in annual
    assert "section_rail(" in annual
    assert "nav_header(" in annual
    assert "mos_strip(" not in annual
    assert "well_frame(" not in annual
    assert "[Calendar]" in annual
    assert "[Notes]" in annual
    assert "padded_link(<index>" in annual
    assert "[Contents]" in annual
    annual_head = annual[annual.index("nav_header(") :]
    assert "contents_bars" not in annual_head
    assert annual_head.startswith(f"nav_header({_HOME_CHIP},")
    assert "side: left" in annual_head[: annual_head.index("\n")]
    weekly = _page_with(typst, "Week 1 <2026W01>")
    assert "section_rail(" in weekly
    assert "nav_header(" in weekly
    assert "mos_strip(" not in weekly
    assert "[Weeks]" in weekly
    assert "Dec 29 – Jan 4" in weekly
    assert "trail_heading(" in weekly
    assert "shrink: true" in weekly
    heading = weekly[weekly.index("nav_header(") : weekly.index("week_matrix(")]
    assert "trail_heading(" in heading
    assert "shrink: true" in heading
    assert "contents_bars" not in heading
    assert "[Contents]" in heading
    assert heading.startswith(f"nav_header({_HOME_CHIP},")
    assert "side: left" in heading


def test_scribe_contents_chip_slot_stable_for_both_hands():
    """Contents is rail-adjacent; same emit slot on every content page; no five-bar."""
    for hand in ("left", "right"):
        typst = _generate("kindle-scribe", hand=hand)
        for needle in _CONTENT_NEEDLES:
            page = _page_with(typst, needle)
            head = page[page.index("nav_header(") :]
            assert head.startswith(f"nav_header({_HOME_CHIP},")
            assert f"side: {hand}" in head
            assert "contents_bars" not in head[:500]
            if hand == "left":
                assert "#mos_frame(\n  left," in page
            else:
                assert "#mos_frame(\n  right," in page


def test_scribe_index_is_full_bleed_brand_without_mos_rail():
    typst = _generate("kindle-scribe")
    index = _page_with(typst, "[Contents <index>]")
    assert "fill: black" in index
    assert "fill: white" in index
    assert "#mos_frame(" not in index
    assert "section_rail(" not in index
    assert "mos_strip(" not in index
    assert "padded_link(<annual>" in index
    cover = _pages(typst)[0]
    assert "fill: black" in cover
    assert "[parch]" in cover
    assert "#mos_frame(" not in cover
    assert "section_rail(" not in cover


def test_nomad_uses_topband_158_keeps_month_mos_strip():
    nomad = _generate("supernote-nomad")
    annual = _page_with(nomad, "2026<annual>")
    assert "page-shell(" in annual
    assert "section-strip(" in annual
    assert "mos_strip(" not in annual
    assert "section_rail(" not in annual
    assert "nav_header(" not in annual
    index = _page_with(nomad, "[Contents <index>]")
    assert "fill: black" in index
    paper = _generate("158x210")
    paper_annual = _page_with(paper, "2026<annual>")
    assert "mos_strip(" in paper_annual
    assert "section_rail(" not in paper_annual
    assert "nav_header(" not in paper_annual
    assert "page-shell(" not in paper_annual
    assert "well_frame(" in paper_annual
    paper_index = _page_with(paper, "[Contents <index>]")
    assert "fill: black" not in paper_index
    assert "15mm" not in paper_index.split("rows:", 1)[1].split("\n", 1)[0]


def test_scribe_right_hand_keeps_mos_frame_side():
    typst = _generate("kindle-scribe", hand="right")
    annual = _page_with(typst, "2026<annual>")
    assert "#mos_frame(\n  right," in annual
    assert "side: right" in annual
    assert "#mos_frame(\n  left," not in annual
    head = annual[annual.index("nav_header(") :]
    assert head.startswith(f"nav_header({_HOME_CHIP},")
    assert "side: right" in head
    assert "contents_bars" not in head[:500]


def test_scribe_preamble_binds_explor_helpers():
    typst = Preamble(Configurator(load(base_config("kindle-scribe")))).generate()
    imported = typst[typst.index('#import "house.typ"') :].splitlines()[0]
    assert "nav_header" in imported
    assert "section_rail" in imported
    assert f"rail-clearance: {RAIL_EDGE_CLEAR}" in typst
    assert f"pad: {RAIL_PAD}" in typst
    assert "cetz" not in typst.lower()
    nomad = Preamble(Configurator(load(base_config("supernote-nomad")))).generate()
    assert "rail-clearance:" not in nomad


def test_scribe_daily_and_notes_use_short_crumb_and_keep_heading_in_well():
    """Tall Nomad day grid stays in the well; nav_header gets a one-line crumb."""
    typst = _generate("kindle-scribe")
    daily = _page_with(typst, "text(size: h1)[1 <2026-01-01>]")
    assert "trail_heading(text(size: h1)[Thursday 1], [], shrink: true)" in daily
    assert daily.index("trail_heading(text(size: h1)[Thursday 1]") < daily.index("rows: (3fr, 2fr)")
    assert daily.index("rows: (3fr, 2fr)") < daily.index("daily_well(")
    assert daily.index("text(size: h1)[1 <2026-01-01>]") < daily.index("daily_well(")
    assert "[*Thursday*]" in daily
    assert "Week 1" in daily
    assert "well_frame(" in daily
    assert "highlight: <2026-01-01>" in daily
    notes = _page_with(typst, "1 <daily-note-2026-01-01-page-1>")
    assert "trail_heading(text(size: h1)[Notes], [], shrink: true)" in notes
    assert notes.index("trail_heading(text(size: h1)[Notes]") < notes.index("rows: (3fr, 2fr)")
    assert notes.index("rows: (3fr, 2fr)") < notes.index("lined_well(")
    assert notes.index("1 <daily-note-2026-01-01-page-1>") < notes.index("lined_well(")
    assert "[*Thursday*]" in notes
    nomad = _generate("supernote-nomad")
    nomad_daily = _page_with(nomad, "Thursday · January 1 <2026-01-01>")
    assert "text(size: h1)[Thursday 1]" not in nomad_daily
    assert "page-shell(" in nomad_daily
    assert "nomad_daily_well(" in nomad_daily
    assert "daily_well(left" not in nomad_daily
    assert "daily_well(right" not in nomad_daily
    assert "mos_frame(" not in nomad_daily


def _link_rects(page):
    from pypdf.generic import DictionaryObject, IndirectObject

    rows = []
    for annot in page.get("/Annots") or []:
        obj = annot.get_object() if isinstance(annot, IndirectObject) else annot
        if not isinstance(obj, DictionaryObject) or obj.get("/Subtype") != "/Link":
            continue
        x1, y1, x2, y2 = (float(v) for v in obj["/Rect"])
        rows.append((min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2)))
    return rows


def test_scribe_rail_links_clear_page_turn_strip_both_hands(tmp_path):
    """MOS-side annots stay off the Kindle edge; mid/lower cells match the top."""
    mm = 72 / 25.4
    clear = 10 * mm
    for hand in ("left", "right"):
        typst = _generate("kindle-scribe", extras=True, hand=hand)
        pdf, stderr = compile_pdf(
            typst, tmp_path / f"scribe-rail-{hand}", device="kindle-scribe"
        )
        assert pdf.is_file() and pdf.stat().st_size > 0, stderr
        pages = sample_page_numbers(
            typst, year=2026, week_id="2026W01", jan1="2026-01-01", stems=("annual",)
        )
        page = PdfReader(str(pdf)).pages[pages["annual"] - 1]
        width = float(page.mediabox.width)
        height = float(page.mediabox.height)
        rects = _link_rects(page)
        slim = [r for r in rects if 15.0 < (r[2] - r[0]) < 26.0]
        if hand == "right":
            rail = [r for r in slim if r[2] > width - 22 * mm]
            edge = [r[2] for r in rail]
            assert edge, (hand, slim)
            assert max(edge) <= width - clear
        else:
            rail = [r for r in slim if r[0] < 22 * mm]
            edge = [r[0] for r in rail]
            assert edge, (hand, slim)
            assert min(edge) >= clear
        assert len(rail) >= 6
        widths = sorted(r[2] - r[0] for r in rail)
        assert widths[0] == pytest.approx(widths[-1], abs=2.5)
        mid_y = height / 2
        lower = [r for r in rail if r[1] < mid_y]
        upper = [r for r in rail if r[3] > mid_y]
        assert lower and upper, (hand, len(rail))
        if hand == "right":
            assert max(r[2] for r in lower) == pytest.approx(max(r[2] for r in upper), abs=1.0)
        else:
            assert min(r[0] for r in lower) == pytest.approx(min(r[0] for r in upper), abs=1.0)


def test_scribe_short_january_compiles(tmp_path):
    typst = _generate("kindle-scribe", extras=True)
    pdf, stderr = compile_pdf(typst, tmp_path / "scribe-nav", device="kindle-scribe")
    assert pdf.is_file() and pdf.stat().st_size > 0, stderr


def test_scribe_contents_chip_pixels_stable_both_hands(tmp_path):
    """Contents hugs the rail; x is constant per hand and flips with MOS side."""
    stems = ("annual", "weekly-w01", "monthly-jan")
    xs: dict[str, list[int]] = {}
    for hand in ("left", "right"):
        typst = _generate("kindle-scribe", hand=hand)
        pdf, stderr = compile_pdf(typst, tmp_path / f"scribe-{hand}", device="kindle-scribe")
        assert pdf.is_file() and pdf.stat().st_size > 0, stderr
        pages = sample_page_numbers(
            typst, year=2026, week_id="2026W01", jan1="2026-01-01", stems=stems
        )
        found = []
        for stem in stems:
            png = raster_page(pdf, pages[stem], tmp_path / f"{hand}-{stem}.png")
            found.append(header_rail_adjacent_ink_x(png, rail=hand))
        assert max(found) - min(found) <= 2, (hand, found)
        xs[hand] = found
    assert xs["left"][0] < 200
    assert xs["right"][0] > 700

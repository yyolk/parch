"""Scribe-family Hyperpaper nav exploration. Nomad stays on mos_strip."""

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
    RAIL_LABELS,
    RAIL_SKIP,
    rail_section_names,
    scribe_hyperpaper_nav,
    section_dest_id,
    section_name_for_page_id,
)
from parch.mos.configurator import Configurator
from parch.services.generate import Generate
from parch.toml_config import apply_hand
from tests.helpers import base_config, load_default
from tests.toml_fixtures import short_january
from tests.test_toml_omit_sections import compile_pdf


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
    assert "contents_bars(size:" in annual
    weekly = _page_with(typst, "Week 1 <2026W01>")
    assert "section_rail(" in weekly
    assert "nav_header(" in weekly
    assert "mos_strip(" not in weekly
    assert "[Weeks]" in weekly
    assert "Dec 29 – Jan 4" in weekly


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


def test_nomad_and_158_keep_month_mos_strip():
    for stem in ("supernote-nomad", "158x210"):
        typst = _generate(stem)
        annual = _page_with(typst, "2026<annual>")
        assert "mos_strip(" in annual
        assert "section_rail(" not in annual
        assert "nav_header(" not in annual
        assert "well_frame(" in annual
        index = _page_with(typst, "[Contents <index>]")
        assert "fill: black" not in index
        assert "15mm" not in index.split("rows:", 1)[1].split("\n", 1)[0]


def test_scribe_right_hand_keeps_mos_frame_side():
    typst = _generate("kindle-scribe", hand="right")
    annual = _page_with(typst, "2026<annual>")
    assert "#mos_frame(\n  right," in annual
    assert "side: right" in annual
    assert "#mos_frame(\n  left," not in annual


def test_scribe_preamble_binds_explor_helpers():
    typst = Preamble(Configurator(load(base_config("kindle-scribe")))).generate()
    imported = typst[typst.index('#import "house.typ"') :].splitlines()[0]
    assert "nav_header" in imported
    assert "section_rail" in imported
    assert "cetz" not in typst.lower()


def test_scribe_short_january_compiles(tmp_path):
    typst = _generate("kindle-scribe", extras=True)
    pdf, stderr = compile_pdf(typst, tmp_path / "scribe-nav", device="kindle-scribe")
    assert pdf.is_file() and pdf.stat().st_size > 0, stderr

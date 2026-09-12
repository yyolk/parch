import pytest

from parch import ConfigError
from parch.devices import NOMAD, SCRIBE, get_device, known_device_ids
from parch.fonts import ROOT_BODY, Pt
from parch.layouts.planner.painters import NAV_H, paint_nav, well_rect
from parch.plotter import RecordingPlotter


def test_nomad_geometry():
    assert NOMAD.id == "supernote-nomad"
    assert NOMAD.page_width == 118.87
    assert NOMAD.page_height == 158.5
    assert NOMAD.width_px == 1404
    assert NOMAD.height_px == 1872
    assert NOMAD.ppi == 300
    assert NOMAD.toolbar_edge == "top"
    assert NOMAD.toolbar_clearance == 8.0
    assert NOMAD.writing_clearance == 4.0
    assert NOMAD.bottom_clearance == 0.0
    assert NOMAD.root_body == ROOT_BODY == Pt(8.5)


def test_toolbar_is_not_the_well():
    slab = NOMAD.toolbar_slab()
    assert slab is not None
    assert slab.y == 0
    assert slab.h == 8.0
    frame = NOMAD.content_frame()
    assert frame.y == 8.0
    assert frame.x == 4.0
    assert frame.bottom == pytest.approx(158.5 - 4.0)


def test_scribe_geometry():
    assert SCRIBE.id == "kindle-scribe"
    assert SCRIBE.name == "Kindle Scribe (1st gen)"
    assert SCRIBE.page_width == 157.48
    assert SCRIBE.page_height == 209.97
    assert SCRIBE.width_px == 1860
    assert SCRIBE.height_px == 2480
    assert SCRIBE.ppi == 300
    assert SCRIBE.toolbar_edge == "none"
    assert SCRIBE.toolbar_clearance == 0.0
    assert SCRIBE.writing_clearance == 4.0
    assert SCRIBE.bottom_clearance > 0
    assert SCRIBE.root_body == ROOT_BODY == Pt(8.5) == NOMAD.root_body
    assert SCRIBE.toolbar_slab() is None
    frame = SCRIBE.content_frame()
    assert frame.x == 4.0
    assert frame.y == 0.0
    assert frame.w == pytest.approx(157.48 - 8.0)
    assert frame.bottom == pytest.approx(209.97 - 4.0 - SCRIBE.bottom_clearance)


def test_bottom_clearance_seats_strip_and_well():
    assert NOMAD.bottom_clearance == 0.0
    assert SCRIBE.bottom_clearance > 0
    assert well_rect(NOMAD).bottom == pytest.approx(NOMAD.page_height - NAV_H - 2.2)
    assert well_rect(SCRIBE).bottom == pytest.approx(
        SCRIBE.page_height - SCRIBE.bottom_clearance - NAV_H - 2.2
    )
    assert NOMAD.content_frame().bottom == pytest.approx(
        NOMAD.page_height - NOMAD.writing_clearance
    )
    assert SCRIBE.content_frame().bottom == pytest.approx(
        SCRIBE.page_height - SCRIBE.writing_clearance - SCRIBE.bottom_clearance
    )
    nomad = RecordingPlotter()
    paint_nav(nomad, NOMAD, (("Year", "year-2026"),), "Year")
    scribe = RecordingPlotter()
    paint_nav(scribe, SCRIBE, (("Year", "year-2026"),), "Year")
    nomad_strip = next(op[1] for op in nomad.ops if op[0] == "rect")
    scribe_strip = next(op[1] for op in scribe.ops if op[0] == "rect")
    assert nomad_strip.y == pytest.approx(NOMAD.page_height - NAV_H)
    assert nomad_strip.bottom == pytest.approx(NOMAD.page_height)
    assert scribe_strip.y == pytest.approx(
        SCRIBE.page_height - SCRIBE.bottom_clearance - NAV_H
    )
    assert scribe_strip.bottom == pytest.approx(
        SCRIBE.page_height - SCRIBE.bottom_clearance
    )


def test_device_aliases():
    assert get_device("nomad") is NOMAD
    assert get_device("supernote-nomad") is NOMAD
    assert get_device("kindle-scribe") is SCRIBE
    assert get_device("scribe") is SCRIBE
    with pytest.raises(ConfigError, match="MVP knows supernote-nomad, kindle-scribe"):
        get_device("unknown-slate")


def test_known_device_ids_are_canonical():
    assert known_device_ids() == ("supernote-nomad", "kindle-scribe")
    assert "nomad" not in known_device_ids()
    assert "scribe" not in known_device_ids()

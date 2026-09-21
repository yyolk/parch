from dataclasses import replace

import pytest

from parch import ConfigError
from parch.devices import NAV_H, NOMAD, SCRIBE, get_device, known_device_ids
from parch.fonts import ROOT_BODY, Pt


def test_nomad_geometry():
    assert NOMAD.id == "supernote-nomad"
    assert NOMAD.page_width == 118.87
    assert NOMAD.page_height == 158.5
    assert NOMAD.width_px == 1404
    assert NOMAD.height_px == 1872
    assert NOMAD.ppi == 300
    assert NOMAD.top_clearance == 8.0
    assert NOMAD.content_top == 8.0
    assert NOMAD.writing_clearance == 4.0
    assert NOMAD.bottom_clearance == 0.0
    assert NOMAD.root_body == ROOT_BODY == Pt(8.5)


def test_top_clearance_is_not_the_well():
    frame = NOMAD.content_frame()
    assert frame.y == 8.0
    assert frame.x == 4.0
    assert frame.bottom == pytest.approx(158.5 - NAV_H)


def test_page_rect_is_full_physical_page():
    for device in (NOMAD, SCRIBE):
        page = device.page_rect()
        assert page.x == 0.0
        assert page.y == 0.0
        assert page.w == pytest.approx(device.page_width)
        assert page.h == pytest.approx(device.page_height)
        frame = device.content_frame()
        assert page.w > frame.w
        assert page.h > frame.h


def test_scribe_geometry():
    assert SCRIBE.id == "kindle-scribe"
    assert SCRIBE.name == "Kindle Scribe (1st gen)"
    assert SCRIBE.page_width == 157.48
    assert SCRIBE.page_height == 209.97
    assert SCRIBE.width_px == 1860
    assert SCRIBE.height_px == 2480
    assert SCRIBE.ppi == 300
    assert SCRIBE.top_clearance == 8.0
    assert SCRIBE.content_top == SCRIBE.top_clearance == 8.0
    assert SCRIBE.writing_clearance == 4.0
    assert SCRIBE.bottom_clearance == 10.0
    assert SCRIBE.root_body == ROOT_BODY == Pt(8.5) == NOMAD.root_body
    frame = SCRIBE.content_frame()
    assert frame.x == 4.0
    assert frame.y == 8.0
    assert frame.w == pytest.approx(157.48 - 8.0)
    assert frame.bottom == pytest.approx(209.97 - NAV_H - SCRIBE.bottom_clearance)


def test_zero_top_clearance_is_content_top_zero():
    bare = replace(NOMAD, top_clearance=0.0)
    assert bare.content_top == 0.0


def test_get_device_top_clearance_override():
    """Omit keeps the registered Device; ``0`` returns a copy with no top band."""
    assert get_device("kindle-scribe") is SCRIBE
    bare = get_device("kindle-scribe", top_clearance=0.0)
    assert bare is not SCRIBE
    assert bare.top_clearance == 0.0
    assert bare.content_top == 0.0


def test_bottom_clearance_seats_content_frame():
    assert NOMAD.bottom_clearance == 0.0
    assert SCRIBE.bottom_clearance == 10.0
    assert NOMAD.content_frame().bottom == pytest.approx(NOMAD.page_height - NAV_H)
    assert SCRIBE.content_frame().bottom == pytest.approx(
        SCRIBE.page_height - NAV_H - SCRIBE.bottom_clearance
    )


def test_device_aliases():
    assert get_device("nomad") is NOMAD
    assert get_device("supernote-nomad") is NOMAD
    assert get_device("kindle-scribe") is SCRIBE
    assert get_device("scribe") is SCRIBE
    with pytest.raises(
        ConfigError, match="known devices: supernote-nomad, kindle-scribe"
    ):
        get_device("unknown-slate")


def test_known_device_ids_are_canonical():
    assert known_device_ids() == ("supernote-nomad", "kindle-scribe")
    assert "nomad" not in known_device_ids()
    assert "scribe" not in known_device_ids()

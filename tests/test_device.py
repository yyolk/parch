from parch.devices import NOMAD, get_device
from parch.fonts import TypeOverlay, JostRamp, EffectiveRamp
from parch import ConfigError
import pytest


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


def test_toolbar_is_not_the_well():
    slab = NOMAD.toolbar_slab()
    assert slab is not None
    assert slab.y == 0
    assert slab.h == 8.0
    frame = NOMAD.content_frame()
    assert frame.y == 8.0
    assert frame.x == 4.0
    assert frame.bottom == pytest.approx(158.5 - 4.0)


def test_nomad_alias():
    assert get_device("nomad") is NOMAD
    with pytest.raises(ConfigError):
        get_device("kindle-scribe")


def test_nomad_type_overlay_is_identity():
    assert isinstance(NOMAD.type_overlay, TypeOverlay)
    assert NOMAD.type_overlay == TypeOverlay()
    empty = EffectiveRamp(overlay=NOMAD.type_overlay)
    jost = JostRamp()
    for role in ("cover_year", "cover_brow", "page_title", "chrome"):
        assert empty.ink(role) == jost.ink(role)

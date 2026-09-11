from parch.devices import NOMAD, NOMAD_TYPE_OVERLAY, get_device
from parch.fonts import EffectiveRamp, JOST_FAMILY_OVERLAY, TypeInk, TypeOverlay
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


def test_nomad_supplies_jost_family_overlay():
    assert NOMAD.type_overlay is NOMAD_TYPE_OVERLAY
    assert NOMAD.type_overlay is JOST_FAMILY_OVERLAY
    assert isinstance(NOMAD.type_overlay, TypeOverlay)
    for role_patch in (
        NOMAD.type_overlay.cover_year,
        NOMAD.type_overlay.cover_brow,
        NOMAD.type_overlay.page_title,
        NOMAD.type_overlay.chrome,
    ):
        assert role_patch is not None
        assert role_patch.family == "jost"
        assert role_patch.size is None
        assert role_patch.weight is None
    ramp = EffectiveRamp(overlay=NOMAD.type_overlay)
    assert ramp.ink("chrome") == TypeInk(family="jost", weight="book", size=7.4)
    assert ramp.ink("cover_year") == TypeInk(family="jost", weight="heavy", size=42)
    assert ramp.ink("page_title") == TypeInk(family="jost", weight="medium", size=11)

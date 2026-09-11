from parch.devices import (
    NOMAD,
    NOMAD_CHROME_SIZE,
    NOMAD_CHROME_WEIGHT,
    NOMAD_COVER_BROW_SIZE,
    get_device,
)
from parch.fonts import TypeInk, TypeOverlay, EffectiveRamp
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


def test_nomad_supplies_type_overlay():
    assert isinstance(NOMAD.type_overlay, TypeOverlay)
    assert NOMAD.type_overlay.chrome is not None
    assert NOMAD.type_overlay.chrome.size == NOMAD_CHROME_SIZE
    assert NOMAD.type_overlay.chrome.weight == NOMAD_CHROME_WEIGHT
    assert NOMAD.type_overlay.cover_brow is not None
    assert NOMAD.type_overlay.cover_brow.size == NOMAD_COVER_BROW_SIZE
    assert NOMAD.type_overlay.cover_brow.weight is None
    ramp = EffectiveRamp(overlay=NOMAD.type_overlay)
    assert ramp.ink("chrome") == TypeInk(
        family="jost", weight=NOMAD_CHROME_WEIGHT, size=NOMAD_CHROME_SIZE
    )
    assert ramp.ink("page_title") == TypeInk(family="jost", weight="medium", size=11)

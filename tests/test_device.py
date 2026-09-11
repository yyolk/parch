import pytest

from parch import ConfigError
from parch.devices import NOMAD, NOMAD_TYPE_OVERLAY, get_device
from parch.fonts import (
    OVERLAY_SCHEMA_VERSION,
    ROOT_BODY,
    TYPE_STEPS,
    EffectiveRamp,
    JostRamp,
    OverlayOk,
    TypeOverlay,
    jost_defaults,
    validate_overlay,
)


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
    assert NOMAD.root_body == ROOT_BODY == 8.5


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


def test_nomad_supplies_identity_type_overlay():
    assert isinstance(NOMAD.type_overlay, TypeOverlay)
    assert NOMAD.type_overlay == TypeOverlay()
    assert NOMAD_TYPE_OVERLAY == TypeOverlay()
    assert NOMAD.type_overlay.schema_version == OVERLAY_SCHEMA_VERSION
    result = validate_overlay(NOMAD.type_overlay, jost_defaults())
    assert isinstance(result, OverlayOk)
    ramp = EffectiveRamp(overlay=NOMAD.type_overlay)
    jost = JostRamp()
    for step in TYPE_STEPS:
        assert ramp.ink(step) == jost.ink(step)
        assert ramp.ink(step, "strong") == jost.ink(step, "strong")
    assert get_device("supernote-nomad") is NOMAD

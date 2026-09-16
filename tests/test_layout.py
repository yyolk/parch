import pytest

from parch.books import YearPlanner
from parch.devices import NAV_H, NOMAD, SCRIBE
from parch.fonts.ramp import EffectiveRamp
from parch.layouts.planner.layout import well_rect
from parch.layouts.planner.painters import (
    HEADER_H,
    WASH,
    paint_header,
    paint_top_clearance,
)
from parch.plotter import RecordingPlotter
from parch.spec import Spec

TOP_CLEARANCE = 8.0


def test_top_clearance_wash_fills_slab():
    for device in (NOMAD, SCRIBE):
        plotter = RecordingPlotter()
        paint_top_clearance(plotter, device)
        fills = [op for op in plotter.ops if op[0] == "rect"]
        assert len(fills) == 1
        box = fills[0][1]
        assert box.y == pytest.approx(0.0)
        assert box.h == pytest.approx(device.top_clearance)
        assert box.w == pytest.approx(device.page_width)
        assert fills[0][2] is False
        assert fills[0][3] is True
        assert fills[0][5] == pytest.approx(WASH)
        assert not any(op[0] == "text" for op in plotter.ops)
        assert not any(op[0] == "link" for op in plotter.ops)


def test_content_stays_below_top_clearance():
    spec = Spec()
    plotter = RecordingPlotter()
    YearPlanner().plot(spec, plotter)

    clearance_fills = [
        op
        for op in plotter.ops
        if op[0] == "rect" and op[1].y == 0 and op[1].h == TOP_CLEARANCE
    ]
    assert clearance_fills
    assert all(op[3] and op[5] == pytest.approx(WASH) for op in clearance_fills)

    texts = [op[2] for op in plotter.ops if op[0] == "text"]
    assert "toolbar 8 mm - not a well" not in texts

    frame = NOMAD.content_frame()
    assert frame.y == TOP_CLEARANCE
    for op in plotter.ops:
        if op[0] == "text":
            assert op[1].y >= TOP_CLEARANCE - 0.01
        if op[0] == "rect" and not (op[1].y == 0 and op[1].h == TOP_CLEARANCE):
            assert op[1].y >= TOP_CLEARANCE - 0.01


def test_scribe_header_sits_below_tap_floor():
    """Measured Send-to-Kindle: taps solid from ~8 mm; header chip/meta sit there."""
    plotter = RecordingPlotter()
    paint_header(
        plotter,
        SCRIBE,
        "Year",
        "2026",
        chip="01",
        ramp=EffectiveRamp(),
    )
    slabs = [
        op
        for op in plotter.ops
        if op[0] == "rect"
        and op[3]
        and op[1].y == pytest.approx(SCRIBE.content_top)
        and op[1].h == pytest.approx(HEADER_H)
    ]
    assert slabs
    assert slabs[0][1].y == pytest.approx(8.0)
    assert slabs[0][1].h == pytest.approx(9.0)
    for op in plotter.ops:
        if op[0] in {"rect", "text"}:
            assert op[1].y >= TOP_CLEARANCE - 0.01


def test_well_sits_above_strip_and_clearance():
    for device in (NOMAD, SCRIBE):
        strip_y = device.page_height - device.bottom_clearance - NAV_H
        assert well_rect(device).bottom + 2.2 == pytest.approx(strip_y)
        assert device.content_frame().bottom == pytest.approx(strip_y)

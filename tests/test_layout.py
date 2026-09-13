import pytest

from parch.books import YearPlanner
from parch.components import CoverTitle
from parch.devices import NOMAD, SCRIBE
from parch.devices.registry import Device
from parch.fonts.ramp import EffectiveRamp
from parch.layouts.planner.painters import NAV_H, paint_cover, paint_nav
from parch.plotter import RecordingPlotter
from parch.spec import Spec

TOOLBAR = 8.0
OUTER = 3.2
INNER = 4.6


def test_content_stays_below_toolbar():
    spec = Spec()
    plotter = RecordingPlotter()
    YearPlanner().plot(spec, plotter)

    toolbar_fills = [
        op
        for op in plotter.ops
        if op[0] == "rect" and op[1].y == 0 and op[1].h == TOOLBAR
    ]
    assert not toolbar_fills, "toolbar slab must stay unmarked"

    texts = [op[2] for op in plotter.ops if op[0] == "text"]
    assert "toolbar 8 mm - not a well" not in texts

    frame = NOMAD.content_frame()
    assert frame.y == TOOLBAR
    for op in plotter.ops:
        if op[0] == "text":
            assert op[1].y >= TOOLBAR - 0.01
        if op[0] == "rect":
            assert op[1].y >= TOOLBAR - 0.01


def _cover(device: Device) -> CoverTitle:
    return CoverTitle(
        year=2026,
        subtitle="",
        device_name=device.id,
        cta_label="",
        cta_dest="year-2026",
    )


def _frame_bottoms(device: Device) -> tuple[float, float]:
    """paint_cover outer / inner bottoms."""
    outer_pad = max(OUTER, device.bottom_clearance + 0.6)
    inner_pad = max(INNER, device.bottom_clearance + 1.8)
    return device.page_height - outer_pad, device.page_height - inner_pad


def test_nav_wash_runs_through_bottom_clearance():
    items = (("Year", "year-2026"), ("Mon", "month-2026-01"))
    nomad = RecordingPlotter()
    paint_nav(nomad, NOMAD, items, "Year", ramp=EffectiveRamp())
    scribe = RecordingPlotter()
    paint_nav(scribe, SCRIBE, items, "Year", ramp=EffectiveRamp())
    nomad_wash = next(op[1] for op in nomad.ops if op[0] == "rect" and op[3])
    scribe_wash = next(op[1] for op in scribe.ops if op[0] == "rect" and op[3])
    assert nomad_wash.h == pytest.approx(NAV_H)
    assert nomad_wash.bottom == pytest.approx(NOMAD.page_height)
    assert scribe_wash.h == pytest.approx(NAV_H + SCRIBE.bottom_clearance)
    assert scribe_wash.bottom == pytest.approx(SCRIBE.page_height)
    for hit in (op[1] for op in scribe.ops if op[0] == "link"):
        assert hit.h == pytest.approx(NAV_H)
        assert hit.bottom == pytest.approx(SCRIBE.page_height - SCRIBE.bottom_clearance)


def test_cover_frames_stop_above_bottom_clearance():
    nomad = RecordingPlotter()
    paint_cover(nomad, NOMAD, _cover(NOMAD), ramp=EffectiveRamp())
    scribe = RecordingPlotter()
    paint_cover(scribe, SCRIBE, _cover(SCRIBE), ramp=EffectiveRamp())
    nomad_frames = [
        op[1] for op in nomad.ops if op[0] == "rect" and op[2] and not op[3]
    ]
    scribe_frames = [
        op[1] for op in scribe.ops if op[0] == "rect" and op[2] and not op[3]
    ]
    assert [box.bottom for box in nomad_frames] == pytest.approx(
        list(_frame_bottoms(NOMAD))
    )
    assert [box.bottom for box in scribe_frames] == pytest.approx(
        list(_frame_bottoms(SCRIBE))
    )
    assert not any(op[3] for op in scribe.ops if op[0] == "rect")
    assert not any(op[3] for op in nomad.ops if op[0] == "rect")

import pytest

from parch.books import YearPlanner, plot_pages
from parch.devices import NAV_H, NOMAD, SCRIBE
from parch.fonts.ramp import EffectiveRamp
from parch.layouts.planner.layout import PlannerLayout, well_rect
from parch.layouts.planner.painters import HEADER_H, INK, paint_header
from parch.plotter import RecordingPlotter
from parch.sections.annual import AnnualSection
from parch.sections.cover import CoverSection
from parch.spec import Spec

TOP_CLEARANCE = 8.0


def test_header_owns_top_clearance():
    """One INK rect from y=0 through top_clearance + HEADER_H. Hits stay at content_top."""
    for device in (NOMAD, SCRIBE):
        plotter = RecordingPlotter()
        paint_header(
            plotter,
            device,
            "Year",
            "2026",
            chip="01",
            ramp=EffectiveRamp(),
        )
        fills = [op for op in plotter.ops if op[0] == "rect" and op[3]]
        assert len(fills) == 1
        box = fills[0][1]
        assert box.y == pytest.approx(0.0)
        assert box.h == pytest.approx(device.top_clearance + HEADER_H)
        assert box.w == pytest.approx(device.page_width)
        assert fills[0][2] is False
        assert fills[0][5] == pytest.approx(INK)
        for op in plotter.ops:
            if op[0] in {"text", "link"}:
                assert op[1].y == pytest.approx(device.content_top)
                assert op[1].h == pytest.approx(HEADER_H)


def test_content_stays_below_top_clearance():
    spec = Spec()
    plotter = RecordingPlotter()
    YearPlanner().plot(spec, plotter)

    header_bands = [
        op
        for op in plotter.ops
        if op[0] == "rect"
        and op[3]
        and op[1].y == pytest.approx(0.0)
        and op[1].h == pytest.approx(TOP_CLEARANCE + HEADER_H)
        and op[1].w == pytest.approx(NOMAD.page_width)
    ]
    assert header_bands
    assert all(op[5] == pytest.approx(INK) for op in header_bands)

    wash_only = [
        op
        for op in plotter.ops
        if op[0] == "rect"
        and op[1].y == pytest.approx(0.0)
        and op[1].h == pytest.approx(TOP_CLEARANCE)
    ]
    assert not wash_only

    texts = [op[2] for op in plotter.ops if op[0] == "text"]
    assert "toolbar 8 mm - not a well" not in texts

    frame = NOMAD.content_frame()
    assert frame.y == TOP_CLEARANCE
    for op in plotter.ops:
        if op[0] == "text":
            assert op[1].y >= TOP_CLEARANCE - 0.01
        if op[0] == "rect" and not (
            op[1].y == pytest.approx(0.0)
            and op[1].h == pytest.approx(TOP_CLEARANCE + HEADER_H)
        ):
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
    fills = [op for op in plotter.ops if op[0] == "rect" and op[3]]
    assert len(fills) == 1
    assert fills[0][1].y == pytest.approx(0.0)
    assert fills[0][1].h == pytest.approx(SCRIBE.top_clearance + HEADER_H)
    assert fills[0][5] == pytest.approx(INK)
    for op in plotter.ops:
        if op[0] in {"text", "link"}:
            assert op[1].y == pytest.approx(SCRIBE.content_top)
            assert op[1].y >= TOP_CLEARANCE - 0.01


def test_plot_pages_honors_spec_top_clearance():
    """Year-planner paint path applies Spec.top_clearance to the slate."""
    spec = Spec(device="kindle-scribe", top_clearance=0.0, months=(1,), notes_pages=0)
    plotter = RecordingPlotter()
    plot_pages(
        AnnualSection(spec).pages,
        plotter,
        ramp=EffectiveRamp(),
        device=spec.device,
        top_clearance=spec.top_clearance,
    )
    fills = [
        op
        for op in plotter.ops
        if op[0] == "rect"
        and op[3]
        and op[1].y == pytest.approx(0.0)
        and op[1].w == pytest.approx(SCRIBE.page_width)
        and op[5] == pytest.approx(INK)
    ]
    assert fills
    assert all(op[1].h == pytest.approx(HEADER_H) for op in fills)
    for op in plotter.ops:
        if op[0] in {"text", "link"}:
            assert op[1].y >= -0.01


def test_cover_has_no_top_fill():
    page = CoverSection(Spec()).pages()[0]
    for device in (NOMAD, SCRIBE):
        ink = RecordingPlotter()
        PlannerLayout().paint(page, ink, device)
        top_fills = [
            op
            for op in ink.ops
            if op[0] == "rect"
            and op[3]
            and op[1].y == pytest.approx(0.0)
            and op[1].w == pytest.approx(device.page_width)
        ]
        assert not top_fills


def test_well_sits_above_strip_and_clearance():
    for device in (NOMAD, SCRIBE):
        strip_y = device.page_height - device.bottom_clearance - NAV_H
        assert well_rect(device).bottom + 2.2 == pytest.approx(strip_y)
        assert device.content_frame().bottom == pytest.approx(strip_y)

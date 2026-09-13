import pytest

from parch.books import YearPlanner
from parch.devices import NAV_H, NOMAD, SCRIBE
from parch.layouts.planner.layout import well_rect
from parch.plotter import RecordingPlotter
from parch.spec import Spec

TOOLBAR = 8.0


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


def test_well_sits_above_strip_and_clearance():
    for device in (NOMAD, SCRIBE):
        strip_y = device.page_height - device.bottom_clearance - NAV_H
        assert well_rect(device).bottom + 2.2 == pytest.approx(strip_y)
        assert device.content_frame().bottom == pytest.approx(strip_y)

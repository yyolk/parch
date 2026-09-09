from parch.books import YearPlanner
from parch.devices import NOMAD
from parch.geom import Rect
from parch.plotter import RecordingPlotter
from parch.spec import Spec

TOOLBAR = 8.0


def _well_rects(plotter: RecordingPlotter) -> list[Rect]:
    """Outer stroked wells: schedule/notes boxes and month cells sit at y >= 8."""
    boxes = []
    for op in plotter.ops:
        if op[0] == "rect":
            box = op[1]
            if box.y >= TOOLBAR - 0.01 and box.h > 20:
                boxes.append(box)
    return boxes


def test_content_stays_below_toolbar():
    spec = Spec()
    plotter = RecordingPlotter()
    YearPlanner().plot(spec, plotter)

    toolbar_fills = [
        op
        for op in plotter.ops
        if op[0] == "rect" and op[1].y == 0 and op[1].h == TOOLBAR
    ]
    assert toolbar_fills, "toolbar slab should be painted"

    for box in _well_rects(plotter):
        assert box.y >= TOOLBAR

    frame = NOMAD.content_frame()
    assert frame.y == TOOLBAR
    for op in plotter.ops:
        if op[0] == "text" and op[2] in {"Schedule", "Notes"}:
            assert op[1].y >= TOOLBAR

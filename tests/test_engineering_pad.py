import pytest

from parch import ConfigError
from parch.books import YearPlanner
from parch.components import EngineeringPad
from parch.devices.registry import NOMAD, SCRIBE
from parch.layouts.planner import PlannerLayout
from parch.layouts.planner.painters import (
    HEADER_H,
    PAD_MAJOR_GRAY,
    PAD_MAJOR_W,
    PAD_MINOR_GRAY,
    PAD_MINOR_PER_MAJOR,
    PAD_MINOR_PITCH,
    PAD_MINOR_W,
    engineering_pad_grid,
    engineering_pad_well,
    paint_engineering_pad,
)
from parch.plotter import RecordingPlotter
from parch.sections.engineering_pad import EngineeringPadSection
from parch.spec import Spec


def _pair(spec: Spec | None = None) -> tuple[EngineeringPad, EngineeringPad]:
    pages = EngineeringPadSection(spec or Spec()).pages()
    front = next(c for c in pages[0].components if isinstance(c, EngineeringPad))
    back = next(c for c in pages[1].components if isinstance(c, EngineeringPad))
    return front, back


def test_section_builds_one_duplex_pair():
    spec = Spec()
    pages = EngineeringPadSection(spec).pages()
    assert len(pages) == 2
    assert [page.kind for page in pages] == ["engineering_pad", "engineering_pad"]
    assert [page.dest for page in pages] == [
        "engineering-pad-2026-front",
        "engineering-pad-2026-back",
    ]
    assert pages[0].title == pages[1].title == "Engineering"
    assert pages[0].nav == ()
    assert pages[1].nav == ()
    front, back = _pair(spec)
    assert front.face == "front"
    assert back.face == "back"
    assert front.year == back.year == 2026
    assert front.other_dest == "engineering-pad-2026-back"
    assert back.other_dest == "engineering-pad-2026-front"
    assert type(front) is type(back) is EngineeringPad


def test_spec_dest_is_face_not_a_knob():
    spec = Spec(year=2027)
    assert spec.dest_for_engineering_pad("front") == "engineering-pad-2027-front"
    assert spec.dest_for_engineering_pad("back") == "engineering-pad-2027-back"
    with pytest.raises(ConfigError, match="front or back"):
        spec.dest_for_engineering_pad("verso")


def test_year_planner_appends_the_pair():
    spec = Spec(months=(1,), notes_pages=0)
    dests = [page.dest for page in YearPlanner().pages(spec)]
    assert dests[-2:] == [
        "engineering-pad-2026-front",
        "engineering-pad-2026-back",
    ]
    assert dests.count("engineering-pad-2026-front") == 1
    kinds = [page.kind for page in YearPlanner().pages(spec)]
    assert kinds.count("engineering_pad") == 2


def test_pad_well_has_no_hole_margin():
    for device in (NOMAD, SCRIBE):
        for face in ("front", "back"):
            well = engineering_pad_well(device, face)
            assert well.x == pytest.approx(device.writing_clearance)
            assert well.right == pytest.approx(
                device.page_width - device.writing_clearance
            )
            assert well.x == pytest.approx(device.page_width - well.right)


def test_front_well_sits_under_header_back_does_not():
    front = engineering_pad_well(NOMAD, "front")
    back = engineering_pad_well(NOMAD, "back")
    assert front.y == pytest.approx(NOMAD.content_top + HEADER_H + 2.2)
    assert back.y == pytest.approx(NOMAD.content_top + NOMAD.writing_clearance)
    assert back.y < front.y
    assert back.h > front.h


def test_grid_is_five_by_five_major_minor():
    well = engineering_pad_well(NOMAD, "back")
    grid, majors_x, majors_y, pitch = engineering_pad_grid(well)
    assert pitch == PAD_MINOR_PITCH == 5.0
    assert PAD_MINOR_PER_MAJOR == 5
    assert majors_x >= 1 and majors_y >= 1
    assert grid.w == pytest.approx(majors_x * 5 * pitch)
    assert grid.h == pytest.approx(majors_y * 5 * pitch)
    assert grid.x >= well.x - 1e-9
    assert grid.right <= well.right + 1e-9


def test_one_painter_branches_on_face():
    front, back = _pair()
    device = NOMAD
    front_ink = RecordingPlotter()
    back_ink = RecordingPlotter()
    paint_engineering_pad(front_ink, device, front)
    paint_engineering_pad(back_ink, device, back)

    front_text = [op[2] for op in front_ink.ops if op[0] == "text"]
    assert "Engineering" in front_text
    assert "2026" in front_text
    assert "GRID" in front_text
    assert front_ink.links() == ["engineering-pad-2026-back"]
    front_lines = [op for op in front_ink.ops if op[0] == "line"]
    assert front_lines == []
    well = engineering_pad_well(device, "front")
    frames = [
        op
        for op in front_ink.ops
        if op[0] == "rect" and not op[3] and op[1].w == pytest.approx(well.w)
    ]
    assert len(frames) == 1

    back_text = [op[2] for op in back_ink.ops if op[0] == "text"]
    assert back_text == []
    assert [op for op in back_ink.ops if op[0] == "rect"] == []
    lines = [op for op in back_ink.ops if op[0] == "line"]
    grid, majors_x, majors_y, pitch = engineering_pad_grid(
        engineering_pad_well(device, "back")
    )
    nx = majors_x * 5
    ny = majors_y * 5
    assert len(lines) == (nx + 1) + (ny + 1)
    majors = [op for op in lines if op[5] == PAD_MAJOR_W and op[6] == PAD_MAJOR_GRAY]
    minors = [op for op in lines if op[5] == PAD_MINOR_W and op[6] == PAD_MINOR_GRAY]
    assert len(majors) == (majors_x + 1) + (majors_y + 1)
    assert len(minors) == len(lines) - len(majors)
    xs = sorted({round(op[1], 5) for op in lines if op[1] == op[3]})
    assert xs[1] - xs[0] == pytest.approx(pitch)
    assert (xs[-1] - xs[0]) / pitch == pytest.approx(nx)


def test_layout_skips_planner_chrome_for_both_faces():
    spec = Spec(months=(1,), notes_pages=0)
    pages = [p for p in YearPlanner().pages(spec) if p.kind == "engineering_pad"]
    layout = PlannerLayout()
    for page in pages:
        ink = RecordingPlotter()
        layout.paint(page, ink, NOMAD)
        labels = [op[2] for op in ink.ops if op[0] == "text"]
        assert "Year" not in labels
        assert "Habit" not in labels


def test_no_hole_marks_on_either_face():
    front, back = _pair()
    for pad in (front, back):
        ink = RecordingPlotter()
        paint_engineering_pad(ink, NOMAD, pad)
        tiny = [
            op for op in ink.ops if op[0] == "rect" and op[1].w < 3.0 and op[1].h < 3.0
        ]
        assert tiny == []

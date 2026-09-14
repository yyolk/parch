from pathlib import Path

from parch.books import YearPlanner
from parch.components.pad import PadFace
from parch.devices import get_device
from parch.layouts.planner import PlannerLayout
from parch.layouts.planner.painters import (
    PAD_FIELDS,
    PAD_MAJOR_G,
    PAD_MAJOR_W,
    PAD_MINOR_G,
    PAD_MINOR_W,
)
from parch.plotter import RecordingPlotter
from parch.sections.pad import PadSection
from parch.spec import Spec


def _paint(spec: Spec) -> RecordingPlotter:
    device = get_device(spec.device)
    plotter = RecordingPlotter()
    layout = PlannerLayout()
    for page in PadSection(spec).pages():
        plotter.reserve_dest(page.dest)
        plotter.begin_page()
        plotter.add_dest(page.dest)
        layout.paint(page, plotter, device)
    return plotter


def _ops_on_page(plotter: RecordingPlotter, page: int) -> list:
    current = 0
    found: list = []
    for op in plotter.ops:
        if op[0] == "begin_page":
            current = op[1]
            continue
        if current == page:
            found.append(op)
    return found


def _lines(ops: list) -> list:
    return [op for op in ops if op[0] == "line"]


def _texts(ops: list) -> list[str]:
    return [op[2] for op in ops if op[0] == "text"]


def _major_lines(ops: list) -> list:
    return [op for op in _lines(ops) if op[5] == PAD_MAJOR_W and op[6] == PAD_MAJOR_G]


def test_default_year_planner_omits_pad():
    pages = YearPlanner().pages(Spec())
    assert not any(page.kind.startswith("pad_") for page in pages)
    assert "pad-2026-01-front" not in [page.dest for page in pages]


def test_pages_knob_emits_duplex_pairs():
    none = PadSection(Spec()).pages()
    one = PadSection(Spec(pad_pages=1)).pages()
    two = PadSection(Spec(pad_pages=2)).pages()
    assert none == []
    assert [page.dest for page in one] == ["pad-2026-01-front", "pad-2026-01-back"]
    assert [page.kind for page in one] == ["pad_front", "pad_back"]
    assert [page.dest for page in two] == [
        "pad-2026-01-front",
        "pad-2026-01-back",
        "pad-2026-02-front",
        "pad-2026-02-back",
    ]
    assert all(isinstance(page.components[0], PadFace) for page in one)
    year = YearPlanner().pages(Spec(pad_pages=1, notes_pages=0, months=(1,)))
    assert [page.dest for page in year[:3]] == [
        "cover",
        "pad-2026-01-front",
        "pad-2026-01-back",
    ]


def test_front_is_header_and_blank_well():
    plotter = _paint(Spec(pad_pages=1))
    front = _ops_on_page(plotter, 1)
    back = _ops_on_page(plotter, 2)
    assert _texts(front) == list(PAD_FIELDS)
    assert len(_lines(front)) == 4
    assert not _major_lines(front)
    fills = [op for op in front if op[0] == "rect" and op[3]]
    assert not fills
    assert "Subject" not in _texts(back)
    assert "Date" not in _texts(back)


def test_back_is_grid_without_header():
    plotter = _paint(Spec(pad_pages=1))
    back = _ops_on_page(plotter, 2)
    assert _texts(back) == []
    assert len(_lines(back)) > 20
    assert _major_lines(back)
    minors = [
        op for op in _lines(back) if op[5] == PAD_MINOR_W and op[6] == PAD_MINOR_G
    ]
    assert minors
    fills = [op for op in back if op[0] == "rect" and op[3]]
    assert not fills


def test_header_off_clears_front_fields():
    on = _ops_on_page(_paint(Spec(pad_pages=1, pad_header=True)), 1)
    off = _ops_on_page(_paint(Spec(pad_pages=1, pad_header=False)), 1)
    assert _texts(on) == list(PAD_FIELDS)
    assert _texts(off) == []
    assert _lines(off) == []
    assert len(_lines(on)) == 4


def test_grid_pitch_changes_back_line_count():
    fine = _lines(_ops_on_page(_paint(Spec(pad_pages=1, pad_grid_pitch_mm=4.0)), 2))
    coarse = _lines(_ops_on_page(_paint(Spec(pad_pages=1, pad_grid_pitch_mm=8.0)), 2))
    assert len(fine) > len(coarse)
    assert len(coarse) > 8


def test_major_every_changes_major_count():
    tight = _major_lines(_ops_on_page(_paint(Spec(pad_pages=1, pad_major_every=4)), 2))
    loose = _major_lines(_ops_on_page(_paint(Spec(pad_pages=1, pad_major_every=10)), 2))
    assert len(tight) > len(loose)
    assert loose


def test_example_toml_knobs():
    spec = Spec.from_path(Path("examples/pad.toml"))
    pages = PadSection(spec).pages()
    assert len(pages) == 2
    face = pages[1].components[0]
    assert isinstance(face, PadFace)
    assert face.face == "back"
    assert face.grid_pitch_mm == 5.0
    assert face.major_every == 5
    assert face.header is True

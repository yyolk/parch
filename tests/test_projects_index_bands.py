import pytest

from parch.books import YearPlanner
from parch.components import ProjectLeaf, ProjectsBoard, ProjectsIndexBands
from parch.devices.nomad import NOMAD
from parch.geom import Rect
from parch.layouts.planner import PlannerLayout
from parch.layouts.planner.layout import well_rect
from parch.layouts.planner.painters import (
    INDEX_BAND_GAP,
    INDEX_BAND_LABELS,
    PROJECT_P,
    TICK,
    paint_project_leaf,
    paint_projects_index_bands,
    projects_index_band_seats,
    projects_index_bands,
    strip_active,
    strip_items,
)
from parch.plotter import RecordingPlotter
from parch.sections.projects_index_bands import INDEX_ROWS, ProjectsIndexBandsSection
from parch.spec import Spec


def _index_page(spec: Spec | None = None):
    spec = spec or Spec(notes_pages=1)
    return ProjectsIndexBandsSection(spec).pages()[0]


def test_index_bands_not_in_year_book():
    kinds = [page.kind for page in YearPlanner().pages(Spec(notes_pages=1))]
    dests = [page.dest for page in YearPlanner().pages(Spec(notes_pages=1))]
    assert kinds.count("projects") == 1
    assert "projects_index_bands" not in kinds
    assert "project" not in kinds
    assert "projects-index-bands-2026" not in dests
    page = next(p for p in YearPlanner().pages(Spec(notes_pages=1)) if p.kind == "projects")
    assert any(isinstance(item, ProjectsBoard) for item in page.components)
    assert not any(isinstance(item, ProjectsIndexBands) for item in page.components)


def test_projects_index_bands_page_and_leaves():
    spec = Spec(notes_pages=1)
    pages = ProjectsIndexBandsSection(spec).pages()
    assert len(pages) == 1 + 3 * INDEX_ROWS
    index = pages[0]
    assert index.dest == "projects-index-bands-2026"
    assert index.kind == "projects_index_bands"
    assert index.title == "Projects"
    board = next(item for item in index.components if isinstance(item, ProjectsIndexBands))
    assert board.year == 2026
    assert [band.label for band in board.bands] == list(INDEX_BAND_LABELS)
    assert INDEX_BAND_LABELS == ("Active", "Waiting", "Done")
    assert all(len(band.rows) == INDEX_ROWS for band in board.bands)

    dests = [page.dest for page in pages[1:]]
    assert dests == [f"project-2026-{n:02d}" for n in range(1, 3 * INDEX_ROWS + 1)]
    assert dests == [row.dest for band in board.bands for row in band.rows]
    leaf = pages[1]
    assert leaf.kind == "project"
    assert leaf.title == "Project"
    card = next(item for item in leaf.components if isinstance(item, ProjectLeaf))
    assert card.year == 2026
    assert card.tasks == 4
    assert card.index_dest == index.dest


def test_proj_tab_points_at_index():
    spec = Spec(notes_pages=1)
    pages = ProjectsIndexBandsSection(spec).pages()
    index = pages[0]
    leaf = pages[1]
    expected = (
        ("Year", "year-2026"),
        ("Proj", "projects-index-bands-2026"),
        ("Quar", "quarter-2026-Q1"),
        ("Mon", "month-2026-01"),
        ("Habit", "month-2026-01-habits"),
        ("Week", "week-2026-W01"),
        ("Day", "2026-01-01"),
        ("Notes", "2026-01-01-notes-1"),
    )
    assert strip_items(index) == expected
    assert strip_items(leaf) == expected
    assert strip_active(index.kind) == "Proj"
    assert strip_active(leaf.kind) == "Proj"
    assert strip_active("projects") == ""


def test_projects_index_band_tracks():
    well = well_rect(NOMAD)
    bands = projects_index_bands(well)
    assert len(bands) == 3
    assert bands[0].y == pytest.approx(well.y)
    assert bands[0].x == pytest.approx(well.x)
    assert bands[0].w == pytest.approx(well.w)
    assert bands[-1].bottom == pytest.approx(well.bottom)
    assert bands[1].y == pytest.approx(bands[0].bottom + INDEX_BAND_GAP)
    leftover = well.h - 2 * INDEX_BAND_GAP
    assert bands[0].h == pytest.approx(leftover / 3)
    assert bands[1].h == pytest.approx(bands[0].h)
    assert bands[2].h == pytest.approx(bands[0].h)

    head, lines = projects_index_band_seats(bands[0], 4)
    assert len(lines) == 4
    assert head.y > bands[0].y
    assert lines[0].y > head.bottom
    assert lines[-1].bottom <= bands[0].bottom
    assert lines[0].x > bands[0].x
    assert lines[0].right < bands[0].right

    five_head, five = projects_index_band_seats(bands[0], 5)
    assert len(five) == 5
    assert five_head.h == pytest.approx(head.h)


def test_projects_index_bands_paint_ticks_and_links():
    spec = Spec(notes_pages=1)
    page = _index_page(spec)
    board = next(item for item in page.components if isinstance(item, ProjectsIndexBands))
    well = well_rect(NOMAD)
    plotter = RecordingPlotter()
    paint_projects_index_bands(plotter, well, board)

    texts = [op[2] for op in plotter.ops if op[0] == "text"]
    assert texts.count("Active") == 1
    assert texts.count("Waiting") == 1
    assert texts.count("Done") == 1
    assert "Todo" not in texts
    assert "Doing" not in texts
    assert "P" not in texts
    assert "PROJECT" not in texts
    assert "Focus" not in texts
    assert "Notes" not in texts

    ticks = [
        op
        for op in plotter.ops
        if op[0] == "rect" and op[2] and not op[3] and op[1].w == pytest.approx(TICK)
    ]
    assert len(ticks) == 3 * INDEX_ROWS

    fills = [op for op in plotter.ops if op[0] == "rect" and op[3]]
    assert fills == []

    outlines = [
        op
        for op in plotter.ops
        if op[0] == "rect" and op[2] and not op[3] and op[1].w == pytest.approx(well.w)
    ]
    assert len(outlines) == 3

    links = plotter.links()
    assert links == [f"project-2026-{n:02d}" for n in range(1, 3 * INDEX_ROWS + 1)]
    hits = [op[1] for op in plotter.ops if op[0] == "link"]
    assert all(hit.w > 20 for hit in hits)


def test_projects_index_bands_knobs():
    spec = Spec(notes_pages=1, project_index_rows=5, project_tasks=5)
    pages = ProjectsIndexBandsSection(spec).pages()
    assert len(pages) == 1 + 15
    board = next(item for item in pages[0].components if isinstance(item, ProjectsIndexBands))
    assert all(len(band.rows) == 5 for band in board.bands)
    plotter = RecordingPlotter()
    paint_projects_index_bands(plotter, Rect(4, 20, 110, 90), board)
    ticks = [
        op
        for op in plotter.ops
        if op[0] == "rect" and op[2] and not op[3] and op[1].w == pytest.approx(TICK)
    ]
    assert len(ticks) == 15
    assert plotter.links()[-1] == "project-2026-15"


def test_index_header_year_and_proj_tab():
    spec = Spec(notes_pages=1)
    page = _index_page(spec)
    plotter = RecordingPlotter()
    plotter.begin_page()
    PlannerLayout().paint(page, plotter, NOMAD)
    texts = [op[2] for op in plotter.ops if op[0] == "text"]
    assert "Projects" in texts
    assert "2026" in texts
    assert "Proj" in texts
    for label in ("Year", "Quar", "Mon", "Habit", "Week", "Day", "Notes"):
        assert label in texts
    assert INDEX_ROWS == 4


def test_project_leaf_back_link_and_g_card():
    spec = Spec(notes_pages=1)
    pages = ProjectsIndexBandsSection(spec).pages()
    leaf = pages[1]
    plotter = RecordingPlotter()
    plotter.begin_page()
    PlannerLayout().paint(leaf, plotter, NOMAD)
    texts = [op[2] for op in plotter.ops if op[0] == "text"]
    assert "Project" in texts
    assert "Index" in texts
    assert "Proj" in texts
    assert "2026" in texts
    links = plotter.links()
    assert "projects-index-bands-2026" in links
    assert links.count("projects-index-bands-2026") >= 2

    board_plotter = RecordingPlotter()
    card = next(item for item in leaf.components if isinstance(item, ProjectLeaf))
    paint_project_leaf(board_plotter, well_rect(NOMAD), card)
    p_boxes = [
        op
        for op in board_plotter.ops
        if op[0] == "rect" and op[2] and not op[3] and op[1].w == pytest.approx(PROJECT_P)
    ]
    assert len(p_boxes) == 1
    assert [op[2] for op in board_plotter.ops if op[0] == "text"].count("P") == 1
    ticks = [
        op
        for op in board_plotter.ops
        if op[0] == "rect" and op[2] and not op[3] and op[1].w == pytest.approx(TICK)
    ]
    assert len(ticks) == 4


def test_experiment_pages_reserve_and_link():
    spec = Spec(notes_pages=1)
    pages = ProjectsIndexBandsSection(spec).pages()
    plotter = RecordingPlotter()
    for page in pages:
        plotter.reserve_dest(page.dest)
    for page in pages:
        plotter.begin_page()
        plotter.add_dest(page.dest)
        PlannerLayout().paint(page, plotter, NOMAD)
    dests = plotter.dests()
    assert dests[0] == "projects-index-bands-2026"
    assert "project-2026-01" in dests
    assert "project-2026-12" in dests
    links = plotter.links()
    assert "project-2026-01" in links
    assert "project-2026-12" in links
    assert "projects-index-bands-2026" in links

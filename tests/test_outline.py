from pathlib import Path

import pytest
from pypdf import PdfReader

from parch import ConfigError
from parch.books import EngineeringNotebook, ProjectsNotebook, YearPlanner
from parch.books.outline import outline_tree
from parch.plotter import RecordingPlotter
from parch.press import press
from parch.spec import Spec


def _jan(*, outline: bool) -> Spec:
    return Spec(months=(1,), notes_pages=0, outline=outline)


def _rows(spec: Spec) -> list[tuple[str, str, int]]:
    dests = {page.dest for page in YearPlanner().pages(spec) if page.kind != "cover"}
    return outline_tree(spec, dests)


def _pdf_outline_rows(path: Path) -> list[tuple[str, int]]:
    items = PdfReader(path).outline or []
    rows: list[tuple[str, int]] = []

    def walk(nodes, level: int) -> None:
        for node in nodes:
            if isinstance(node, list):
                walk(node, level + 1)
                continue
            rows.append((str(node.title), level))
            kids = getattr(node, "children", None)
            if kids:
                walk(kids, level + 1)

    walk(items, 0)
    return rows


def test_outline_defaults_off():
    assert Spec().outline is False
    assert Spec.from_mapping({}).outline is False
    assert Spec.from_mapping({"outline": True}).outline is True
    assert Spec.from_path(Path("examples/nomad-outline.toml")).outline is True
    with pytest.raises(ConfigError, match="outline must be a bool"):
        Spec.from_mapping({"outline": {"enabled": True}})


def test_year_planner_outline_hierarchy_depth():
    spec = _jan(outline=True)
    pages = YearPlanner().pages(spec)
    dests = {page.dest for page in pages}
    rows = _rows(spec)
    levels = {level for _, _, level in rows}
    assert levels == {0, 1, 2, 3}
    assert rows[0] == ("Annual", spec.year_dest, 0)
    assert ("Q1", spec.dest_for_quarter(1), 1) in rows
    assert ("January", spec.dest_for_month(1), 2) in rows
    assert ("Habits", spec.dest_for_habits(1), 3) in rows
    weeks = [row for row in rows if row[0].startswith("Week ") and row[2] == 3]
    assert weeks
    assert all(dest in dests for _, dest, _ in rows)
    assert spec.cover_dest not in {dest for _, dest, _ in rows}
    day_dests = {page.dest for page in pages if page.kind == "daily"}
    assert day_dests
    assert day_dests.isdisjoint({dest for _, dest, _ in rows})
    annual_i = next(i for i, row in enumerate(rows) if row[0] == "Annual")
    projects_i = next(i for i, row in enumerate(rows) if row[0] == "Projects")
    q1_i = next(i for i, row in enumerate(rows) if row[0] == "Q1")
    assert annual_i < q1_i < projects_i
    assert ("Projects", spec.projects_index_dest, 0) in rows
    assert ("Meetings", spec.meetings_index_dest, 0) in rows
    assert ("Tasks", spec.tasks_index_dest, 0) in rows
    assert ("Review", spec.review_index_dest, 0) in rows


def test_engineering_notebook_outline_is_flat():
    spec = Spec(book="engineering-notebook", engineering_sheets=1, outline=True)
    pages = EngineeringNotebook().pages(spec)
    dests = {page.dest for page in pages if page.kind != "cover"}
    front = spec.dest_for_engineering_pad(1, "front")
    assert outline_tree(spec, dests) == [("Engineering", front, 0)]
    assert spec.cover_dest not in {dest for _, dest, _ in outline_tree(spec, dests)}
    plotter = RecordingPlotter()
    EngineeringNotebook().plot(spec, plotter)
    assert plotter.outlines() == [("Engineering", front, 0)]
    assert spec.cover_dest not in {dest for _, dest, _ in plotter.outlines()}


def test_projects_notebook_outline_is_flat():
    spec = Spec(book="projects-notebook", outline=True)
    dests = {
        page.dest
        for page in ProjectsNotebook().pages(spec)
        if page.kind != "cover"
    }
    assert outline_tree(spec, dests) == [("Projects", spec.projects_index_dest, 0)]


def test_outline_disabled_emits_nothing():
    plotter = RecordingPlotter()
    YearPlanner().plot(_jan(outline=False), plotter)
    assert plotter.outlines() == []
    eng = RecordingPlotter()
    EngineeringNotebook().plot(
        Spec(book="engineering-notebook", engineering_sheets=1), eng
    )
    assert eng.outlines() == []


def test_outline_skips_cover_on_plot():
    plotter = RecordingPlotter()
    YearPlanner().plot(_jan(outline=True), plotter)
    dests = {dest for _, dest, _ in plotter.outlines()}
    assert "cover" not in dests
    assert plotter.outlines()[0] == ("Annual", "year-2026", 0)
    titles = [title for title, _, _ in plotter.outlines()]
    assert "Cover" not in titles


def test_press_outline_pdf_hierarchy_and_no_toc_page(tmp_path: Path):
    spec = _jan(outline=True)
    pages = YearPlanner().pages(spec)
    out = tmp_path / "outline.pdf"
    press(spec, out)
    reader = PdfReader(out)
    assert len(reader.pages) == len(pages)
    rows = _pdf_outline_rows(out)
    titles = [title for title, _ in rows]
    assert "cover" not in {t.lower() for t in titles}
    assert titles[0] == "Annual"
    assert "Q1" in titles
    assert "January" in titles
    assert "Habits" in titles
    assert any(title.startswith("Week ") for title in titles)
    levels = {level for _, level in rows}
    assert {0, 1, 2, 3} <= levels
    dests = {str(key).lstrip("/") for key in (reader.named_destinations or {})}
    assert "year-2026" in dests
    assert "cover" in dests
    off = tmp_path / "off.pdf"
    press(_jan(outline=False), off)
    assert (PdfReader(off).outline or []) == []
    assert len(PdfReader(off).pages) == len(reader.pages)


def test_press_engineering_outline_flat_skips_cover(tmp_path: Path):
    spec = Spec(book="engineering-notebook", engineering_sheets=1, outline=True)
    out = tmp_path / "eng.pdf"
    press(spec, out)
    rows = _pdf_outline_rows(out)
    assert rows == [("Engineering", 0)]
    dests = {str(key).lstrip("/") for key in (PdfReader(out).named_destinations or {})}
    assert "cover" in dests
    assert spec.dest_for_engineering_pad(1, "front") in dests

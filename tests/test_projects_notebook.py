from pathlib import Path

import pytest
from pypdf import PdfReader

from parch.books import ProjectsNotebook, YearPlanner
from parch.components import CoverTitle, ProjectsBoard, ProjectsIndex
from parch.devices import get_device, known_device_ids
from parch.layouts.planner.painters import strip_active, strip_items
from parch.plotter import RecordingPlotter
from parch.plotter.fpdf2 import Fpdf2Plotter
from parch.sections import CoverSection, NavItem, ProjectsSection
from parch.spec import Spec

MM_PER_INCH = 25.4


def _pt(mm: float) -> float:
    return mm / MM_PER_INCH * 72.0


def _named_dests(reader: PdfReader) -> set[str]:
    raw = reader.named_destinations or {}
    return {str(key).lstrip("/") for key in raw}


def _section_pages(spec: Spec):
    return [*CoverSection(spec).pages(), *ProjectsSection(spec).pages()]


def test_notebook_is_cover_then_projects_only():
    spec = Spec(notes_pages=1)
    pages = ProjectsNotebook().pages(spec)
    assert [page.kind for page in pages] == [
        "cover",
        "projects_index",
        *["project"] * spec.project_count,
    ]
    assert [page.dest for page in pages] == [
        spec.cover_dest,
        spec.projects_index_dest,
        *[spec.dest_for_project(slot) for slot in range(1, spec.project_count + 1)],
    ]
    assert not any(
        page.kind
        in {
            "annual",
            "meetings_index",
            "meeting",
            "tasks_index",
            "task",
            "review_index",
            "review",
            "quarter",
            "month",
            "habits",
            "weekly",
            "daily",
            "daily_notes",
        }
        for page in pages
    )


def test_notebook_reuses_section_content():
    spec = Spec(notes_pages=1)
    notebook = ProjectsNotebook().pages(spec)
    sections = _section_pages(spec)
    assert [page.dest for page in notebook] == [page.dest for page in sections]
    assert [page.kind for page in notebook] == [page.kind for page in sections]
    assert [page.title for page in notebook] == [page.title for page in sections]
    assert [page.components for page in notebook[1:]] == [
        page.components for page in sections[1:]
    ]
    cover = notebook[0].components[0]
    assert isinstance(cover, CoverTitle)
    assert cover.cta_dest == spec.projects_index_dest
    assert cover.year == sections[0].components[0].year
    assert cover.subtitle == sections[0].components[0].subtitle


def test_notebook_minimal_proj_nav():
    spec = Spec(notes_pages=1)
    pages = ProjectsNotebook().pages(spec)
    index = pages[1]
    leaf = next(page for page in pages if page.dest == "projects-2026-03")
    assert index.nav == (NavItem("Proj", spec.projects_index_dest),)
    assert leaf.nav == (NavItem("Proj", spec.projects_index_dest),)
    assert strip_items(index) == (("Proj", spec.projects_index_dest),)
    assert strip_items(leaf) == (("Proj", spec.projects_index_dest),)
    assert strip_active(index.kind) == "Proj"
    assert strip_active(leaf.kind) == "Proj"
    assert all(label == "Proj" for page in pages[1:] for label, _ in strip_items(page))


def test_notebook_index_pages_keep_leaf_landing():
    spec = Spec(notes_pages=1, project_index_pages=3)
    pages = ProjectsNotebook().pages(spec)
    dests = [page.dest for page in pages]
    assert dests == [
        "cover",
        "projects-index-2026-01",
        "projects-index-2026-02",
        "projects-index-2026-03",
        *[f"projects-2026-{slot:02d}" for slot in range(1, 25)],
    ]
    leaf = next(page for page in pages if page.dest == "projects-2026-10")
    board = next(item for item in leaf.components if isinstance(item, ProjectsBoard))
    assert board.number == 10
    assert board.index_dest == "projects-index-2026-02"
    assert leaf.nav == (NavItem("Proj", "projects-index-2026-02"),)
    assert strip_items(leaf) == (("Proj", "projects-index-2026-02"),)
    page_two = next(page for page in pages if page.dest == "projects-index-2026-02")
    roster = next(
        item for item in page_two.components if isinstance(item, ProjectsIndex)
    )
    assert [ticket.number for ticket in roster.tickets] == list(range(9, 17))


def test_notebook_year_planner_still_has_full_strip():
    spec = Spec(notes_pages=1)
    year = next(p for p in YearPlanner().pages(spec) if p.kind == "projects_index")
    notebook = next(
        p for p in ProjectsNotebook().pages(spec) if p.kind == "projects_index"
    )
    assert "Year" in dict(strip_items(year))
    assert "Meet" in dict(strip_items(year))
    assert strip_items(notebook) == (("Proj", spec.projects_index_dest),)
    assert year.components == notebook.components


def test_notebook_plot_is_device_agnostic():
    for device in known_device_ids():
        spec = Spec(device=device, notes_pages=1)
        plotter = RecordingPlotter()
        ProjectsNotebook().plot(spec, plotter)
        dests = plotter.dests()
        assert dests[0] == spec.cover_dest
        assert dests[1] == spec.projects_index_dest
        assert spec.year_dest not in dests
        assert spec.meetings_index_dest not in dests
        assert spec.tasks_index_dest not in dests
        links = plotter.links()
        assert spec.projects_index_dest in links
        assert spec.dest_for_project(1) in links
        assert spec.year_dest not in links
        assert spec.meetings_index_dest not in links
        assert "Year" not in [op[2] for op in plotter.ops if op[0] == "text"]
        assert "Proj" in [op[2] for op in plotter.ops if op[0] == "text"]


def test_notebook_pdf_cover_and_projects(tmp_path: Path):
    spec = Spec(notes_pages=1)
    out = tmp_path / "projects-notebook.pdf"
    plotter = Fpdf2Plotter(get_device(spec.device))
    ProjectsNotebook().plot(spec, plotter)
    plotter.finish(out)
    reader = PdfReader(out)
    assert len(reader.pages) == 1 + spec.project_index_pages + spec.project_count
    dests = _named_dests(reader)
    assert spec.cover_dest in dests
    assert spec.projects_index_dest in dests
    assert spec.dest_for_project(1) in dests
    assert spec.dest_for_project(spec.project_count) in dests
    assert spec.year_dest not in dests
    assert spec.meetings_index_dest not in dests
    page = reader.pages[0]
    assert float(page.mediabox.width) == pytest.approx(_pt(118.87), abs=0.6)
    assert float(page.mediabox.height) == pytest.approx(_pt(158.5), abs=0.6)


def test_notebook_scribe_page_geometry(tmp_path: Path):
    spec = Spec(device="kindle-scribe", notes_pages=1)
    out = tmp_path / "scribe-projects.pdf"
    plotter = Fpdf2Plotter(get_device(spec.device))
    ProjectsNotebook().plot(spec, plotter)
    plotter.finish(out)
    page = PdfReader(out).pages[0]
    assert float(page.mediabox.width) == pytest.approx(_pt(157.48), abs=0.6)
    assert float(page.mediabox.height) == pytest.approx(_pt(209.97), abs=0.6)

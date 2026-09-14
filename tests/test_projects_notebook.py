from pathlib import Path

from pypdf import PdfReader

from parch.books import ProjectsNotebook, YearPlanner, book_for
from parch.components import CoverTitle, ProjectsBoard, ProjectsIndex
from parch.press import press
from parch.spec import Spec


def test_projects_notebook_is_cover_then_projects():
    spec = Spec(notes_pages=1, book="projects-notebook")
    pages = ProjectsNotebook().pages(spec)
    assert [page.kind for page in pages[:2]] == ["cover", "projects_index"]
    assert {page.kind for page in pages} == {"cover", "projects_index", "project"}
    assert len(pages) == 1 + spec.project_index_pages + spec.project_count

    cover = pages[0].components[0]
    assert isinstance(cover, CoverTitle)
    assert cover.cta_dest == spec.projects_index_dest
    assert pages[1].dest == spec.projects_index_dest
    assert isinstance(pages[1].components[0], ProjectsIndex)
    assert isinstance(pages[2].components[0], ProjectsBoard)
    assert all(item.label == "Proj" for page in pages[1:] for item in page.nav)
    assert spec.year_dest not in {page.dest for page in pages}


def test_press_selects_projects_notebook_from_toml(tmp_path: Path):
    spec = Spec.from_path(Path("examples/projects-notebook.toml"))
    assert spec.book == "projects-notebook"
    assert book_for(spec.book) is ProjectsNotebook
    assert book_for("year-planner") is YearPlanner

    out = tmp_path / "projects.pdf"
    press(spec, out)
    dests = {str(key).lstrip("/") for key in (PdfReader(out).named_destinations or {})}
    assert "cover" in dests
    assert spec.projects_index_dest in dests
    assert spec.dest_for_project(1) in dests
    assert spec.year_dest not in dests
    assert spec.meetings_index_dest not in dests
    assert (
        len(PdfReader(out).pages) == 1 + spec.project_index_pages + spec.project_count
    )

from pathlib import Path

from pypdf import PdfReader

from parch.books import YearPlanner
from parch.layouts.planner.painters import strip_items
from parch.press import press
from parch.sections import CoverSection, ProjectsNotebookSection, ProjectsSection
from parch.spec import Spec


def test_projects_notebook_is_composite_section():
    spec = Spec.from_path(Path("examples/projects.toml"))
    assert spec.book == "projects"
    composite = ProjectsNotebookSection(spec).pages()
    assert composite == [
        *CoverSection(spec).pages(),
        *ProjectsSection(spec).pages(),
    ]
    pages = YearPlanner().pages(spec)
    assert pages == composite
    kinds = [page.kind for page in pages]
    assert kinds[0] == "cover"
    assert set(kinds) == {"cover", "projects_index", "project"}
    cover = pages[0].components[0]
    assert cover.cta_dest == spec.projects_index_dest
    assert cover.device_name == "SuperNote Nomad"
    index = next(page for page in pages if page.kind == "projects_index")
    assert strip_items(index) == (("Proj", spec.projects_index_dest),)


def test_projects_notebook_device_from_spec():
    spec = Spec(book="projects", device="kindle-scribe")
    cover = CoverSection(spec).pages()[0].components[0]
    assert cover.device_name == "Kindle Scribe (1st gen)"
    assert cover.cta_dest == spec.projects_index_dest


def test_projects_notebook_press_finishes(tmp_path: Path):
    spec = Spec.from_path(Path("examples/projects.toml"))
    out = tmp_path / "projects.pdf"
    press(spec, out)
    reader = PdfReader(out)
    dests = {str(key).lstrip("/") for key in (reader.named_destinations or {})}
    assert len(reader.pages) == 10
    assert dests == {
        "cover",
        "projects-index-2026-01",
        *(f"projects-2026-{slot:02d}" for slot in range(1, 9)),
    }

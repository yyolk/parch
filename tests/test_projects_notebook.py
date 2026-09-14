from pathlib import Path

from pypdf import PdfReader

from parch.books import ProjectsNotebook, YearPlanner
from parch.devices import SCRIBE
from parch.plotter import RecordingPlotter
from parch.press import main, press
from parch.spec import Spec


def _named_dests(reader: PdfReader) -> set[str]:
    raw = reader.named_destinations or {}
    return {str(key).lstrip("/") for key in raw}


def test_projects_notebook_kinds_and_cover_cta():
    spec = Spec(book="projects", months=(1,), notes_pages=0)
    pages = ProjectsNotebook().pages(spec)
    kinds = [page.kind for page in pages]
    assert kinds[0] == "cover"
    assert set(kinds) == {"cover", "projects_index", "project"}
    assert kinds.count("projects_index") == 1
    assert kinds.count("project") == 8
    cover = pages[0]
    assert cover.components[0].cta_dest == spec.projects_index_dest
    assert cover.nav[0].dest == spec.projects_index_dest
    assert cover.components[0].eyebrow == "Projects"
    assert cover.components[0].device_name == "SuperNote Nomad"


def test_projects_notebook_device_agnostic_scribe():
    spec = Spec(book="projects", device="kindle-scribe", months=(1,), notes_pages=0)
    pages = ProjectsNotebook().pages(spec)
    cover = pages[0]
    assert cover.components[0].device_name == SCRIBE.name
    assert cover.components[0].cta_dest == spec.projects_index_dest
    kinds = [page.kind for page in pages]
    assert kinds[0] == "cover"
    assert set(kinds) == {"cover", "projects_index", "project"}


def test_year_planner_cover_cta_unchanged():
    spec = Spec(notes_pages=1)
    cover = YearPlanner().pages(spec)[0]
    assert cover.components[0].cta_dest == "year-2026"
    assert cover.components[0].eyebrow == "Year Book"
    assert cover.components[0].device_name == "SuperNote Nomad"
    scribe = YearPlanner().pages(Spec(device="kindle-scribe", notes_pages=1))[0]
    assert scribe.components[0].device_name == SCRIBE.name
    assert scribe.components[0].cta_dest == "year-2026"


def test_projects_notebook_plot_dests():
    spec = Spec(book="projects", months=(1,), notes_pages=0)
    plotter = RecordingPlotter()
    ProjectsNotebook().plot(spec, plotter)
    dests = plotter.dests()
    assert dests[0] == "cover"
    assert dests[1] == spec.projects_index_dest
    assert spec.dest_for_project(1) in dests
    assert spec.year_dest not in dests
    assert spec.projects_index_dest in plotter.links()
    texts = [op[2] for op in plotter.ops if op[0] == "text"]
    assert "Projects" in texts
    assert "Year Book" not in texts


def test_example_projects_toml_and_press(tmp_path: Path):
    spec = Spec.from_path(Path("examples/projects.toml"))
    assert spec.book == "projects"
    assert spec.device == "supernote-nomad"
    kinds = [page.kind for page in ProjectsNotebook().pages(spec)]
    assert kinds[0] == "cover"
    assert set(kinds) == {"cover", "projects_index", "project"}

    out = tmp_path / "projects.pdf"
    press(spec, out)
    dests = _named_dests(PdfReader(out))
    assert "cover" in dests
    assert spec.projects_index_dest in dests
    assert spec.dest_for_project(1) in dests
    assert spec.year_dest not in dests


def test_cli_press_projects_toml(tmp_path: Path):
    out = tmp_path / "cli-projects.pdf"
    assert main(["press", "examples/projects.toml", "-o", str(out)]) == 0
    dests = _named_dests(PdfReader(out))
    assert "projects-index-2026-01" in dests
    assert "year-2026" not in dests

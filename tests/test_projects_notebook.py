from pathlib import Path

import pytest
from pypdf import PdfReader

from parch import ConfigError
from parch.books import YearPlanner, pages_factory, projects_notebook_pages
from parch.components import CoverTitle, ProjectsBoard, ProjectsIndex
from parch.devices import SCRIBE
from parch.layouts.planner.painters import strip_items
from parch.plotter import RecordingPlotter
from parch.press import main, press
from parch.spec import Spec


def _named_dests(reader: PdfReader) -> set[str]:
    raw = reader.named_destinations or {}
    return {str(key).lstrip("/") for key in raw}


def test_projects_notebook_pages_are_cover_then_projects():
    spec = Spec.from_path(Path("examples/projects.toml"))
    assert spec.title == "Projects"
    assert spec.device == "supernote-nomad"
    assert not hasattr(spec, "book")

    pages = projects_notebook_pages(spec)
    kinds = [page.kind for page in pages]
    assert kinds[0] == "cover"
    assert set(kinds) == {"cover", "projects_index", "project"}
    assert kinds.count("projects_index") == spec.project_index_pages
    assert kinds.count("project") == spec.project_count
    assert len(pages) == 1 + spec.project_index_pages + spec.project_count

    cover = pages[0].components[0]
    assert isinstance(cover, CoverTitle)
    assert cover.cta_dest == spec.projects_index_dest
    assert cover.device_name == "SuperNote Nomad"
    assert pages[0].nav[0].dest == spec.projects_index_dest
    assert pages[1].dest == spec.projects_index_dest
    assert isinstance(pages[1].components[0], ProjectsIndex)
    assert isinstance(pages[2].components[0], ProjectsBoard)
    assert strip_items(pages[1]) == (("Proj", spec.projects_index_dest),)
    leaf = next(page for page in pages if page.kind == "project")
    assert strip_items(leaf) == (
        ("Proj", spec.dest_for_projects_index_of(leaf.components[0].number)),
    )
    assert spec.year_dest not in {page.dest for page in pages}


def test_year_planner_cover_cta_unchanged():
    spec = Spec(notes_pages=1)
    cover = YearPlanner().pages(spec)[0]
    assert cover.components[0].cta_dest == "year-2026"
    assert cover.components[0].device_name == "SuperNote Nomad"
    scribe = YearPlanner().pages(Spec(device="kindle-scribe", notes_pages=1))[0]
    assert scribe.components[0].device_name == SCRIBE.name
    assert scribe.components[0].cta_dest == "year-2026"


def test_projects_notebook_device_agnostic_scribe():
    spec = Spec(device="kindle-scribe", months=(1,), notes_pages=1)
    pages = projects_notebook_pages(spec)
    cover = pages[0]
    assert cover.components[0].device_name == SCRIBE.name
    assert cover.components[0].cta_dest == spec.projects_index_dest
    assert {page.kind for page in pages} == {"cover", "projects_index", "project"}


def test_pages_factory_lookup_and_plot_dests():
    spec = Spec.from_path(Path("examples/projects.toml"))
    assert pages_factory("projects") is projects_notebook_pages
    with pytest.raises(ConfigError, match="unknown pages factory"):
        pages_factory("year")

    plotter = RecordingPlotter()
    YearPlanner().plot(spec, plotter, pages=projects_notebook_pages(spec))
    dests = plotter.dests()
    assert dests[0] == "cover"
    assert dests[1] == spec.projects_index_dest
    assert dests[2:] == [
        spec.dest_for_project(slot) for slot in range(1, spec.project_count + 1)
    ]
    assert spec.year_dest not in dests
    assert spec.projects_index_dest in plotter.links()


def test_press_pages_factory_from_toml(tmp_path: Path):
    spec = Spec.from_path(Path("examples/projects.toml"))
    out = tmp_path / "projects.pdf"
    press(spec, out, pages="projects")
    dests = _named_dests(PdfReader(out))
    assert "cover" in dests
    assert spec.projects_index_dest in dests
    assert spec.dest_for_project(1) in dests
    assert spec.year_dest not in dests
    assert spec.meetings_index_dest not in dests
    assert (
        len(PdfReader(out).pages) == 1 + spec.project_index_pages + spec.project_count
    )


def test_cli_press_projects_pages_factory(tmp_path: Path):
    out = tmp_path / "cli-projects.pdf"
    assert (
        main(["press", "examples/projects.toml", "--pages", "projects", "-o", str(out)])
        == 0
    )
    dests = _named_dests(PdfReader(out))
    assert "projects-index-2026-01" in dests
    assert "year-2026" not in dests

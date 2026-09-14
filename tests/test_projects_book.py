from pathlib import Path

import pytest

from parch import ConfigError
from parch.books import YearPlanner
from parch.layouts.planner.painters import strip_items
from parch.plotter import RecordingPlotter
from parch.spec import Spec


def test_projects_book_from_example_toml():
    spec = Spec.from_path(Path("examples/projects.toml"))
    assert spec.book == "projects"
    assert spec.sections == ("cover", "projects")
    assert spec.device == "supernote-nomad"
    assert spec.title == "Projects"
    assert spec.projects_hub
    assert spec.cover_cta_dest == spec.projects_index_dest

    pages = YearPlanner().pages(spec)
    kinds = [page.kind for page in pages]
    assert kinds[0] == "cover"
    assert set(kinds) == {"cover", "projects_index", "project"}
    cover = pages[0].components[0]
    assert cover.cta_dest == spec.projects_index_dest
    assert cover.device_name == "SuperNote Nomad"
    assert pages[1].kind == "projects_index"
    assert pages[1].dest == spec.projects_index_dest
    assert strip_items(pages[1]) == (("Proj", spec.projects_index_dest),)
    leaf = next(page for page in pages if page.kind == "project")
    assert strip_items(leaf) == (
        ("Proj", spec.dest_for_projects_index_of(leaf.components[0].number)),
    )


def test_sections_list_is_the_same_hook():
    spec = Spec(sections=("cover", "projects"))
    assert spec.book == "year"
    assert spec.projects_hub
    assert spec.cover_cta_dest == spec.projects_index_dest
    pages = YearPlanner().pages(spec)
    assert {page.kind for page in pages} == {"cover", "projects_index", "project"}


def test_projects_book_plot_has_no_year_pages():
    spec = Spec.from_path(Path("examples/projects.toml"))
    plotter = RecordingPlotter()
    YearPlanner().plot(spec, plotter)
    dests = plotter.dests()
    assert dests[0] == "cover"
    assert dests[1] == spec.projects_index_dest
    assert dests[2:] == [
        spec.dest_for_project(slot) for slot in range(1, spec.project_count + 1)
    ]
    assert spec.year_dest not in dests
    assert spec.projects_index_dest in plotter.links()


def test_unknown_book_and_section_fail():
    with pytest.raises(ConfigError, match="book must be"):
        Spec(book="meetings")
    with pytest.raises(ConfigError, match="unknown section"):
        Spec.from_mapping({"sections": ["cover", "atlas"]})
    with pytest.raises(ConfigError, match="sections must be a non-empty list"):
        Spec.from_mapping({"sections": []})

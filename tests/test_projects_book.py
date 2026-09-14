from pathlib import Path

import pytest
from pypdf import PdfReader

from parch import ConfigError
from parch.books import YearPlanner
from parch.layouts.planner.painters import strip_items
from parch.plotter import RecordingPlotter
from parch.press import press
from parch.spec import Spec


def test_default_spec_is_year_book():
    spec = Spec()
    assert spec.book == "year"
    assert spec.sections is None
    assert spec.presses_section("annual")
    assert spec.cover_cta_dest == "year-2026"
    pages = YearPlanner().pages(Spec(notes_pages=1, months=(1,)))
    assert pages[0].kind == "cover"
    assert pages[1].dest == "year-2026"
    assert pages[2].kind == "projects_index"


def test_projects_book_kind_emits_cover_and_projects_only():
    spec = Spec(book="projects")
    assert spec.pressed_sections() == ("cover", "projects")
    assert spec.cover_cta_dest == "projects-index-2026-01"
    pages = YearPlanner().pages(spec)
    dests = [page.dest for page in pages]
    assert dests == [
        "cover",
        "projects-index-2026-01",
        *[f"projects-2026-{slot:02d}" for slot in range(1, 9)],
    ]
    assert {page.kind for page in pages} == {"cover", "projects_index", "project"}
    assert pages[0].components[0].cta_dest == spec.projects_index_dest
    assert strip_items(pages[1]) == (("Proj", "projects-index-2026-01"),)
    assert strip_items(pages[2]) == (("Proj", "projects-index-2026-01"),)


def test_projects_book_via_sections_list():
    spec = Spec(sections=("cover", "projects"))
    assert spec.book == "year"
    assert spec.pressed_sections() == ("cover", "projects")
    assert spec.cover_cta_dest == "projects-index-2026-01"
    dests = [page.dest for page in YearPlanner().pages(spec)]
    assert dests[0] == "cover"
    assert dests[1] == "projects-index-2026-01"
    assert "year-2026" not in dests
    assert "meetings-index-2026" not in dests


def test_projects_toml_and_mapping():
    from_book = Spec.from_mapping({"book": "projects", "title": "Projects"})
    assert from_book.book == "projects"
    assert from_book.title == "Projects"
    from_list = Spec.from_mapping({"sections": ["cover", "projects"]})
    assert from_list.pressed_sections() == ("cover", "projects")
    path = Spec.from_path(Path("examples/projects.toml"))
    assert path.book == "projects"
    assert path.device == "supernote-nomad"
    assert path.project_index_pages == 1
    assert path.cover_cta_dest == path.projects_index_dest


def test_book_and_sections_validation():
    with pytest.raises(ConfigError, match="book must be year or projects"):
        Spec(book="meetings")
    with pytest.raises(ConfigError, match="unknown section"):
        Spec(sections=("cover", "nope"))
    with pytest.raises(ConfigError, match="sections must not be empty"):
        Spec(sections=())
    with pytest.raises(ConfigError, match="duplicate section"):
        Spec(sections=("cover", "cover"))
    with pytest.raises(ConfigError, match="book and sections disagree"):
        Spec(book="projects", sections=("cover", "annual"))
    with pytest.raises(ConfigError, match="sections must be a TOML array"):
        Spec.from_mapping({"sections": "cover"})


def test_projects_book_plot_links_index_hub():
    spec = Spec(book="projects")
    plotter = RecordingPlotter()
    YearPlanner().plot(spec, plotter)
    dests = plotter.dests()
    links = plotter.links()
    assert dests[0] == "cover"
    assert dests[1] == "projects-index-2026-01"
    assert "year-2026" not in dests
    assert "year-2026" not in links
    assert "projects-index-2026-01" in links
    assert "projects-2026-01" in dests
    assert "projects-2026-08" in dests
    assert "projects-2026-01" in links


def test_projects_toml_presses(tmp_path: Path):
    out = tmp_path / "projects.pdf"
    spec = Spec.from_path(Path("examples/projects.toml"))
    press(spec, out)
    reader = PdfReader(out)
    assert len(reader.pages) == 10
    raw = reader.named_destinations or {}
    dests = {str(key).lstrip("/") for key in raw}
    assert "cover" in dests
    assert "projects-index-2026-01" in dests
    assert "projects-2026-08" in dests
    assert "year-2026" not in dests

from pathlib import Path

import pytest
from pypdf import PdfReader

from parch import ConfigError
from parch.books import YearPlanner
from parch.components import CoverTitle, ProjectsBoard, ProjectsIndex
from parch.press import press
from parch.sections import CoverSection, ProjectsSection
from parch.spec import BOOK_SECTIONS, SECTION_NAMES, Spec


def test_year_book_is_the_default_walk():
    spec = Spec()
    assert spec.book == "year"
    assert spec.sections is None
    assert spec.section_names == SECTION_NAMES
    assert spec.includes("annual")
    assert spec.includes("projects")
    assert spec.entry_dest == spec.year_dest == "year-2026"


def test_projects_book_kind_filters_year_planner():
    spec = Spec(book="projects", notes_pages=1, project_index_pages=3)
    assert spec.section_names == ("cover", "projects")
    assert spec.includes("cover")
    assert spec.includes("projects")
    assert not spec.includes("annual")
    assert spec.entry_dest == spec.projects_index_dest

    pages = YearPlanner().pages(spec)
    kinds = [page.kind for page in pages]
    dests = [page.dest for page in pages]
    assert dests[0] == "cover"
    assert dests[1:4] == [
        "projects-index-2026-01",
        "projects-index-2026-02",
        "projects-index-2026-03",
    ]
    assert dests[4:] == [f"projects-2026-{slot:02d}" for slot in range(1, 25)]
    assert (
        kinds
        == ["cover", "projects_index", "projects_index", "projects_index"]
        + ["project"] * 24
    )
    assert "year-2026" not in dests
    assert "meetings-index-2026" not in dests
    assert not any(kind in {"annual", "meeting", "month", "daily"} for kind in kinds)
    assert len(pages) == 1 + 3 + 24


def test_projects_book_reuses_cover_and_projects_sections():
    spec = Spec(book="projects", title="Projects", notes_pages=1)
    cover = CoverSection(spec).pages()
    projects = ProjectsSection(spec).pages()
    built = YearPlanner().pages(spec)
    assert [page.dest for page in built] == [page.dest for page in (*cover, *projects)]
    assert built[0].components == cover[0].components
    assert isinstance(built[0].components[0], CoverTitle)
    assert built[0].components[0].cta_dest == spec.projects_index_dest
    assert built[0].components[0].subtitle == "Projects"
    roster = next(
        item for item in built[1].components if isinstance(item, ProjectsIndex)
    )
    board = next(
        item for item in built[2].components if isinstance(item, ProjectsBoard)
    )
    assert roster.year == 2026
    assert board.number == 1


def test_sections_allowlist_overrides_book_preset():
    spec = Spec(book="year", sections=("cover", "projects"), notes_pages=1)
    assert spec.book == "year"
    assert spec.section_names == ("cover", "projects")
    dests = [page.dest for page in YearPlanner().pages(spec)]
    assert dests[0] == "cover"
    assert dests[1] == "projects-index-2026-01"
    assert "year-2026" not in dests
    assert len(dests) == 1 + 1 + 8


def test_nomad_projects_toml():
    spec = Spec.from_path(Path("examples/nomad-projects.toml"))
    assert spec.book == "projects"
    assert spec.title == "Projects"
    assert spec.months == (1,)
    assert spec.project_index_pages == 3
    assert spec.section_names == BOOK_SECTIONS["projects"]
    pages = YearPlanner().pages(spec)
    assert [page.kind for page in pages].count("projects_index") == 3
    assert [page.kind for page in pages].count("project") == 24
    assert pages[0].kind == "cover"


def test_book_and_sections_fail_loudly():
    with pytest.raises(ConfigError, match="book must be projects, year"):
        Spec(book="meetings")
    with pytest.raises(ConfigError, match="unknown section 'colophon'"):
        Spec(sections=("cover", "colophon"))
    with pytest.raises(ConfigError, match="sections must not be empty"):
        Spec(sections=())
    with pytest.raises(ConfigError, match="duplicate section projects"):
        Spec.from_mapping({"sections": ["cover", "projects", "projects"]})
    with pytest.raises(ConfigError, match="sections must be a TOML array"):
        Spec.from_mapping({"sections": "projects"})
    with pytest.raises(ConfigError, match="book must be a string"):
        Spec.from_mapping({"book": 1})


def test_press_projects_notebook(tmp_path: Path):
    out = tmp_path / "projects.pdf"
    spec = Spec.from_path(Path("examples/nomad-projects.toml"))
    press(spec, out)
    reader = PdfReader(out)
    assert len(reader.pages) == 28
    dests = {str(key).lstrip("/") for key in (reader.named_destinations or {})}
    assert "cover" in dests
    assert "projects-index-2026-01" in dests
    assert "projects-2026-24" in dests
    assert "year-2026" not in dests
    assert "2026-01-01" not in dests

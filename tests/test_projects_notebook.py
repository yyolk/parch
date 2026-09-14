from pathlib import Path

from pypdf import PdfReader

from parch.books import ProjectsNotebook, YearPlanner, remap_chrome
from parch.components import CoverTitle
from parch.devices.registry import NOMAD, SCRIBE
from parch.layouts.planner.painters import strip_items
from parch.press import press
from parch.sections import CoverSection, ProjectsSection
from parch.spec import Spec


def _named_dests(reader: PdfReader) -> set[str]:
    raw = reader.named_destinations or {}
    return {str(key).lstrip("/") for key in raw}


def test_raw_cover_projects_have_dead_year_chrome():
    spec = Spec(notes_pages=1)
    raw = [*CoverSection(spec).pages(), *ProjectsSection(spec).pages()]
    cover = next(item for item in raw[0].components if isinstance(item, CoverTitle))
    assert cover.cta_dest == spec.year_dest
    assert spec.year_dest not in {page.dest for page in raw}
    assert any(item.dest == spec.year_dest for page in raw for item in page.nav)


def test_remap_chrome_retargets_cover_and_collapses_strip():
    spec = Spec(notes_pages=1, device="kindle-scribe")
    raw = [*CoverSection(spec).pages(), *ProjectsSection(spec).pages()]
    pages = remap_chrome(raw, device_name=SCRIBE.name)
    live = {page.dest for page in pages}
    hub = spec.projects_index_dest

    cover = next(item for item in pages[0].components if isinstance(item, CoverTitle))
    assert cover.cta_dest == hub
    assert cover.device_name == SCRIBE.name
    assert all(item.dest in live for page in pages for item in page.nav)

    kinds = {page.kind for page in pages}
    assert kinds == {"cover", "projects_index", "project"}
    index = next(page for page in pages if page.kind == "projects_index")
    leaf = next(page for page in pages if page.dest == "projects-2026-03")
    assert strip_items(index) == (("Proj", hub),)
    assert strip_items(leaf) == (("Proj", spec.dest_for_projects_index_of(3)),)


def test_projects_notebook_pages_are_cover_plus_projects():
    spec = Spec(notes_pages=1)
    pages = ProjectsNotebook().pages(spec)
    assert [page.kind for page in pages] == [
        "cover",
        "projects_index",
        *["project"] * 8,
    ]
    cover = next(item for item in pages[0].components if isinstance(item, CoverTitle))
    assert cover.cta_dest == spec.projects_index_dest
    assert cover.device_name == NOMAD.name
    yearly = YearPlanner().pages(spec)
    assert "annual" in {page.kind for page in yearly}
    yearly_cover = next(
        item for item in yearly[0].components if isinstance(item, CoverTitle)
    )
    assert yearly_cover.cta_dest == spec.year_dest


def test_remap_keeps_leaf_index_hub_on_later_pages():
    spec = Spec(notes_pages=1, project_index_pages=3)
    leaf = next(
        page
        for page in ProjectsNotebook().pages(spec)
        if page.dest == "projects-2026-10"
    )
    assert strip_items(leaf) == (("Proj", "projects-index-2026-02"),)


def test_press_projects_example(tmp_path: Path):
    spec = Spec.from_path(Path("examples/projects.toml"))
    out = tmp_path / "projects.pdf"
    press(spec, out)
    reader = PdfReader(out)
    dests = _named_dests(reader)
    assert spec.book == "projects"
    assert len(reader.pages) == 10
    assert dests == {
        "cover",
        "projects-index-2026-01",
        *(f"projects-2026-{slot:02d}" for slot in range(1, 9)),
    }
    assert "year-2026" not in dests

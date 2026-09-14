from pathlib import Path

from pypdf import PdfReader

from parch.components import CoverTitle
from parch.devices.registry import SCRIBE
from parch.layouts.planner.painters import strip_items
from parch.press import main, press
from parch.sections import CoverSection, ProjectsSection
from parch.sections.remap import projects_notebook_pages, remap_year_chrome
from parch.spec import Spec


def _named_dests(reader: PdfReader) -> set[str]:
    raw = reader.named_destinations or {}
    return {str(key).lstrip("/") for key in raw}


def test_remap_rewrites_year_chrome_onto_projects_index():
    spec = Spec(months=(1,), notes_pages=1, title="Projects")
    raw = [*CoverSection(spec).pages(), *ProjectsSection(spec).pages()]
    cover = next(page for page in raw if page.kind == "cover")
    cta = next(item for item in cover.components if isinstance(item, CoverTitle))
    assert cta.cta_dest == spec.year_dest
    assert any(item.dest == spec.year_dest for item in cover.nav)
    assert any(
        item.dest == spec.year_dest
        for page in raw
        if page.kind == "projects_index"
        for item in page.nav
    )

    pages = remap_year_chrome(raw, spec)
    dests = {page.dest for page in pages}
    assert dests == {page.dest for page in raw}
    assert spec.year_dest not in dests
    assert all(item.dest in dests for page in pages for item in page.nav)

    remapped = next(page for page in pages if page.kind == "cover")
    remapped_cta = next(
        item for item in remapped.components if isinstance(item, CoverTitle)
    )
    assert remapped_cta.cta_dest == spec.projects_index_dest
    assert remapped.nav[0].label == str(spec.year)
    assert remapped.nav[0].dest == spec.projects_index_dest
    assert remapped_cta.device_name == "SuperNote Nomad"

    index = next(page for page in pages if page.kind == "projects_index")
    assert strip_items(index) == (("Proj", spec.projects_index_dest),)
    leaf = next(page for page in pages if page.kind == "project")
    assert strip_items(leaf) == (("Proj", spec.dest_for_projects_index_of(1)),)


def test_projects_notebook_pages_calls_existing_sections():
    spec = Spec.from_path(Path("examples/projects.toml"))
    pages = projects_notebook_pages(spec)
    assert [page.kind for page in pages] == [
        "cover",
        "projects_index",
        *["project"] * 8,
    ]
    assert CoverSection(spec).pages()[0].dest == pages[0].dest
    assert ProjectsSection(spec).pages()[0].dest == pages[1].dest


def test_projects_notebook_press_finishes(tmp_path: Path):
    out = tmp_path / "projects.pdf"
    spec = Spec.from_path(Path("examples/projects.toml"))
    press(spec, out, projects_notebook=True)
    reader = PdfReader(out)
    assert len(reader.pages) == 10
    dests = _named_dests(reader)
    assert dests == {
        "cover",
        "projects-index-2026-01",
        *(f"projects-2026-{slot:02d}" for slot in range(1, 9)),
    }
    assert "year-2026" not in dests


def test_cli_projects_notebook_flag(tmp_path: Path):
    out = tmp_path / "cli.pdf"
    assert (
        main(
            [
                "press",
                "--projects-notebook",
                "examples/projects.toml",
                "-o",
                str(out),
            ]
        )
        == 0
    )
    assert out.is_file()
    assert "year-2026" not in _named_dests(PdfReader(out))


def test_remap_device_name_from_spec():
    spec = Spec(device="kindle-scribe", months=(1,), title="Projects")
    cover = next(
        item
        for page in projects_notebook_pages(spec)
        if page.kind == "cover"
        for item in page.components
        if isinstance(item, CoverTitle)
    )
    assert cover.device_name == SCRIBE.name
    assert cover.cta_dest == spec.projects_index_dest

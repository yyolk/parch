from pathlib import Path

from pypdf import PdfReader

from parch.books import projects_notebook_pages
from parch.press import main
from parch.spec import Spec


def test_projects_notebook_pages_factory():
    spec = Spec.from_path(Path("examples/projects.toml"))
    pages = projects_notebook_pages(spec)
    kinds = [page.kind for page in pages]
    assert kinds[0] == "cover"
    assert set(kinds) == {"cover", "projects_index", "project"}
    assert kinds.count("projects_index") == spec.project_index_pages
    assert kinds.count("project") == spec.project_count
    assert pages[0].components[0].cta_dest == spec.projects_index_dest
    for page in pages[1:]:
        assert [item.label for item in page.nav] == ["Proj"]


def test_cli_book_projects(tmp_path: Path):
    out = tmp_path / "projects.pdf"
    assert (
        main(["press", "examples/projects.toml", "--book", "projects", "-o", str(out)])
        == 0
    )
    reader = PdfReader(out)
    assert len(reader.pages) == 10
    dests = {str(key).lstrip("/") for key in (reader.named_destinations or {})}
    assert "cover" in dests
    assert "projects-index-2026-01" in dests
    assert "projects-2026-08" in dests
    assert "year-2026" not in dests

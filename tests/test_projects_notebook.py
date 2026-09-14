from pathlib import Path

from parch.books import ProjectsNotebook
from parch.spec import Spec


def test_projects_notebook_page_kinds_only():
    spec = Spec.from_path(Path("examples/projects.toml"))
    pages = ProjectsNotebook().pages(spec)
    kinds = [page.kind for page in pages]
    assert kinds[0] == "cover"
    assert set(kinds) == {"cover", "projects_index", "project"}
    assert kinds.count("projects_index") == spec.project_index_pages
    assert kinds.count("project") == spec.project_count
    assert pages[0].components[0].cta_dest == spec.projects_index_dest

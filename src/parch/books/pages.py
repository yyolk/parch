"""Pages factories — compose existing sections. Not a Book, not a Spec.book filter."""

from collections.abc import Callable
from dataclasses import replace

from parch import ConfigError
from parch.sections import CoverSection, Page, ProjectsSection
from parch.sections.page import NavItem
from parch.spec import Spec

type PagesFactory = Callable[[Spec], list[Page]]


def projects_notebook_pages(spec: Spec) -> list[Page]:
    """Cover + Projects (index + dests). Factory composition only."""
    landing = spec.projects_index_dest
    built = [*CoverSection(spec, landing_dest=landing).pages()]
    for page in ProjectsSection(spec).pages():
        built.append(replace(page, nav=_proj_nav(page)))
    return built


def _proj_nav(page: Page) -> tuple[NavItem, ...]:
    """Keep the Proj chip — dests still come from ProjectsSection."""
    kept = tuple(item for item in page.nav if item.label == "Proj")
    return kept if kept else (NavItem("Proj", page.dest),)


_FACTORIES: dict[str, PagesFactory] = {
    "projects": projects_notebook_pages,
}


def pages_factory(name: str) -> PagesFactory:
    """Look up a pages factory by CLI / press token. Default book stays YearPlanner."""
    try:
        return _FACTORIES[name]
    except KeyError:
        known = ", ".join(sorted(_FACTORIES))
        raise ConfigError(f"unknown pages factory {name!r}; known: {known}") from None

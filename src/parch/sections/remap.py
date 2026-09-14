"""Rewrite year-shaped chrome so Cover + Projects can finish as a notebook.

``CoverSection`` and ``ProjectsSection`` stay as-is. This adapter filters
``Page.nav`` to dests that exist in the page list (projects-index and
project leaves) and rewrites the cover CTA (and cover year-nav dest) onto
the projects index. Orphan year/quarter/month/… dests are dropped rather
than aliased onto the hub.
"""

from dataclasses import replace

from parch.components import Component, CoverTitle
from parch.devices import get_device
from parch.sections.cover import CoverSection
from parch.sections.page import NavItem, Page
from parch.sections.projects import ProjectsSection
from parch.spec import Spec


def projects_notebook_pages(spec: Spec) -> list[Page]:
    """Cover + Projects, then remap year-shaped chrome."""
    return remap_year_chrome(
        [*CoverSection(spec).pages(), *ProjectsSection(spec).pages()],
        spec,
    )


def remap_year_chrome(pages: list[Page], spec: Spec) -> list[Page]:
    """Filter / rewrite nav and cover CTA dests onto in-book project dests."""
    dests = {page.dest for page in pages}
    hub = spec.projects_index_dest
    device_name = get_device(spec.device).name
    return [
        replace(
            page,
            nav=_remap_nav(page, dests=dests, hub=hub),
            components=tuple(
                _remap_component(item, dests=dests, hub=hub, device_name=device_name)
                for item in page.components
            ),
        )
        for page in pages
    ]


def _remap_nav(page: Page, *, dests: set[str], hub: str) -> tuple[NavItem, ...]:
    if page.kind == "cover":
        return tuple(
            NavItem(item.label, item.dest if item.dest in dests else hub)
            for item in page.nav
        )
    return tuple(item for item in page.nav if item.dest in dests)


def _remap_component(
    item: Component, *, dests: set[str], hub: str, device_name: str
) -> Component:
    if isinstance(item, CoverTitle):
        cta = item.cta_dest if item.cta_dest in dests else hub
        return replace(item, cta_dest=cta, device_name=device_name)
    return item

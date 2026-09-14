"""Remap planner chrome onto dests that exist in a slim book.

CoverSection / ProjectsSection still emit year-planner nav and a cover CTA
to ``spec.year_dest``. A projects notebook does not reserve those dests.
This rewrite keeps the section objects; it only retargets chrome.

Cover CTA is rewritten onto the projects-index hub. Nav items whose dest
is missing are dropped — rewriting them onto a ``projects-index-`` dest
would collide in ``strip_items`` (Meet/Task follow Proj and would steal a
leaf’s own index). The painted strip is then **Proj** only.
"""

from dataclasses import replace

from parch.components import CoverTitle
from parch.sections.page import NavItem, Page


def live_dests(pages: list[Page]) -> frozenset[str]:
    return frozenset(page.dest for page in pages)


def remap_dest(dest: str, live: frozenset[str], fallback: str) -> str:
    return dest if dest in live else fallback


def remap_nav(nav: tuple[NavItem, ...], live: frozenset[str]) -> tuple[NavItem, ...]:
    """Keep dests that exist. Drop the rest.

    Rewriting dead ``year-`` / ``quarter-`` / … items onto a
    ``projects-index-`` hub would collide in ``strip_items``: Meet and
    Task come after Proj and would overwrite a leaf’s own index dest.
    """
    return tuple(item for item in nav if item.dest in live)


def remap_cover(
    cover: CoverTitle,
    live: frozenset[str],
    fallback: str,
    *,
    device_name: str | None = None,
) -> CoverTitle:
    return replace(
        cover,
        cta_dest=remap_dest(cover.cta_dest, live, fallback),
        device_name=device_name if device_name is not None else cover.device_name,
    )


def remap_page(
    page: Page,
    live: frozenset[str],
    fallback: str,
    *,
    device_name: str | None = None,
) -> Page:
    components = tuple(
        remap_cover(item, live, fallback, device_name=device_name)
        if isinstance(item, CoverTitle)
        else item
        for item in page.components
    )
    return Page(
        dest=page.dest,
        kind=page.kind,
        title=page.title,
        nav=remap_nav(page.nav, live),
        components=components,
    )


def remap_chrome(
    pages: list[Page],
    fallback: str | None = None,
    *,
    device_name: str | None = None,
) -> list[Page]:
    """Retarget cover CTA + ``Page.nav`` onto dests in ``pages``.

    Default fallback is the first ``projects_index`` dest (Proj landing).
    """
    live = live_dests(pages)
    hub = fallback
    if hub is None:
        hub = next(
            (page.dest for page in pages if page.kind == "projects_index"),
            None,
        )
    if hub is None:
        raise ValueError(
            "remap_chrome needs a projects_index page or an explicit fallback"
        )
    if hub not in live:
        raise ValueError(f"fallback dest {hub!r} is not in the book")
    return [remap_page(page, live, hub, device_name=device_name) for page in pages]

"""Optional PDF reader outline — section hubs, never a printed TOC page."""

from collections.abc import Iterable
from dataclasses import dataclass

from parch import ConfigError
from parch.sections.page import Page, PageKind
from parch.spec import Spec

_HUB_TITLES: dict[PageKind, str] = {
    "annual": "Annual",
    "projects_index": "Projects",
    "meetings_index": "Meetings",
    "tasks_index": "Tasks",
    "review_index": "Review",
    "quarter": "Quarters",
    "month": "Months",
    "weekly": "Weeks",
    "daily": "Days",
    "engineering_front": "Engineering",
    "steno": "Steno",
}


@dataclass(frozen=True, slots=True)
class OutlineEntry:
    """One reader bookmark: ``title`` jumps to named ``dest`` (optional nest ``level``)."""

    title: str
    dest: str
    level: int = 0


def outline_from_pages(ledger: Iterable[Page]) -> list[OutlineEntry]:
    """First dest of each hub kind; cover and leaf pages are omitted."""
    seen: set[PageKind] = set()
    entries: list[OutlineEntry] = []
    for page in ledger:
        if page.kind in seen or page.kind not in _HUB_TITLES:
            continue
        seen.add(page.kind)
        entries.append(OutlineEntry(_HUB_TITLES[page.kind], page.dest))
    return entries


def outline_for(book: object, spec: Spec) -> tuple[OutlineEntry, ...]:
    """Duck-typed ``book.outline_entries(spec)``, else hubs from ``book.pages``."""
    if not spec.outline:
        return ()
    method = getattr(book, "outline_entries", None)
    if callable(method):
        return tuple(method(spec))
    pages = getattr(book, "pages", None)
    if callable(pages):
        return tuple(outline_from_pages(pages(spec)))
    return ()


def require_outline_dests(
    entries: Iterable[OutlineEntry], ledger: Iterable[Page]
) -> tuple[OutlineEntry, ...]:
    """Fail if an outline dest is missing from the painted ledger."""
    known = {page.dest for page in ledger}
    resolved = tuple(entries)
    for entry in resolved:
        if entry.dest not in known:
            raise ConfigError(f"outline dest {entry.dest!r} is not in the page ledger")
    return resolved

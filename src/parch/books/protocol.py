"""Book protocol at press/dispatch; ``plot_pages`` walks a page ledger."""

from collections.abc import Callable, Iterable
from typing import Protocol

from parch.devices import get_device
from parch.fonts.ramp import TypeRamp
from parch.layouts.planner import PlannerLayout
from parch.plotter.protocol import Plotter
from parch.progress import render_progress
from parch.sections.page import Page, PageKind
from parch.spec import Spec

_KIND_LABELS: dict[PageKind, str] = {
    "annual": "Year",
    "projects_index": "Projects",
    "project": "Project",
    "meetings_index": "Meetings",
    "meeting": "Meeting",
    "tasks_index": "Tasks",
    "task": "Task",
    "review_index": "Review",
    "review": "Review week",
    "quarter": "Quarter",
    "month": "Month",
    "habits": "Habits",
    "weekly": "Weekly",
    "daily": "Daily",
    "daily_notes": "Notes",
    "engineering_front": "Engineering",
    "engineering_back": "Computation",
    "steno": "Steno",
}
_TITLE_KINDS: frozenset[PageKind] = frozenset({"month", "quarter", "weekly", "habits"})


def section_outline_entries(ledger: Iterable[Page]) -> list[tuple[str, str]]:
    """``(human_title, dest)`` at each PageKind run; cover is omitted."""
    entries: list[tuple[str, str]] = []
    prev: PageKind | None = None
    for page in ledger:
        if page.kind == "cover":
            continue
        if page.kind == prev:
            continue
        title = page.title if page.kind in _TITLE_KINDS else _KIND_LABELS[page.kind]
        entries.append((title, page.dest))
        prev = page.kind
    return entries


class Book(Protocol):
    """Press/dispatch surface: ``pages`` + ``plot``.

    Structural only — press does not ``isinstance``-check it.
    ``plot_pages`` is not typed as ``Book`` — it takes a zero-arg pages
    factory (or any duck that is ``Callable[[], Iterable[Page]]``).
    """

    def pages(self, spec: Spec) -> list[Page]:
        """Build the book's pages in press order."""

    def plot(self, spec: Spec, plotter: Plotter) -> None:
        """Reserve dests, then paint each page (outline during begin_page)."""


def plot_pages(
    pages: Callable[[], Iterable[Page]],
    plotter: Plotter,
    *,
    ramp: TypeRamp,
    device: str,
    outline: bool = False,
) -> None:
    """Reserve dests, then begin/add/paint. Progress ticks match the books.

    ``pages`` is a ledger factory — section ``.pages``, ``lambda: book.pages(spec)``,
    or any zero-arg callable that yields ``Page``. Not a ``Book``.

    When ``outline``, a ledger post-pass builds dests, then ``add_outline``
    runs during ``begin_page`` (fpdf2 ``start_section`` needs the current page).
    """
    ledger = list(pages())
    slate = get_device(device)
    layout = PlannerLayout(ramp=ramp)
    n = len(ledger)
    dest_titles = (
        {dest: title for title, dest in section_outline_entries(ledger)}
        if outline
        else {}
    )
    for page in ledger:
        plotter.reserve_dest(page.dest)
    for i, page in enumerate(ledger, start=1):
        plotter.begin_page()
        plotter.add_dest(page.dest)
        title = dest_titles.get(page.dest)
        if title is not None:
            plotter.add_outline(title, page.dest)
        layout.paint(page, plotter, slate)
        render_progress(i, n, page.kind)

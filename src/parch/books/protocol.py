"""Book protocol at press/dispatch; ``plot_pages`` walks a page ledger."""

from collections.abc import Callable, Iterable
from typing import Literal, Protocol

from parch.books.outline import OutlineEntry, outline_from_pages, require_outline_dests
from parch.devices import get_device
from parch.fonts.ramp import TypeRamp
from parch.layouts.planner import PlannerLayout
from parch.plotter.protocol import Plotter
from parch.progress import render_progress
from parch.sections.page import Page
from parch.spec import Spec


class Book(Protocol):
    """Press/dispatch surface: ``pages`` + ``plot``.

    Structural only — press does not ``isinstance``-check it.
    ``plot_pages`` is not typed as ``Book`` — it takes a zero-arg pages
    factory (or any duck that is ``Callable[[], Iterable[Page]]``).
    Optional ``outline_entries`` is duck-typed, not a Protocol member.
    """

    def pages(self, spec: Spec) -> list[Page]:
        """Build the book's pages in press order."""

    def plot(self, spec: Spec, plotter: Plotter) -> None:
        """Reserve dests, then paint each page."""


def plot_pages(
    pages: Callable[[], Iterable[Page]],
    plotter: Plotter,
    *,
    ramp: TypeRamp,
    device: str,
    outline: Iterable[OutlineEntry] | Literal[True] = (),
) -> None:
    """Reserve dests, then begin/add/paint. Progress ticks match the books.

    ``pages`` is a ledger factory — section ``.pages``, ``lambda: book.pages(spec)``,
    or any zero-arg callable that yields ``Page``. Not a ``Book``.
    ``outline=True`` derives hubs from the ledger; a sequence registers those dests.
    """
    ledger = list(pages())
    slate = get_device(device)
    layout = PlannerLayout(ramp=ramp)
    n = len(ledger)
    entries = (
        outline_from_pages(ledger)
        if outline is True
        else require_outline_dests(outline, ledger)
    )
    hubs = {entry.dest: entry for entry in entries}
    for page in ledger:
        plotter.reserve_dest(page.dest)
    for i, page in enumerate(ledger, start=1):
        plotter.begin_page()
        plotter.add_dest(page.dest)
        if page.dest in hubs:
            entry = hubs[page.dest]
            plotter.add_outline(entry.title, entry.dest, level=entry.level)
        layout.paint(page, plotter, slate)
        render_progress(i, n, page.kind)

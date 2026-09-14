"""Book protocol. Press takes ``book: Book``; it never sees YearPlanner."""

from typing import Protocol, runtime_checkable

from parch.devices import get_device
from parch.fonts.ramp import TypeRamp
from parch.layouts.planner import PlannerLayout
from parch.plotter.protocol import Plotter
from parch.sections.page import Page
from parch.spec import Spec


@runtime_checkable
class Book(Protocol):
    """Page sequence + plot. ``ramp`` is bound by press.

    ``pages(spec)`` is the book. ``plot`` reserves dests then paints.
    Books implement ``plot`` by calling ``plot_book`` unless they need a
    different walk.
    """

    ramp: TypeRamp

    def pages(self, spec: Spec) -> list[Page]:
        """Build the book's pages in press order."""

    def plot(self, spec: Spec, plotter: Plotter) -> None:
        """Reserve dests, then paint each page through PlannerLayout."""


def plot_book(book: Book, spec: Spec, plotter: Plotter) -> None:
    """Shared reserve-then-paint walk. YearPlanner and ProjectsNotebook use this.

    Sections may emit nav / cover CTA dests this book does not press (the
    leftover of reusing CoverSection + ProjectsSection). Those orphans are
    reserved and bound to the first page so fpdf2 can finish.
    """
    device = get_device(spec.device)
    layout = PlannerLayout(ramp=book.ramp)
    pages = book.pages(spec)
    present = {page.dest for page in pages}
    orphans = [dest for dest in _referenced_dests(pages) if dest not in present]
    for page in pages:
        plotter.reserve_dest(page.dest)
    for dest in orphans:
        plotter.reserve_dest(dest)
    for index, page in enumerate(pages):
        plotter.begin_page()
        plotter.add_dest(page.dest)
        if index == 0:
            for dest in orphans:
                plotter.add_dest(dest)
        layout.paint(page, plotter, device)


def _referenced_dests(pages: list[Page]) -> list[str]:
    """Nav + cover CTA dests, first-seen order. Ticket dests are page dests."""
    found: list[str] = []
    seen: set[str] = set()

    def add(name: str) -> None:
        if name and name not in seen:
            seen.add(name)
            found.append(name)

    for page in pages:
        for item in page.nav:
            add(item.dest)
        for component in page.components:
            cta = getattr(component, "cta_dest", None)
            if isinstance(cta, str):
                add(cta)
    return found

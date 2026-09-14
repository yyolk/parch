"""Book protocol at press/dispatch; ``plot_pages`` walks a page ledger."""

from collections.abc import Callable, Iterable
from typing import Protocol

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
    """

    def pages(self, spec: Spec) -> list[Page]:
        """Build the book's pages in press order."""

    def plot(self, spec: Spec, plotter: Plotter) -> None:
        """Reserve dests, then paint each page."""


def _section_start(kind: str, prev_kind: str | None) -> bool:
    """First non-cover page of a contiguous PageKind run (or first after cover)."""
    if kind == "cover":
        return False
    return prev_kind is None or prev_kind == "cover" or prev_kind != kind


# Reader outline hubs only. Weeks, days, notes, leaves, habits, and pad kinds omitted.
_OUTLINE_KINDS = frozenset(
    {
        "annual",
        "projects_index",
        "meetings_index",
        "tasks_index",
        "review_index",
        "quarter",
        "month",
    }
)


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
    When ``outline``, each allowlisted section start gets a reader bookmark
    on ``page.dest``. Cover, weekly, daily, notes, leaves, habits, and pad
    kinds are omitted — pads with only those kinds get an empty outline.
    """
    ledger = list(pages())
    slate = get_device(device)
    layout = PlannerLayout(ramp=ramp)
    n = len(ledger)
    for page in ledger:
        plotter.reserve_dest(page.dest)
    prev_kind: str | None = None
    for i, page in enumerate(ledger, start=1):
        plotter.begin_page()
        plotter.add_dest(page.dest)
        if (
            outline
            and _section_start(page.kind, prev_kind)
            and page.kind in _OUTLINE_KINDS
        ):
            plotter.add_outline(page.title, page.dest)
        layout.paint(page, plotter, slate)
        render_progress(i, n, page.kind)
        prev_kind = page.kind

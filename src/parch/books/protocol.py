"""Book protocol at press/dispatch; ``plot_pages`` walks a page ledger."""

from collections.abc import Callable, Iterable
from typing import Protocol

from parch.devices import get_device
from parch.fonts.ramp import TypeRamp
from parch.layouts.planner import PlannerLayout
from parch.plotter.protocol import Plotter
from parch.progress import render_progress
from parch.sections.page import Page, PageKind
from parch.spec import OutlineSpec, Spec

# First page of each section kind. Cover is omitted; leaf dest pages
# (project / meeting / task / review / engineering_back) are not starts.
_SECTION_START_KINDS: frozenset[PageKind] = frozenset(
    {
        "annual",
        "projects_index",
        "meetings_index",
        "tasks_index",
        "review_index",
        "quarter",
        "month",
        "habits",
        "weekly",
        "daily",
        "daily_notes",
        "engineering_front",
        "steno",
    }
)


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


def plot_pages(
    pages: Callable[[], Iterable[Page]],
    plotter: Plotter,
    *,
    ramp: TypeRamp,
    device: str,
    outline: OutlineSpec | None = None,
) -> None:
    """Reserve dests, then begin/add/paint. Progress ticks match the books.

    ``pages`` is a ledger factory — section ``.pages``, ``lambda: book.pages(spec)``,
    or any zero-arg callable that yields ``Page``. Not a ``Book``.

    When ``outline.enabled``, emit one flat reader bookmark for the first
    page of each section kind (cover skipped). No printed TOC page.
    """
    ledger = list(pages())
    slate = get_device(device)
    layout = PlannerLayout(ramp=ramp)
    n = len(ledger)
    emit_outline = outline is not None and outline.enabled
    seen_kinds: set[PageKind] = set()
    for page in ledger:
        plotter.reserve_dest(page.dest)
    for i, page in enumerate(ledger, start=1):
        plotter.begin_page()
        plotter.add_dest(page.dest)
        if (
            emit_outline
            and page.kind in _SECTION_START_KINDS
            and page.kind not in seen_kinds
        ):
            seen_kinds.add(page.kind)
            plotter.add_outline(page.title, page.dest)
        layout.paint(page, plotter, slate)
        render_progress(i, n, page.kind)

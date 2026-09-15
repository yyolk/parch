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


# Reader outline hubs only. Weeks, days, notes, leaves, habits, pad,
# rapid-log, and monthly-task kinds omitted.
# RUN: once per contiguous kind-run (tasks_index re-fires after task leaves).
# EACH: every such page (contiguous Q1–Q4; months already interrupted by habits).
_OUTLINE_RUN = frozenset(
    {
        "annual",
        "projects_index",
        "meetings_index",
        "tasks_index",
        "review_index",
        "bujo_key",
        "bujo_index",
        "future_log",
        "collection",
    }
)
_OUTLINE_EACH = frozenset({"quarter", "month", "monthly_log"})


def _section_start(kind: str, prev_kind: str | None) -> bool:
    """First non-cover page of a contiguous PageKind run (or first after cover)."""
    if kind == "cover":
        return False
    return prev_kind is None or prev_kind == "cover" or prev_kind != kind


def _should_outline(kind: str, prev_kind: str | None) -> bool:
    return kind in _OUTLINE_EACH or (
        kind in _OUTLINE_RUN and _section_start(kind, prev_kind)
    )


def outline_entries(pages: Iterable[Page]) -> list[tuple[str, str]]:
    """Reader outline ``(title, dest)`` pairs for a page ledger. No PDF.

    Cover and non-hub kinds are omitted. RUN kinds emit once per kind-run;
    EACH kinds emit every page (Q1–Q4 and each pressed month).
    """
    prev_kind: str | None = None
    entries: list[tuple[str, str]] = []
    for page in pages:
        if _should_outline(page.kind, prev_kind):
            entries.append((page.title, page.dest))
        prev_kind = page.kind
    return entries


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
    When ``outline``, ``outline_entries`` picks reader bookmarks on ``page.dest``.
    Cover, weekly, daily, notes, leaves, habits, pad, rapid-log, and
    monthly-task kinds are omitted — pads with only those kinds get an
    empty outline.
    """
    ledger = list(pages())
    slate = get_device(device)
    layout = PlannerLayout(ramp=ramp)
    n = len(ledger)
    for page in ledger:
        plotter.reserve_dest(page.dest)
    picks = {dest for _title, dest in outline_entries(ledger)} if outline else set()
    for i, page in enumerate(ledger, start=1):
        plotter.begin_page()
        plotter.add_dest(page.dest)
        if page.dest in picks:
            plotter.add_outline(page.title, page.dest)
        layout.paint(page, plotter, slate)
        render_progress(i, n, page.kind)

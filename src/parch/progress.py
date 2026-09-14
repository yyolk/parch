"""One-line TTY progress for ``parch press``. Stdlib bar; iteration advances it."""

import sys
from collections.abc import Callable, Iterator, Sequence

from parch.devices.registry import Device
from parch.layouts.planner import PlannerLayout
from parch.plotter.protocol import Plotter
from parch.sections.page import Page

_BAR_WIDTH = 10

type ProgressBar = Callable[[int, int, str], None]


def render_progress(i: int, n: int, label: str) -> None:
    """Redraw ``parch |████░░░░░░| 4/10  cover`` on stderr when it is a TTY."""
    stream = sys.stderr
    if not stream.isatty():
        return
    filled = 0 if n <= 0 else min(_BAR_WIDTH, (i * _BAR_WIDTH) // n)
    bar = f"{'█' * filled}{'░' * (_BAR_WIDTH - filled)}"
    ending = "\n" if n > 0 and i >= n else ""
    stream.write(f"\rparch |{bar}| {i}/{n}  {label}{ending}")
    stream.flush()


def track(
    pages: Sequence[Page],
    *,
    bar: ProgressBar | None = None,
) -> Iterator[Page]:
    """Yield each page; tick ``bar`` when the consumer finishes that page.

    Reporting is iteration — ``for page in track(pages, bar=...): paint...``.
    ``bar`` defaults to ``render_progress`` (looked up at call time).
    """
    tick = render_progress if bar is None else bar
    n = len(pages)
    for i, page in enumerate(pages, start=1):
        yield page
        tick(i, n, page.kind)


def plot_pages(
    pages: Sequence[Page],
    plotter: Plotter,
    layout: PlannerLayout,
    device: Device,
    *,
    bar: ProgressBar | None = None,
) -> None:
    """Reserve dests, then paint by consuming ``track(pages)``."""
    for page in pages:
        plotter.reserve_dest(page.dest)
    for page in track(pages, bar=bar):
        plotter.begin_page()
        plotter.add_dest(page.dest)
        layout.paint(page, plotter, device)

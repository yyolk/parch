"""Optional progress sink fired from ``begin_page``. Not a Plotter protocol method."""

from collections.abc import Sequence
from pathlib import Path
from typing import override

from parch.fonts.ramp import TypeInk, TypeRamp, TypeRef
from parch.geom import Rect
from parch.plotter.protocol import Plotter, TextAlign
from parch.progress import ProgressSink


class BeginPageHook:
    """Mixin: ``expect_pages`` plus a sink invoked each ``begin_page``.

    Total N and kind labels come from the pages list (known before paint).
    The Plotter protocol is unchanged — this is a hook on the existing call.
    """

    def __init__(self, progress: ProgressSink | None = None) -> None:
        self.progress = progress
        self._progress_kinds: tuple[str, ...] = ()
        self._progress_total = 0
        self._progress_i = 0

    def expect_pages(self, kinds: Sequence[str]) -> None:
        """Record page kinds so each ``begin_page`` can label ``i/N``."""
        self._progress_kinds = tuple(kinds)
        self._progress_total = len(self._progress_kinds)
        self._progress_i = 0

    def _hook_begin_page(self) -> None:
        self._progress_i += 1
        if self.progress is None:
            return
        kind = ""
        if 0 < self._progress_i <= len(self._progress_kinds):
            kind = self._progress_kinds[self._progress_i - 1]
        self.progress(self._progress_i, self._progress_total, kind)

    def _hook_finish(self) -> None:
        close = getattr(self.progress, "close", None)
        if close is not None:
            close()


def expect_page_kinds(plotter: object, kinds: Sequence[str]) -> None:
    """Tell a hooked plotter the page kinds (total N + labels). No-op otherwise."""
    expect = getattr(plotter, "expect_pages", None)
    if callable(expect):
        expect(tuple(kinds))


class ProgressPlotter(BeginPageHook, Plotter):
    """Wrapper: every ``begin_page`` on the inner plotter advances the sink."""

    def __init__(self, inner: Plotter, progress: ProgressSink | None = None) -> None:
        super().__init__(progress)
        self._inner = inner

    @property
    def ramp(self) -> TypeRamp:
        return self._inner.ramp

    @ramp.setter
    def ramp(self, value: TypeRamp) -> None:
        self._inner.ramp = value

    @override
    def begin_page(self) -> None:
        self._inner.begin_page()
        self._hook_begin_page()

    @override
    def reserve_dest(self, name: str) -> None:
        self._inner.reserve_dest(name)

    @override
    def add_dest(self, name: str) -> None:
        self._inner.add_dest(name)

    @override
    def rect(
        self,
        box: Rect,
        *,
        stroke: bool = True,
        fill: bool = False,
        stroke_width: float = 0.2,
        fill_gray: float = 0.92,
        stroke_gray: float = 0.0,
    ) -> None:
        self._inner.rect(
            box,
            stroke=stroke,
            fill=fill,
            stroke_width=stroke_width,
            fill_gray=fill_gray,
            stroke_gray=stroke_gray,
        )

    @override
    def line(
        self,
        x1: float,
        y1: float,
        x2: float,
        y2: float,
        *,
        stroke_width: float = 0.2,
        stroke_gray: float = 0.0,
    ) -> None:
        self._inner.line(
            x1,
            y1,
            x2,
            y2,
            stroke_width=stroke_width,
            stroke_gray=stroke_gray,
        )

    @override
    def text(
        self,
        box: Rect,
        content: str,
        *,
        ink: TypeInk | None = None,
        ref: TypeRef | None = None,
        align: TextAlign = "left",
        gray: float = 0.0,
        small_caps: bool = False,
    ) -> None:
        self._inner.text(
            box,
            content,
            ink=ink,
            ref=ref,
            align=align,
            gray=gray,
            small_caps=small_caps,
        )

    @override
    def link(self, box: Rect, dest: str) -> None:
        self._inner.link(box, dest)

    @override
    def finish(self, path: Path) -> None:
        self._inner.finish(path)
        self._hook_finish()

"""Recording plotter for tests — same protocol, no PDF."""

from pathlib import Path

from parch.geom import Rect
from parch.plotter.protocol import TextAlign

type Op = tuple[object, ...]


class RecordingPlotter:
    def __init__(self) -> None:
        self.ops: list[Op] = []
        self.page = 0

    def begin_page(self) -> None:
        self.page += 1
        self.ops.append(("begin_page", self.page))

    def reserve_dest(self, name: str) -> None:
        self.ops.append(("reserve_dest", name))

    def add_dest(self, name: str) -> None:
        self.ops.append(("add_dest", name, self.page))

    def rect(
        self,
        box: Rect,
        *,
        stroke: bool = True,
        fill: bool = False,
        stroke_width: float = 0.2,
        fill_gray: float = 0.92,
    ) -> None:
        self.ops.append(("rect", box, stroke, fill, stroke_width, fill_gray))

    def line(
        self,
        x1: float,
        y1: float,
        x2: float,
        y2: float,
        *,
        stroke_width: float = 0.2,
    ) -> None:
        self.ops.append(("line", x1, y1, x2, y2, stroke_width))

    def text(
        self,
        box: Rect,
        content: str,
        *,
        size: float = 10,
        align: TextAlign = "left",
        bold: bool = False,
    ) -> None:
        self.ops.append(("text", box, content, size, align, bold))

    def link(self, box: Rect, dest: str) -> None:
        self.ops.append(("link", box, dest))

    def finish(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(repr(self.ops), encoding="utf-8")

    def dests(self) -> list[str]:
        found: list[str] = []
        for op in self.ops:
            match op:
                case ("add_dest", str() as name, _):
                    found.append(name)
        return found

    def links(self) -> list[str]:
        found: list[str] = []
        for op in self.ops:
            match op:
                case ("link", _, str() as dest):
                    found.append(dest)
        return found

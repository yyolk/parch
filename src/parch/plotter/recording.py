"""Recording plotter for tests — same protocol, no PDF."""

from pathlib import Path
from typing import override

from parch.fonts.ramp import JostRamp, TypeInk, TypeRamp, TypeRef
from parch.geom import Rect
from parch.plotter.protocol import (
    Plotter,
    TextAlign,
    TextFace,
    TextFamily,
    TextWeight,
    resolve_text_ink,
)

type Op = tuple[object, ...]


class RecordingPlotter(Plotter):
    def __init__(self, ramp: TypeRamp | None = None) -> None:
        self.ramp: TypeRamp = JostRamp() if ramp is None else ramp
        self.ops: list[Op] = []
        self.page = 0

    @override
    def begin_page(self) -> None:
        self.page += 1
        self.ops.append(("begin_page", self.page))

    @override
    def reserve_dest(self, name: str) -> None:
        self.ops.append(("reserve_dest", name))

    @override
    def add_dest(self, name: str) -> None:
        self.ops.append(("add_dest", name, self.page))

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
        self.ops.append(("rect", box, stroke, fill, stroke_width, fill_gray, stroke_gray))

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
        self.ops.append(("line", x1, y1, x2, y2, stroke_width, stroke_gray))

    @override
    def text(
        self,
        box: Rect,
        content: str,
        *,
        ink: TypeInk | None = None,
        ref: TypeRef | None = None,
        size: float = 10,
        align: TextAlign = "left",
        bold: bool = False,
        face: TextFace = "sans",
        gray: float = 0.0,
        small_caps: bool = False,
        weight: TextWeight | None = None,
        family: TextFamily | None = None,
    ) -> None:
        resolved = resolve_text_ink(self.ramp, ink=ink, ref=ref)
        if resolved is not None:
            size = resolved.size
            weight = resolved.weight
            family = resolved.family
            bold = False
            face = "sans"
        self.ops.append(
            (
                "text",
                box,
                content,
                size,
                align,
                bold,
                face,
                gray,
                small_caps,
                weight,
                family,
            )
        )

    @override
    def link(self, box: Rect, dest: str) -> None:
        self.ops.append(("link", box, dest))

    @override
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

    def text_ops(self) -> list[Op]:
        return [op for op in self.ops if op[0] == "text"]

    def face_only_text(self) -> list[Op]:
        """Text ops that never set ``family`` — FaceBridge / legacy face+bold."""
        return [op for op in self.text_ops() if op[10] is None]

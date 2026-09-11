"""Axis-aligned millimetre rectangles. Origin is top-left, y grows down."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Rect:
    x: float
    y: float
    w: float
    h: float

    @property
    def right(self) -> float:
        return self.x + self.w

    @property
    def bottom(self) -> float:
        return self.y + self.h

    def inset(self, dx: float, dy: float | None = None) -> Rect:
        if dy is None:
            dy = dx
        return Rect(self.x + dx, self.y + dy, self.w - 2 * dx, self.h - 2 * dy)

    def split_top(self, height: float) -> tuple[Rect, Rect]:
        return (
            Rect(self.x, self.y, self.w, height),
            Rect(self.x, self.y + height, self.w, self.h - height),
        )

    def split_left(self, width: float) -> tuple[Rect, Rect]:
        return (
            Rect(self.x, self.y, width, self.h),
            Rect(self.x + width, self.y, self.w - width, self.h),
        )

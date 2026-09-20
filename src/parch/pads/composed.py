"""Concatenate pad pages. No cover."""

from collections.abc import Sequence

from parch.books.protocol import plot_pages
from parch.fonts.ramp import EffectiveRamp, TypeRamp
from parch.pads.protocol import Pad
from parch.plotter.protocol import Plotter
from parch.sections import Page
from parch.spec import Spec


class Composed:
    def __init__(self, pads: Sequence[Pad], ramp: TypeRamp | None = None) -> None:
        self.pads: tuple[Pad, ...] = tuple(pads)
        self.ramp: TypeRamp = EffectiveRamp() if ramp is None else ramp

    def pages(self, spec: Spec) -> list[Page]:
        built: list[Page] = []
        for pad in self.pads:
            built.extend(pad.pages(spec))
        return built

    def plot(self, spec: Spec, plotter: Plotter) -> None:
        plot_pages(
            lambda: self.pages(spec),
            plotter,
            ramp=self.ramp,
            device=spec.device,
            outline=spec.outline,
            top_clearance=spec.top_clearance,
        )

"""Pad-only Gregg sheets — no cover. No steno-notebook book."""

from parch.books.protocol import plot_pages
from parch.fonts.ramp import EffectiveRamp, TypeRamp
from parch.plotter.protocol import Plotter
from parch.sections import Page, StenoPadSection
from parch.spec import Spec


class Steno:
    def __init__(self, ramp: TypeRamp | None = None) -> None:
        self.ramp: TypeRamp = EffectiveRamp() if ramp is None else ramp

    def pages(self, spec: Spec) -> list[Page]:
        return StenoPadSection(spec).pages()

    def plot(self, spec: Spec, plotter: Plotter) -> None:
        plot_pages(
            lambda: self.pages(spec),
            plotter,
            ramp=self.ramp,
            device=spec.device,
            outline=spec.outline,
            top_clearance=spec.top_clearance,
        )

"""Lined / dot-grid mix notebook — cover → one duplex pair section."""

from parch.books.protocol import plot_pages
from parch.fonts.ramp import EffectiveRamp, TypeRamp
from parch.plotter.protocol import Plotter
from parch.sections import CoverSection, Page
from parch.sections.lined_dot_grid import LinedDotGridPadSection
from parch.spec import Spec


class LinedDotGridNotebook:
    def __init__(self, ramp: TypeRamp | None = None) -> None:
        self.ramp: TypeRamp = EffectiveRamp() if ramp is None else ramp

    def pages(self, spec: Spec) -> list[Page]:
        order = "lined-dot-grid" if spec.lined_dot_grid_sheets else "dot-grid-lined"
        body = LinedDotGridPadSection(spec, order).pages()
        landing = body[0].dest
        return [
            *CoverSection(
                spec,
                landing_dest=landing,
                display_title="Lined / Dot grid",
                specs_lead="",
            ).pages(),
            *body,
        ]

    def plot(self, spec: Spec, plotter: Plotter) -> None:
        plot_pages(
            lambda: self.pages(spec),
            plotter,
            ramp=self.ramp,
            device=spec.device,
            outline=spec.outline,
            top_clearance=spec.top_clearance,
        )

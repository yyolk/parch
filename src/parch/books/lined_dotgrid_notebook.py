"""Lined / dot-grid mix notebook — cover → duplex pairs (zip when 2+ types)."""

from parch.books.protocol import plot_pages
from parch.fonts.ramp import EffectiveRamp, TypeRamp
from parch.plotter.protocol import Plotter
from parch.sections import CoverSection, Page
from parch.sections.lined_dot_grid import duplex_pair_pages
from parch.spec import Spec


class LinedDotGridNotebook:
    def __init__(self, ramp: TypeRamp | None = None) -> None:
        self.ramp: TypeRamp = EffectiveRamp() if ramp is None else ramp

    def pages(self, spec: Spec) -> list[Page]:
        body = duplex_pair_pages(spec)
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

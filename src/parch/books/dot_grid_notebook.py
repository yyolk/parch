"""Dot-grid notebook — cover → edge-to-edge clone-dot pages (sibling of YearPlanner)."""

from parch.books.protocol import plot_pages
from parch.dotgrid import dotgrid_pages
from parch.fonts.ramp import EffectiveRamp, TypeRamp
from parch.plotter.protocol import Plotter
from parch.sections import CoverSection, Page
from parch.spec import Spec


class DotGridNotebook:
    def __init__(self, ramp: TypeRamp | None = None) -> None:
        self.ramp: TypeRamp = EffectiveRamp() if ramp is None else ramp

    def pages(self, spec: Spec) -> list[Page]:
        landing = spec.dest_for_dotgrid_pad(1)
        return [
            *CoverSection(
                spec,
                landing_dest=landing,
                display_title="Dot grid",
                specs_lead="",
            ).pages(),
            *dotgrid_pages(spec),
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

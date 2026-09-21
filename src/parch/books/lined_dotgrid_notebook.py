"""Lined / dot-grid notebook — cover → lined, dot, lined, dot, … (sibling book)."""

from parch.books.protocol import plot_pages
from parch.dotgrid import dotgrid_pages
from parch.fonts.ramp import EffectiveRamp, TypeRamp
from parch.lined import lined_pages
from parch.plotter.protocol import Plotter
from parch.sections import CoverSection, Page
from parch.spec import Spec


def alternating_lined_dotgrid_pages(spec: Spec) -> list[Page]:
    """Interleave ``lined_pages`` then ``dotgrid_pages``. Lined starts.

    Pair *i* is lined sheet *i+1* then dot-grid sheet *i+1*. Leftover
    faces from the longer count append after the last pair. Empty
    helpers stay empty — this does not invent a pad protocol.
    """
    lined = lined_pages(spec)
    dots = dotgrid_pages(spec)
    built: list[Page] = []
    for index in range(max(len(lined), len(dots))):
        if index < len(lined):
            built.append(lined[index])
        if index < len(dots):
            built.append(dots[index])
    return built


class LinedDotGridNotebook:
    def __init__(self, ramp: TypeRamp | None = None) -> None:
        self.ramp: TypeRamp = EffectiveRamp() if ramp is None else ramp

    def pages(self, spec: Spec) -> list[Page]:
        landing = spec.dest_for_lined_pad(1)
        return [
            *CoverSection(
                spec,
                landing_dest=landing,
                display_title="Lined / Dot grid",
                specs_lead="",
            ).pages(),
            *alternating_lined_dotgrid_pages(spec),
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

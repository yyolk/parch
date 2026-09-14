"""Engineering notebook — cover → duplex pad faces (sibling of YearPlanner)."""

from parch.devices import get_device
from parch.fonts.ramp import EffectiveRamp, TypeRamp
from parch.layouts.planner import PlannerLayout
from parch.plotter.protocol import Plotter
from parch.progress import render_progress
from parch.sections import CoverSection, EngineeringPadSection, Page
from parch.spec import Spec


class EngineeringNotebook:
    def __init__(self, ramp: TypeRamp | None = None) -> None:
        self.ramp: TypeRamp = EffectiveRamp() if ramp is None else ramp

    def pages(self, spec: Spec) -> list[Page]:
        return [
            *CoverSection(
                spec,
                landing_dest=spec.dest_for_engineering_pad(1, "front"),
                eyebrow="Engineering",
                specs_lead="",
            ).pages(),
            *EngineeringPadSection(spec).pages(),
        ]

    def plot(self, spec: Spec, plotter: Plotter) -> None:
        device = get_device(spec.device)
        layout = PlannerLayout(ramp=self.ramp)
        pages = self.pages(spec)
        n = len(pages)
        for page in pages:
            plotter.reserve_dest(page.dest)
        for i, page in enumerate(pages, start=1):
            plotter.begin_page()
            plotter.add_dest(page.dest)
            layout.paint(page, plotter, device)
            render_progress(i, n, page.kind)

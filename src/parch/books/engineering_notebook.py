"""Engineering notebook — cover → duplex pad sheets (pages factory / sheet expander)."""

from parch.devices import get_device
from parch.fonts.ramp import EffectiveRamp, TypeRamp
from parch.layouts.planner import PlannerLayout
from parch.plotter.protocol import Plotter
from parch.progress import render_progress
from parch.sections import CoverSection, EngineeringPadSection, Page
from parch.spec import Spec


def _sheet_landing(spec: Spec) -> str:
    """Cover CTA / year tap — first front when sheets exist, else the cover itself."""
    if spec.engineering_sheets < 1:
        return spec.cover_dest
    return spec.dest_for_engineering_pad(1, "front")


class EngineeringNotebook:
    """Thin book: ``pages()`` is a factory, not a second paint language."""

    def __init__(self, ramp: TypeRamp | None = None) -> None:
        self.ramp: TypeRamp = EffectiveRamp() if ramp is None else ramp

    def pages(self, spec: Spec) -> list[Page]:
        """Emit Cover, then expand each sheet index to front+back."""
        pad = EngineeringPadSection(spec)
        built = [
            *CoverSection(
                spec,
                landing_dest=_sheet_landing(spec),
                eyebrow="Engineering",
                specs_lead="",
            ).pages(),
        ]
        for sheet in range(1, spec.engineering_sheets + 1):
            built.extend(pad.pages_for(sheet))
        return built

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

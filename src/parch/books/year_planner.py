"""Year planner book — MVP emits cover → one month → one day."""

from parch.devices import get_device
from parch.layouts.planner import PlannerLayout
from parch.plotter.protocol import Plotter
from parch.sections import CoverSection, DailySection, MonthSection, Page
from parch.spec import Spec


class YearPlanner:
    def pages(self, spec: Spec) -> list[Page]:
        return [
            *CoverSection(spec).pages(),
            *MonthSection(spec).pages(),
            *DailySection(spec).pages(),
        ]

    def plot(self, spec: Spec, plotter: Plotter) -> None:
        device = get_device(spec.device)
        layout = PlannerLayout()
        pages = self.pages(spec)
        for page in pages:
            plotter.reserve_dest(page.dest)
        for page in pages:
            plotter.begin_page()
            plotter.add_dest(page.dest)
            layout.paint(page, plotter, device)

"""Year planner book — cover → annual → projects index/dests → meetings → tasks → review → quarters → months+habits → weeks → days.

``Spec.book`` / ``Spec.sections`` filter this walk. The ``projects`` kind keeps
``CoverSection`` + ``ProjectsSection`` only; no sibling book class.
"""

from parch.calendar import months_touching_weeks
from parch.devices import get_device
from parch.fonts.ramp import EffectiveRamp, TypeRamp
from parch.layouts.planner import PlannerLayout
from parch.plotter.protocol import Plotter
from parch.sections import (
    AnnualSection,
    CoverSection,
    DailyNotesSection,
    DailySection,
    HabitSection,
    MeetingSection,
    MonthSection,
    Page,
    ProjectsSection,
    QuarterSection,
    ReviewSection,
    TasksSection,
    WeeklySection,
)
from parch.spec import Spec


class YearPlanner:
    def __init__(self, ramp: TypeRamp | None = None) -> None:
        self.ramp: TypeRamp = EffectiveRamp() if ramp is None else ramp

    def pages(self, spec: Spec) -> list[Page]:
        built: list[Page] = []
        if spec.includes("cover"):
            built.extend(CoverSection(spec).pages())
        if spec.includes("annual"):
            built.extend(AnnualSection(spec).pages())
        if spec.includes("projects"):
            built.extend(ProjectsSection(spec).pages())
        if spec.includes("meetings"):
            built.extend(MeetingSection(spec).pages())
        if spec.includes("tasks"):
            built.extend(TasksSection(spec).pages())
        if spec.includes("review"):
            built.extend(ReviewSection(spec).pages())
        if spec.includes("quarters"):
            built.extend(QuarterSection(spec).pages())
        if spec.includes("months") or spec.includes("habits"):
            month = MonthSection(spec)
            habits = HabitSection(spec)
            for number in spec.months:
                if spec.includes("months"):
                    built.extend(month.pages_for(number))
                if spec.includes("habits"):
                    built.extend(habits.pages_for(number))
        if spec.includes("weeks") or spec.includes("days"):
            weekly = WeeklySection(spec)
            daily = DailySection(spec)
            notes = DailyNotesSection(spec)
            for week in months_touching_weeks(
                spec.year, spec.months, spec.weekday_start
            ):
                if spec.includes("weeks"):
                    built.extend(weekly.pages_for(week))
                if spec.includes("days"):
                    for day in week:
                        if not spec.presses_day(day):
                            continue
                        built.extend(daily.pages_for(day))
                        built.extend(notes.pages_for(day))
        return built

    def plot(self, spec: Spec, plotter: Plotter) -> None:
        device = get_device(spec.device)
        layout = PlannerLayout(ramp=self.ramp)
        pages = self.pages(spec)
        for page in pages:
            plotter.reserve_dest(page.dest)
        for page in pages:
            plotter.begin_page()
            plotter.add_dest(page.dest)
            layout.paint(page, plotter, device)

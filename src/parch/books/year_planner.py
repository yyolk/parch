"""Year planner book — cover → annual → quarters → months+habits → weeks → days+notes → optional lists → review → projects → meetings → tasks."""

from parch.books.protocol import plot_pages
from parch.calendar import months_touching_weeks
from parch.fonts.ramp import EffectiveRamp, TypeRamp
from parch.plotter.protocol import Plotter
from parch.sections import (
    AnnualSection,
    CoverSection,
    DailyNotesSection,
    DailySection,
    Days365Section,
    FavoritesSection,
    HabitSection,
    MeetingSection,
    MonthSection,
    My100Section,
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
        daily = DailySection(spec)
        notes = DailyNotesSection(spec)
        weekly = WeeklySection(spec)
        month = MonthSection(spec)
        habits = HabitSection(spec)
        built = [
            *CoverSection(spec).pages(),
            *AnnualSection(spec).pages(),
            *QuarterSection(spec).pages(),
        ]
        for number in spec.months:
            built.extend(month.pages_for(number))
            built.extend(habits.pages_for(number))
        for week in months_touching_weeks(spec.year, spec.months, spec.weekday_start):
            built.extend(weekly.pages_for(week))
            for day in week:
                if not spec.presses_day(day):
                    continue
                built.extend(daily.pages_for(day))
                built.extend(notes.pages_for(day))
        # Optional year lists (defaults off). After the calendar-first walk
        # so Year→Quar→Mon→…→Day stay contiguous; before review tools.
        built.extend(FavoritesSection(spec).pages())
        built.extend(My100Section(spec).pages())
        built.extend(Days365Section(spec).pages())
        built.extend(ReviewSection(spec).pages())
        built.extend(ProjectsSection(spec).pages())
        built.extend(MeetingSection(spec).pages())
        built.extend(TasksSection(spec).pages())
        return built

    def plot(self, spec: Spec, plotter: Plotter) -> None:
        plot_pages(
            lambda: self.pages(spec),
            plotter,
            ramp=self.ramp,
            device=spec.device,
            outline=spec.outline,
        )

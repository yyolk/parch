"""Optional 365 Days Check-Off Sheet — after annual, before quarters in YearPlanner."""

from parch.calendar import month_touching_weeks, year_day
from parch.components import Checkoff365
from parch.sections.nav import planner_nav
from parch.sections.page import Page
from parch.spec import Spec


class Checkoff365Section:
    """One page when ``spec.checkoff_365``. Dest ``checkoff-365-{year}``. Strip chip **365** when on."""

    def __init__(self, spec: Spec) -> None:
        self.spec = spec

    def pages(self) -> list[Page]:
        spec = self.spec
        if not spec.checkoff_365:
            return []
        days = spec.year_day_count
        first = month_touching_weeks(spec.year, spec.month, spec.weekday_start)[0]
        dests = tuple(
            spec.dest_for_day(day) if spec.presses_day(day) else None
            for day in (year_day(spec.year, number) for number in range(1, days + 1))
        )
        return [
            Page(
                dest=spec.checkoff_365_dest,
                kind="checkoff_365",
                title="365 Days Check-Off Sheet",
                nav=planner_nav(spec, week_dest=spec.dest_for_week(first[0])),
                components=(Checkoff365(year=spec.year, days=days, day_dests=dests),),
            )
        ]

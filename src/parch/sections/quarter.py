from parch.calendar import month_touching_weeks, months_in_quarter
from parch.components import QuarterGrid
from parch.sections.annual import build_annual_month
from parch.sections.nav import planner_nav
from parch.sections.page import Page
from parch.spec import Spec


class QuarterSection:
    def __init__(self, spec: Spec) -> None:
        self.spec = spec

    def pages(self) -> list[Page]:
        spec = self.spec
        built: list[Page] = []
        for quarter in spec.pressed_quarters():
            built.extend(self.pages_for(quarter))
        return built

    def pages_for(self, quarter: int) -> list[Page]:
        spec = self.spec
        months = tuple(
            build_annual_month(spec, month) for month in months_in_quarter(quarter)
        )
        landing_month = next(
            month for month in months_in_quarter(quarter) if spec.presses(month)
        )
        first = month_touching_weeks(spec.year, landing_month, spec.weekday_start)[0]
        dest = spec.dest_for_quarter(quarter)
        return [
            Page(
                dest=dest,
                kind="quarter",
                title=f"Q{quarter} {spec.year}",
                nav=planner_nav(
                    spec, week_dest=spec.dest_for_week(first[0]), month=landing_month
                ),
                components=(
                    QuarterGrid(year=spec.year, quarter=quarter, months=months),
                ),
            )
        ]

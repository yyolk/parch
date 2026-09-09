from parch.calendar import month_name, month_weeks, weekday_labels
from parch.components import MonthCell, MonthGrid
from parch.sections.page import NavItem, Page
from parch.spec import Spec


class MonthSection:
    def __init__(self, spec: Spec) -> None:
        self.spec = spec

    def pages(self) -> list[Page]:
        spec = self.spec
        weeks = []
        for week in month_weeks(spec.year, spec.month, spec.weekday_start):
            cells = []
            for day in week:
                match day:
                    case None:
                        cells.append(MonthCell(day=None))
                    case _ if day == spec.date:
                        cells.append(MonthCell(day=day.day, dest=spec.day_dest))
                    case _:
                        cells.append(MonthCell(day=day.day))
            weeks.append(tuple(cells))
        nav = [
            NavItem("Cover", spec.cover_dest),
            NavItem(f"{spec.day}", spec.day_dest),
        ]
        if spec.notes_pages > 0:
            nav.append(NavItem("Notes", spec.notes_dest(1)))
        return [
            Page(
                dest=spec.month_dest,
                kind="month",
                title=f"{month_name(spec.month)} {spec.year}",
                nav=tuple(nav),
                components=(
                    MonthGrid(
                        year=spec.year,
                        month=spec.month,
                        month_name=month_name(spec.month),
                        weekday_labels=weekday_labels(spec.weekday_start),
                        weeks=tuple(weeks),
                    ),
                ),
            )
        ]

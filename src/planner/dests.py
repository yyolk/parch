"""Page-number map + named-destination names for the book we will emit."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

from planner.calendar_model import (
    YearPlan,
    dest_cover,
    dest_day,
    dest_days,
    dest_month,
    dest_months,
    dest_quarter,
    dest_quarters,
    dest_weeks,
    dest_year,
)


@dataclass
class PageMap:
    """1-based PDF page numbers for every destination we actually emit."""

    pages: dict[str, int] = field(default_factory=dict)

    def put(self, name: str, page: int) -> None:
        self.pages[name] = page

    def has(self, name: str) -> bool:
        return name in self.pages

    def page(self, name: str) -> int:
        return self.pages[name]


def build_page_map(plan: YearPlan, *, specimen: bool) -> PageMap:
    """Assign pages in emit order: cover, year, quarters, months, weeks, days."""
    mapping = PageMap()
    page = 1

    mapping.put(dest_cover(), page)
    page += 1

    mapping.put(dest_year(), page)
    page += 1

    quarters = (1,) if specimen else (1, 2, 3, 4)
    for q in quarters:
        if q == 1:
            mapping.put(dest_quarters(), page)
        mapping.put(dest_quarter(q), page)
        page += 1

    months = (1,) if specimen else tuple(range(1, 13))
    for month in months:
        if month == 1:
            mapping.put(dest_months(), page)
        mapping.put(dest_month(month), page)
        page += 1

    weeks = plan.weeks[:1] if specimen else plan.weeks
    for i, week in enumerate(weeks):
        if i == 0:
            mapping.put(dest_weeks(), page)
        mapping.put(week.dest(), page)
        page += 1

    days: tuple[date, ...] = (plan.jan1,) if specimen else plan.days
    for i, day in enumerate(days):
        if i == 0:
            mapping.put(dest_days(), page)
        mapping.put(dest_day(day), page)
        page += 1

    return mapping

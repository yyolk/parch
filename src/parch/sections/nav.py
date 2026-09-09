"""Planner strip dests. Layout remaps these into Year · Mon · Week · Day · Notes.

YEAR dest: annual page → self; month/week/day/notes → spec.year_dest.

MON dest: month page → that month; daily/notes/week → the landing day's month;
year → first pressed month.

WEEK dest: daily/notes → ISO week of that day; week page → self; year/month → first
ISO week that touches that month (year uses the first pressed month).

DAY / NOTES dests (no generation-time “today”, not spec.day):
- daily / notes → that day (notes-1)
- week → first pressed day in that week (a day that has a daily)
- month → 1st of that month
- year → 1st of the first pressed month
"""

from datetime import date

from parch.sections.page import NavItem
from parch.spec import Spec


def landing_day(spec: Spec, *, day: date | None = None, month: int | None = None) -> date:
    """DAY/NOTES landing. ``spec.day`` is not a today seed."""
    if day is not None:
        return day
    return date(spec.year, month if month is not None else spec.months[0], 1)


def planner_nav(
    spec: Spec,
    *,
    week_dest: str,
    day: date | None = None,
    month: int | None = None,
) -> tuple[NavItem, ...]:
    landing = landing_day(spec, day=day, month=month)
    mon = spec.dest_for_month(month) if month is not None else spec.month_dest
    items = [
        NavItem("Year", spec.year_dest),
        NavItem("Mon", mon),
        NavItem("Week", week_dest),
        NavItem("Day", spec.dest_for_day(landing)),
    ]
    if spec.notes_pages > 0:
        items.append(NavItem("Notes", spec.dest_for_notes(landing, 1)))
    return tuple(items)

"""Planner strip dests. Layout remaps these into Year · Mon · Week · Day · Notes.

YEAR dest: annual page → self; month/week/day/notes → spec.year_dest.

WEEK dest: daily/notes → ISO week of that day; week page → self; year/month → first
ISO week that touches the month.

DAY dest: daily/notes → that day; week → first in-month day of the week;
year/month → spec.date landing.
"""

from datetime import date

from parch.sections.page import NavItem
from parch.spec import Spec


def planner_nav(
    spec: Spec,
    *,
    week_dest: str,
    day: date | None = None,
    month: int | None = None,
) -> tuple[NavItem, ...]:
    landing = day or spec.date
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

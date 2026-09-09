"""Planner strip dests. Layout remaps these into Year · Quar · Mon · Week · Day · Notes.

QUAR is provisional — may come out of the strip later.

YEAR dest: annual page → self; elsewhere → spec.year_dest.

QUAR dest: quarter page → self; month/week/day/notes → quarter containing the
landing month; year → first pressed quarter.

MON dest: month page → that month; daily/notes/week → the landing day's month;
year/quarter → first pressed month in that quarter (year uses first pressed month).

WEEK dest: daily/notes → ISO week of that day; week page → self; year/month/quarter
→ first ISO week that touches the landing month.

DAY / NOTES dests (no generation-time “today”, not spec.day):
- daily / notes → that day (notes-1)
- week → first pressed day in that week (a day that has a daily)
- month / quarter → 1st of the landing month
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
        NavItem("Quar", spec.dest_for_quarter_of(landing.month)),
        NavItem("Mon", mon),
        NavItem("Week", week_dest),
        NavItem("Day", spec.dest_for_day(landing)),
    ]
    if spec.notes_pages > 0:
        items.append(NavItem("Notes", spec.dest_for_notes(landing, 1)))
    return tuple(items)

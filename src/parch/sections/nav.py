"""Planner strip dests. Layout remaps these into Year · Quar · Mon · Habit · Proj · Meet · Task · Week · Day · Notes.

QUAR is provisional — may come out of the strip later.

YEAR dest: annual page → self; elsewhere → spec.year_dest.

QUAR dest: quarter page → self; month/week/day/notes → quarter containing the
landing month; year → first pressed quarter.

MON dest: month page → that month; daily/notes/week → the landing day's month;
year/quarter → first pressed month in that quarter (year uses first pressed month).

HABITS dest (``spec.dest_for_habits(month)``; strip label **Habit**):
- habits page → that month’s habits (self)
- month page → habits for that month
- daily / notes → habits for the landing day’s month
- week → habits for the month of the first pressed day in that week
  (same landing month as DAY would use from week)
- quarter → habits for first pressed month in that quarter
- year → habits for first pressed month

Mirror Mon: Habits dest = ``spec.dest_for_habits(landing.month)``, or the
explicit ``month`` when on a month / habits page.

PROJ dest (strip label **Proj**):
- index page → self
- G projects dest → the index page that lists that row (header chip is the same dest)
- everywhere else → index page 1 (``spec.projects_index_dest``)

MEET dest (strip label **Meet**):
- meetings index → self
- Meeting dest → the index (header chip is the same dest)
- everywhere else → ``spec.meetings_index_dest``

TASK dest (strip label **Task**):
- index page → self
- weekly Tasks dest → the index page that lists that cover (header chip is the same dest)
- everywhere else → index page 1 (``spec.tasks_index_dest``)

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
    proj_dest: str | None = None,
    meet_dest: str | None = None,
    task_dest: str | None = None,
) -> tuple[NavItem, ...]:
    landing = landing_day(spec, day=day, month=month)
    mon = spec.dest_for_month(month) if month is not None else spec.month_dest
    habit_month = month if month is not None else landing.month
    items = [
        NavItem("Year", spec.year_dest),
        NavItem("Quar", spec.dest_for_quarter_of(landing.month)),
        NavItem("Mon", mon),
        NavItem("Habit", spec.dest_for_habits(habit_month)),
        NavItem("Proj", proj_dest or spec.projects_index_dest),
        NavItem("Meet", meet_dest or spec.meetings_index_dest),
        NavItem("Task", task_dest or spec.tasks_index_dest),
        NavItem("Week", week_dest),
        NavItem("Day", spec.dest_for_day(landing)),
    ]
    if spec.notes_pages > 0:
        items.append(NavItem("Notes", spec.dest_for_notes(landing, 1)))
    return tuple(items)

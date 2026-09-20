"""Painted-hour wash via Clock Bound overlap.

Exploratory B keeps shade off Spec. Each well row is a one-hour Clock
Bound (``HH:00``–``HH:59``). Shade when that band ``overlaps`` the
optional ``work_hours`` Bound. Omit ``work_hours`` → no shade.

This is not a floor/ceil hour-tuple ∩ of ``schedule_hours``. A half-hour
``to`` shades the row it intersects, not the next label.
"""

from datetime import time

from tomlrange import Bound, Clock


def painted_hour_bound(hour: int) -> Bound[time]:
    """Closed Clock Bound for the well row labeled ``hour`` (HH:00–HH:59)."""
    if not 0 <= hour <= 23:
        raise ValueError(f"hour out of range: {hour}")
    return Clock.parse({"from": time(hour, 0), "to": time(hour, 59)})


def shade_painted_hour(hour: int, work: Bound[time] | None) -> bool:
    """True when ``work`` overlaps the painted hour band. Omit work → no shade."""
    if work is None:
        return False
    return painted_hour_bound(hour).overlaps(work)

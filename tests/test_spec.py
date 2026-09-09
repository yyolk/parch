from datetime import date

from parch.spec import Spec


def test_dest_names_from_tstrings():
    spec = Spec()
    assert spec.cover_dest == "cover"
    assert spec.year_dest == "year-2026"
    assert spec.months == (1, 2, 3)
    assert spec.month == 1
    assert spec.presses(3)
    assert not spec.presses(4)
    assert spec.month_dest == "month-2026-01"
    assert spec.dest_for_month(1) == "month-2026-01"
    assert spec.day_dest == "2026-01-05"
    assert spec.dest_for_day(date(2026, 1, 15)) == "2026-01-15"
    assert spec.dest_for_week(date(2026, 1, 1)) == "week-2026-W01"
    assert spec.dest_for_week(date(2025, 12, 29)) == "week-2026-W01"
    assert spec.dest_for_week(date(2026, 1, 5)) == "week-2026-W02"
    assert spec.dest_for_week(date(2026, 1, 26)) == "week-2026-W05"
    assert spec.notes_dest(1) == "2026-01-05-notes-1"
    assert spec.dest_for_notes(date(2026, 1, 15), 1) == "2026-01-15-notes-1"


def test_value_bags_are_slotted():
    spec = Spec()
    assert not hasattr(spec, "__dict__")

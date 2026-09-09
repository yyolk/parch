from datetime import date

from parch.calendar import iso_monday, month_days, month_touching_weeks, month_weeks, weekday_labels


def test_january_2026_monday_start():
    weeks = month_weeks(2026, 1, weekday_start=0)
    assert weekday_labels(0)[0] == "Mon"
    # Thursday 1 January sits in the first week, index 3.
    assert weeks[0][3] == date(2026, 1, 1)
    assert weeks[0][0] is None
    assert date(2026, 1, 5).weekday() == 0
    assert weeks[1][0] == date(2026, 1, 5)
    days = month_days(2026, 1)
    assert days[0] == date(2026, 1, 1)
    assert days[-1] == date(2026, 1, 31)
    assert len(days) == 31
    touching = month_touching_weeks(2026, 1, weekday_start=0)
    assert touching[0][0] == date(2025, 12, 29)
    assert iso_monday(date(2026, 1, 1)) == date(2025, 12, 29)

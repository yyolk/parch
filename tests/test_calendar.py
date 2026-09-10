from datetime import date

from parch.calendar import (
    iso_monday,
    month_days,
    month_touching_weeks,
    month_week_bands,
    month_weeks,
    months_touching_weeks,
    weekday_labels,
)


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


def test_month_week_bands_first_seen():
    bands = month_week_bands(2026, (1, 2, 3), weekday_start=0)
    assert [month for month, _weeks in bands] == [1, 2, 3]
    jan, feb, mar = (weeks for _month, weeks in bands)
    assert len(jan) == 5
    assert len(feb) == 4
    assert len(mar) == 5
    assert jan[0][0] == date(2025, 12, 29)
    assert jan[-1][0] == date(2026, 1, 26)
    assert feb[0][0] == date(2026, 2, 2)
    assert mar[-1][-1] == date(2026, 4, 5)
    flat = [week[0] for _month, weeks in bands for week in weeks]
    assert flat == [week[0] for week in months_touching_weeks(2026, (1, 2, 3), weekday_start=0)]
    keys = [week[0].isocalendar()[:2] for week in months_touching_weeks(2026, (1, 2, 3))]
    assert len(keys) == len(set(keys)) == 14

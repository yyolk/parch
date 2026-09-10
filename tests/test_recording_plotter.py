from parch.books import YearPlanner
from parch.calendar import month_days, months_touching_weeks
from parch.components import (
    AnnualGrid,
    AnnualMonth,
    CoverTitle,
    HabitGrid,
    MonthGrid,
    Notes,
    Priorities,
    MeetingAgenda,
    MeetingCover,
    MeetingsIndex,
    ProjectTicket,
    ProjectsBoard,
    ProjectsIndex,
    QuarterGrid,
    Schedule,
    WeekStrip,
)
from parch.plotter import RecordingPlotter
from parch.spec import Spec


def _year_dests(*, notes_pages: int) -> list[str]:
    spec = Spec()
    dests = ["cover", spec.year_dest, spec.projects_dest]
    dests.extend(
        spec.dest_for_projects_index(page)
        for page in range(1, spec.project_index_pages + 1)
    )
    dests.extend(spec.dest_for_project(slot) for slot in range(1, spec.project_count + 1))
    dests.extend(
        spec.dest_for_meetings_index(page)
        for page in range(1, spec.meeting_index_pages + 1)
    )
    dests.extend(spec.dest_for_meeting(slot) for slot in range(1, spec.meeting_count + 1))
    dests.extend(spec.dest_for_quarter(quarter) for quarter in spec.pressed_quarters())
    for month in spec.months:
        dests.append(spec.dest_for_month(month))
        dests.append(spec.dest_for_habits(month))
    for week in months_touching_weeks(2026, spec.months, weekday_start=0):
        dests.append(spec.dest_for_week(week[0]))
        for day in week:
            if not spec.presses_day(day):
                continue
            dests.append(day.isoformat())
            if notes_pages:
                dests.append(f"{day.isoformat()}-notes-1")
    return dests


def test_components_do_not_draw():
    for cls in (
        AnnualGrid,
        AnnualMonth,
        CoverTitle,
        HabitGrid,
        MonthGrid,
        Notes,
        Priorities,
        MeetingAgenda,
        MeetingCover,
        MeetingsIndex,
        ProjectTicket,
        ProjectsBoard,
        ProjectsIndex,
        QuarterGrid,
        Schedule,
        WeekStrip,
    ):
        assert "draw" not in cls.__dict__


def test_book_records_year_dests_and_links():
    spec = Spec(notes_pages=1)
    plotter = RecordingPlotter()
    YearPlanner().plot(spec, plotter)

    dests = plotter.dests()
    assert dests == _year_dests(notes_pages=1)
    assert dests.count("week-2026-W05") == 1
    assert dests.count("week-2026-W09") == 1
    assert dests.count("week-2026-W53") == 1

    links = plotter.links()
    assert "year-2026" in links
    assert "month-2026-01" in links
    assert "month-2026-02" in links
    assert "month-2026-03" in links
    assert "month-2026-07-habits" in links
    assert "projects-index-2026-01" in dests
    assert "projects-index-2026-01" in links
    assert "projects-2026-01" in dests
    assert "projects-2026-01" in links
    assert "projects-2026-08" in dests
    assert "projects-2026-08" in links
    assert "meetings-index-2026-01" in dests
    assert "meetings-index-2026-01" in links
    assert "meeting-2026-01" in dests
    assert "meeting-2026-01" in links
    assert "meeting-2026-06" in dests
    assert "meeting-2026-06" in links
    assert "month-2026-01-habits" in dests
    assert "week-2026-W01" in links
    assert "week-2026-W14" in links
    for month in spec.months:
        for day in month_days(2026, month):
            assert day.isoformat() in links
    assert "2026-02-15-notes-1" in links

    texts = [op[2] for op in plotter.ops if op[0] == "text"]
    assert "Schedule" in texts
    assert "Notes" in texts
    assert "Notes 1/1" in texts
    assert "Year Book" in texts
    assert "Week 01" in texts
    assert "February 2026" in texts
    assert "toolbar 8 mm - not a well" not in texts


def test_notes_pages_zero_skips_wells():
    plotter = RecordingPlotter()
    YearPlanner().plot(Spec(notes_pages=0), plotter)
    dests = plotter.dests()
    assert dests == _year_dests(notes_pages=0)
    assert not any("-notes-" in name for name in dests)
    assert "2026-01-05-notes-1" not in plotter.links()

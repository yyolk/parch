from datetime import date
from pathlib import Path

from parch.spec import Spec


def test_dest_names_from_tstrings():
    spec = Spec()
    assert spec.cover_dest == "cover"
    assert spec.year_dest == "year-2026"
    assert spec.months == tuple(range(1, 13))
    assert spec.month == 1
    assert spec.presses(3)
    assert spec.presses(12)
    assert spec.presses_day(date(2026, 12, 31))
    assert not spec.presses_day(date(2025, 12, 29))
    assert not spec.presses_day(date(2027, 1, 1))
    assert spec.quarter_dest == "quarter-2026-Q1"
    assert spec.dest_for_quarter(1) == "quarter-2026-Q1"
    assert spec.dest_for_quarter(3) == "quarter-2026-Q3"
    assert spec.pressed_quarters() == (1, 2, 3, 4)
    assert spec.month_dest == "month-2026-01"
    assert spec.dest_for_month(1) == "month-2026-01"
    assert spec.dest_for_habits(7) == "month-2026-07-habits"
    assert spec.habit_columns == 10
    assert spec.priority_rows == 6
    assert spec.projects_dest == "projects-2026"
    assert spec.projects_index_dest == "projects-index-2026"
    assert spec.project_cards == 3
    assert spec.project_tasks == 4
    assert spec.project_index_rows == 9
    assert spec.project_page_count == 9
    assert spec.dest_for_project(1) == "project-2026-01"
    assert spec.dest_for_project(9) == "project-2026-09"
    assert spec.day_dest == "2026-01-05"
    assert spec.dest_for_day(date(2026, 1, 15)) == "2026-01-15"
    assert spec.dest_for_week(date(2026, 1, 1)) == "week-2026-W01"
    assert spec.dest_for_week(date(2025, 12, 29)) == "week-2026-W01"
    assert spec.dest_for_week(date(2026, 1, 5)) == "week-2026-W02"
    assert spec.dest_for_week(date(2026, 1, 26)) == "week-2026-W05"
    assert spec.notes_dest(1) == "2026-01-05-notes-1"
    assert spec.dest_for_notes(date(2026, 1, 15), 1) == "2026-01-15-notes-1"


def test_habit_columns_from_toml_keys():
    assert Spec.from_mapping({"habits": {"columns": 8}}).habit_columns == 8
    assert Spec.from_mapping({"habits": {"rows": 6}}).habit_columns == 6
    assert Spec.from_mapping({"habit_rows": 7}).habit_columns == 7
    assert Spec.from_path(Path("examples/mvp.toml")).habit_columns == 10
    assert Spec.from_mapping({"projects": {"cards": 2, "tasks": 5}}).project_cards == 2
    assert Spec.from_mapping({"projects": {"cards": 2, "tasks": 5}}).project_tasks == 5
    assert Spec.from_mapping({"projects": {"index_rows": 8}}).project_index_rows == 8
    mvp = Spec.from_path(Path("examples/mvp.toml"))
    assert mvp.project_cards == 3
    assert mvp.project_tasks == 4
    assert mvp.project_index_rows == 9


def test_value_bags_are_slotted():
    spec = Spec()
    assert not hasattr(spec, "__dict__")

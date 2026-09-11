from datetime import date
from pathlib import Path

import pytest

from parch import ConfigError
from parch.fonts import OVERLAY_SCHEMA_VERSION, TypeOverlay, TypePatch
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
    assert spec.projects_index_dest == "projects-index-2026-01"
    assert spec.dest_for_projects_index(1) == "projects-index-2026-01"
    assert spec.project_cards == 3
    assert spec.project_tasks == 4
    assert spec.project_tickets == 8
    assert spec.project_index_pages == 1
    assert spec.project_count == 8
    assert spec.dest_for_project(1) == "projects-2026-01"
    assert spec.dest_for_project(8) == "projects-2026-08"
    assert spec.dest_for_projects_index_of(8) == "projects-index-2026-01"
    assert spec.meetings_index_dest == "meetings-index-2026"
    assert spec.meeting_index_rows == 16
    assert spec.meeting_count == 16
    assert spec.dest_for_meeting(1) == "meeting-2026-01"
    assert spec.dest_for_meeting(16) == "meeting-2026-16"
    assert spec.dest_for_meetings_index_of(16) == "meetings-index-2026"
    assert spec.dest_for_day(date(2026, 1, 15)) == "2026-01-15"
    assert spec.dest_for_week(date(2026, 1, 1)) == "week-2026-W01"
    assert spec.dest_for_week(date(2025, 12, 29)) == "week-2026-W01"
    assert spec.dest_for_week(date(2026, 1, 5)) == "week-2026-W02"
    assert spec.dest_for_week(date(2026, 1, 26)) == "week-2026-W05"
    assert spec.tasks_index_dest == "tasks-index-2026-Q1"
    assert spec.dest_for_tasks_index(3) == "tasks-index-2026-Q3"
    assert spec.dest_for_task(date(2026, 1, 1)) == "tasks-2026-W01"
    assert spec.dest_for_task(date(2025, 12, 29)) == "tasks-2026-W01"
    assert spec.dest_for_tasks_index_of(date(2026, 1, 1)) == "tasks-index-2026-Q1"
    assert spec.dest_for_tasks_index_of(date(2026, 7, 15)) == "tasks-index-2026-Q3"
    assert spec.task_rows == 6
    assert spec.review_index_dest == "review-index-2026"
    assert spec.dest_for_review(date(2026, 1, 1)) == "review-2026-W01"
    assert spec.dest_for_review(date(2025, 12, 29)) == "review-2026-W01"
    assert spec.dest_for_notes(date(2026, 1, 15), 1) == "2026-01-15-notes-1"


def test_habit_columns_from_toml_keys():
    assert Spec.from_mapping({"habits": {"columns": 8}}).habit_columns == 8
    assert Spec.from_mapping({"habits": {"rows": 6}}).habit_columns == 6
    assert Spec.from_mapping({"habit_rows": 7}).habit_columns == 7
    assert Spec.from_path(Path("examples/mvp.toml")).habit_columns == 10
    assert Spec.from_mapping({"projects": {"cards": 2, "tasks": 5}}).project_cards == 2
    assert Spec.from_mapping({"projects": {"cards": 2, "tasks": 5}}).project_tasks == 5
    assert Spec.from_mapping({"projects": {"tickets": 6}}).project_tickets == 6
    assert Spec.from_mapping({"projects": {"tickets_per_page": 7}}).project_tickets == 7
    triple = Spec.from_mapping({"projects": {"index_pages": 3, "tickets": 8}})
    assert triple.project_index_pages == 3
    assert triple.project_count == 24
    assert triple.dest_for_projects_index(2) == "projects-index-2026-02"
    assert triple.dest_for_project(9) == "projects-2026-09"
    assert triple.dest_for_projects_index_of(9) == "projects-index-2026-02"
    assert Spec.from_mapping({"meetings": {"index_rows": 12}}).meeting_index_rows == 12
    assert Spec.from_mapping({"tasks": {"rows": 5}}).task_rows == 5
    mvp = Spec.from_path(Path("examples/mvp.toml"))
    assert mvp.project_cards == 3
    assert mvp.project_tasks == 4
    assert mvp.project_tickets == 8
    assert mvp.project_index_pages == 3
    assert mvp.project_count == 24
    assert mvp.meeting_index_rows == 16
    assert mvp.meeting_count == 16
    assert mvp.task_rows == 6
    assert mvp.type_overlay == TypeOverlay()


def test_typography_overlay_from_toml():
    overlayed = Spec.from_path(Path("examples/mvp-typo-overlay.toml"))
    assert overlayed.type_overlay == TypeOverlay(
        schema_version=OVERLAY_SCHEMA_VERSION,
        chrome=TypePatch(size=9.6, weight="bold"),
        title=TypePatch(size=14, weight="bold"),
        eyebrow=TypePatch(size=13, weight="bold"),
        display=TypePatch(size=48, weight="heavy"),
    )
    partial = Spec.from_mapping(
        {
            "typography": {
                "overlay": {
                    "schema_version": OVERLAY_SCHEMA_VERSION,
                    "chrome": {"size": 9.2},
                    "title": {"weight": "bold"},
                }
            }
        }
    )
    assert partial.type_overlay.chrome == TypePatch(size=9.2)
    assert partial.type_overlay.title == TypePatch(weight="bold")
    assert partial.type_overlay.display is None
    assert partial.type_overlay.schema_version == OVERLAY_SCHEMA_VERSION


def test_typography_unknown_keys_fail_loudly():
    with pytest.raises(ConfigError, match="unknown typography key 'family'"):
        Spec.from_mapping({"typography": {"family": "jost"}})
    with pytest.raises(ConfigError, match="unknown step 'cover_year'"):
        Spec.from_mapping(
            {
                "typography": {
                    "overlay": {
                        "schema_version": OVERLAY_SCHEMA_VERSION,
                        "cover_year": {"size": 48},
                    }
                }
            }
        )
    with pytest.raises(ConfigError, match="unknown step 'chrome.family'"):
        Spec.from_mapping(
            {
                "typography": {
                    "overlay": {
                        "schema_version": OVERLAY_SCHEMA_VERSION,
                        "chrome": {"family": "jost"},
                    }
                }
            }
        )
    with pytest.raises(ConfigError, match="bad weight 'hairline'"):
        Spec.from_mapping(
            {
                "typography": {
                    "overlay": {
                        "schema_version": OVERLAY_SCHEMA_VERSION,
                        "chrome": {"weight": "hairline"},
                    }
                }
            }
        )
    with pytest.raises(ConfigError, match="nonpositive size"):
        Spec.from_mapping(
            {
                "typography": {
                    "overlay": {"schema_version": OVERLAY_SCHEMA_VERSION, "chrome": {"size": 0}}
                }
            }
        )
    with pytest.raises(ConfigError, match="schema_version"):
        Spec.from_mapping({"typography": {"overlay": {"chrome": {"size": 9.2}}}})
    with pytest.raises(ConfigError, match="typography must be a TOML table"):
        Spec.from_mapping({"typography": "loud"})


def test_value_bags_are_slotted():
    spec = Spec()
    assert not hasattr(spec, "__dict__")

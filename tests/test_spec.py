import tomllib
from datetime import date, time, timedelta
from pathlib import Path

import pytest
from tomlrange import Bound, Clock

from parch import ConfigError
from parch.fonts import OVERLAY_SCHEMA_VERSION, TypeOverlay, TypePatch
from parch.spec import Spec


def test_dest_names_from_tstrings():
    spec = Spec()
    assert spec.cover_dest == "cover"
    assert spec.year_dest == "year-2026"
    assert spec.favorites_pages == 0
    assert spec.favorites_dest == "favorites-2026"
    assert spec.checkoff_365 is False
    assert spec.year_day_count == 365
    assert spec.checkoff_365_dest == "checkoff-365-2026"
    assert spec.book == "year-planner"
    assert spec.title is None
    assert Spec.from_mapping({}).title is None
    assert Spec.from_mapping({"title": "Year planner"}).title == "Year planner"
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
    assert spec.task_rows == 6
    assert spec.review_index_dest == "review-index-2026"
    assert spec.dest_for_review(date(2026, 1, 1)) == "review-2026-W01"
    assert spec.dest_for_review(date(2025, 12, 29)) == "review-2026-W01"
    assert spec.dest_for_notes(date(2026, 1, 15), 1) == "2026-01-15-notes-1"
    assert spec.engineering_sheets == 0
    assert spec.steno_sheets == 0
    assert spec.dot_grid_sheets == 0
    assert spec.outline is False
    assert spec.my_100 is False
    assert spec.my_100_dest == "my-100-2026"
    assert spec.dest_for_my_100(1) == "my-100-2026"
    assert spec.dest_for_my_100(2) == "my-100-2026-02"
    assert spec.checkoff_365 is False
    assert spec.bujo_index_pages == 2
    assert spec.bujo_collections == 24
    assert spec.bujo_key_dest == "bujo-key-2026"
    assert spec.bujo_index_dest == "bujo-index-2026-01"
    assert spec.dest_for_bujo_index(2) == "bujo-index-2026-02"
    assert spec.bujo_future_pages == 4
    assert spec.bujo_future_dest == "bujo-future-2026-01"
    assert spec.dest_for_bujo_future(4) == "bujo-future-2026-04"
    assert spec.dest_for_month_tasks(1) == "month-2026-01-tasks"
    assert spec.dest_for_bujo_collection(1) == "bujo-col-2026-01"
    assert spec.dest_for_bujo_collection(24) == "bujo-col-2026-24"


def test_habit_columns_from_toml_keys():
    assert Spec.from_mapping({"habits": {"columns": 8}}).habit_columns == 8
    assert Spec.from_mapping({"habits": {"rows": 6}}).habit_columns == 6
    assert Spec.from_mapping({"habit_rows": 7}).habit_columns == 7
    assert Spec.from_path(Path("examples/nomad.toml")).habit_columns == 10
    assert Spec.from_mapping({"projects": {"cards": 2}}).project_cards == 2
    leftover = Spec.from_mapping({"projects": {"cards": 2, "tasks": 5}})
    assert leftover.project_cards == 2
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
    assert Spec.from_mapping({"book": "projects-notebook"}).book == "projects-notebook"
    assert Spec.from_mapping({"book": "projects-notebook"}).title is None
    assert Spec.from_path(Path("examples/projects.toml")).title == "Projects"
    assert (
        Spec.from_mapping(
            {"book": "engineering-notebook", "engineering": {"sheets": 1}}
        ).book
        == "engineering-notebook"
    )
    assert Spec.from_mapping({"engineering": {"sheets": 3}}).engineering_sheets == 3
    assert Spec.from_path(Path("examples/engineering-pad.toml")).engineering_sheets == 1
    assert (
        Spec.from_path(Path("examples/engineering.toml")).book == "engineering-notebook"
    )
    assert Spec.from_path(Path("examples/engineering.toml")).title == "Engineering"
    bujo = Spec.from_path(Path("examples/nomad-bujo.toml"))
    assert bujo.book == "bullet-journal"
    assert bujo.title == "Bullet journal"
    assert bujo.bujo_index_pages == 2
    assert bujo.bujo_collections == 24
    assert bujo.habit_columns == 8
    assert Spec.from_mapping({"book": "bullet-journal"}).book == "bullet-journal"
    assert Spec.from_mapping({"months": [1]}).bujo_future_pages == 1
    assert Spec.from_path(Path("examples/engineering.toml")).outline is True
    assert Spec.from_mapping({"outline": True}).outline is True
    with pytest.raises(ConfigError, match="outline must be a boolean"):
        Spec.from_mapping({"outline": "true"})
    assert Spec.from_mapping({"favorites": True}).favorites_pages == 1
    assert Spec.from_mapping({"favorites_pages": 1}).favorites_pages == 1
    with pytest.raises(ConfigError, match="favorites must be a boolean"):
        Spec.from_mapping({"favorites": "true"})
    with pytest.raises(ConfigError, match="favorites_pages must be"):
        Spec(favorites_pages=2)
    assert Spec.from_mapping({"my_100": True}).my_100 is True
    assert Spec.from_path(Path("examples/nomad.toml")).my_100 is False
    assert Spec.from_path(Path("examples/nomad.toml")).favorites_pages == 0
    assert Spec.from_path(Path("examples/nomad.toml")).checkoff_365 is False
    extras = Spec.from_path(Path("examples/nomad-extras.toml"))
    assert extras.favorites_pages == 1
    assert extras.my_100 is True
    assert extras.checkoff_365 is True
    assert extras.notes_pages == 0
    assert extras.months == (1,)
    with pytest.raises(ConfigError, match="my_100 must be a boolean"):
        Spec.from_mapping({"my_100": 1})
    with pytest.raises(ConfigError, match="my 100 page must be >= 1"):
        Spec().dest_for_my_100(0)
    assert Spec.from_mapping({"steno": {"sheets": 2}}).steno_sheets == 2
    assert Spec.from_path(Path("examples/steno-pad.toml")).steno_sheets == 1
    assert Spec.from_mapping({"dot_grid": {"sheets": 2}}).dot_grid_sheets == 2
    assert Spec.from_path(Path("examples/dot-grid.toml")).dot_grid_sheets == 1
    with pytest.raises(ConfigError, match="book must be"):
        Spec.from_mapping({"book": "meetings-notebook"})
    with pytest.raises(ConfigError, match="engineering-notebook requires"):
        Spec(book="engineering-notebook")
    nomad = Spec.from_path(Path("examples/nomad.toml"))
    assert nomad.device == "supernote-nomad"
    assert nomad.book == "year-planner"
    assert nomad.title == "Year planner"
    assert nomad.outline is True
    assert nomad.project_cards == 3
    assert nomad.project_tickets == 8
    assert nomad.project_index_pages == 3
    assert nomad.project_count == 24
    assert nomad.meeting_index_rows == 16
    assert nomad.meeting_count == 16
    assert nomad.task_rows == 6
    assert nomad.type_overlay == TypeOverlay()
    assert Spec().top_clearance is None
    assert nomad.top_clearance is None
    scribe = Spec.from_path(Path("examples/scribe.toml"))
    assert scribe.device == "kindle-scribe"
    assert scribe.top_clearance == 0.0


def test_top_clearance_toml_override():
    assert Spec.from_mapping({}).top_clearance is None
    assert Spec.from_mapping({"top_clearance": 0}).top_clearance == 0.0
    assert Spec.from_mapping({"top_clearance": 8}).top_clearance == 8.0
    assert Spec.from_mapping({"top_clearance": 0.0}).top_clearance == 0.0
    with pytest.raises(ConfigError, match="top_clearance must be >= 0"):
        Spec(top_clearance=-1)
    with pytest.raises(ConfigError, match="top_clearance must be a number"):
        Spec.from_mapping({"top_clearance": False})
    with pytest.raises(ConfigError, match="top_clearance must be a number"):
        Spec.from_mapping({"top_clearance": "0"})


def test_typography_overlay_from_toml():
    overlayed = Spec.from_path(Path("examples/nomad-typo-overlay.toml"))
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
                    "overlay": {
                        "schema_version": OVERLAY_SCHEMA_VERSION,
                        "chrome": {"size": 0},
                    }
                }
            }
        )
    with pytest.raises(ConfigError, match="schema_version"):
        Spec.from_mapping({"typography": {"overlay": {"chrome": {"size": 9.2}}}})
    with pytest.raises(ConfigError, match="typography must be a TOML table"):
        Spec.from_mapping({"typography": "loud"})


def test_parse_months_list_and_tomlrange_table(tmp_path: Path):
    assert Spec.from_mapping({"months": [1, 2, 3]}).months == (1, 2, 3)
    assert Spec.from_mapping({"months": [1, 3]}).months == (1, 3)
    assert Spec.from_mapping({"months": {"from": 1, "to": 3}}).months == (1, 2, 3)
    assert Spec.from_mapping({"months": {"from": 6, "to": 6}}).months == (6,)
    assert Spec.from_mapping({}).months == tuple(range(1, 13))
    assert Spec.from_mapping({"month": 7}).months == (7,)
    assert Spec.from_path(Path("examples/nomad.toml")).months == tuple(range(1, 13))
    assert Spec.from_path(Path("examples/nomad-extras.toml")).months == (1,)

    inline = tmp_path / "inline.toml"
    inline.write_text("months = { from = 4, to = 6 }\n", encoding="utf-8")
    header = tmp_path / "header.toml"
    header.write_text("[months]\nfrom = 1\nto = 12\n", encoding="utf-8")
    assert Spec.from_path(inline).months == (4, 5, 6)
    assert Spec.from_path(header).months == tuple(range(1, 13))

    with pytest.raises(ConfigError, match="months must not be empty"):
        Spec.from_mapping({"months": []})
    with pytest.raises(ConfigError, match="expected a table"):
        Spec.from_mapping({"months": "1..12"})
    with pytest.raises(ConfigError, match="is after"):
        Spec.from_mapping({"months": {"from": 4, "to": 2}})
    with pytest.raises(ConfigError, match="above month"):
        Spec.from_mapping({"months": {"from": 1, "to": 13}})


def test_value_bags_are_slotted():
    spec = Spec()
    assert not hasattr(spec, "__dict__")


def test_daily_schedule_default_and_toml_local_times(tmp_path: Path):
    default = Spec()
    assert isinstance(default.schedule, Bound)
    assert default.schedule.domain is Clock.domain
    assert default.schedule.start == time(7, 0)
    assert default.schedule.stop == time(16, 0)
    assert default.schedule_hours == tuple(range(7, 17))

    mapped = Spec.from_mapping(
        {"daily": {"schedule": {"from": time(7, 0), "to": time(16, 0)}}}
    )
    assert mapped.schedule.as_tuple() == (time(7, 0), time(16, 0))
    assert mapped.schedule.domain is Clock.domain
    assert mapped.schedule_hours == tuple(range(7, 17))

    nomad = Spec.from_path(Path("examples/nomad.toml"))
    assert nomad.schedule.start == time(7, 0)
    assert nomad.schedule.stop == time(16, 0)
    assert nomad.schedule_hours == tuple(range(7, 17))

    inline = tmp_path / "inline.toml"
    inline.write_text(
        "[daily]\nschedule = { from = 07:00:00, to = 16:00:00 }\n",
        encoding="utf-8",
    )
    header = tmp_path / "header.toml"
    header.write_text(
        "[daily.schedule]\nfrom = 09:00:00\nto = 17:00:00\n",
        encoding="utf-8",
    )
    assert Spec.from_path(inline).schedule_hours == tuple(range(7, 17))
    late = Spec.from_path(header)
    assert late.schedule.start == time(9, 0)
    assert late.schedule.stop == time(17, 0)
    assert late.schedule_hours == tuple(range(9, 18))


def test_daily_schedule_rejects_bad_tables():
    with pytest.raises(ConfigError, match="expected a table"):
        Spec.from_mapping({"daily": {"schedule": [7, 16]}})
    with pytest.raises(ConfigError, match="unknown keys"):
        Spec.from_mapping(
            {
                "daily": {
                    "schedule": {"from": time(7), "to": time(16), "until": time(17)}
                }
            }
        )
    with pytest.raises(ConfigError, match="must have keys"):
        Spec.from_mapping({"daily": {"schedule": {"from": time(7)}}})


def test_daily_schedule_int_step_is_clock_grain_minutes():
    spec = Spec.from_mapping(
        {"daily": {"schedule": {"from": time(7), "to": time(16), "step": 30}}}
    )
    assert spec.schedule.as_tuple() == (time(7, 0), time(16, 0))
    assert spec.schedule.step == timedelta(minutes=30)
    assert spec.schedule.as_table()["step"] == 30
    assert spec.schedule_hours == tuple(range(7, 17))


def test_daily_schedule_time_shaped_step_is_clock_grain(tmp_path: Path):
    mapped = Spec.from_mapping(
        {"daily": {"schedule": {"from": time(7), "to": time(16), "step": time(0, 30)}}}
    )
    assert mapped.schedule.domain is Clock.domain
    assert mapped.schedule.as_tuple() == (time(7, 0), time(16, 0))
    assert mapped.schedule.step == timedelta(minutes=30)
    assert mapped.schedule.as_table()["step"] == 30
    assert mapped.schedule_hours == tuple(range(7, 17))

    path = tmp_path / "half.toml"
    path.write_text(
        "[daily]\nschedule = { from = 07:00:00, to = 16:00:00, step = 00:30:00 }\n",
        encoding="utf-8",
    )
    parsed = Spec.from_path(path)
    assert parsed.schedule.step == timedelta(minutes=30)
    assert parsed.schedule.as_table()["step"] == 30
    assert parsed.schedule_hours == tuple(range(7, 17))


def test_daily_schedule_ignores_leftover_int_keys():
    leftover = Spec.from_mapping({"daily": {"schedule_from": 8, "schedule_to": 18}})
    assert leftover.schedule.as_tuple() == (time(7, 0), time(16, 0))
    present = Spec.from_mapping(
        {
            "daily": {
                "schedule": {"from": time(9), "to": time(17)},
                "schedule_from": 8,
                "schedule_to": 18,
            }
        }
    )
    assert present.schedule.as_tuple() == (time(9, 0), time(17, 0))


def test_daily_schedule_rejects_from_after_to():
    with pytest.raises(ConfigError, match="is after"):
        Spec.from_mapping({"daily": {"schedule": {"from": time(16), "to": time(7)}}})


def test_daily_schedule_rejects_non_time_values():
    with pytest.raises(ConfigError, match="expected time, got int"):
        Spec.from_mapping({"daily": {"schedule": {"from": 7, "to": 16}}})
    with pytest.raises(ConfigError, match="expected time, got str"):
        Spec.from_mapping(
            {"daily": {"schedule": {"from": "07:00:00", "to": "16:00:00"}}}
        )


def test_to_toml_roundtrips_default_spec():
    spec = Spec()
    assert Spec.from_mapping(spec.to_mapping()) == spec
    dumped = tomllib.loads(spec.to_toml())
    assert Spec.from_mapping(dumped) == spec
    assert dumped["months"] == {"from": 1, "to": 12}
    assert "title" not in dumped
    assert "top_clearance" not in dumped
    assert "typography" not in dumped
    assert dumped["daily"]["schedule"] == {"from": time(7, 0), "to": time(16, 0)}


def test_to_toml_roundtrips_examples():
    for path in sorted(Path("examples").glob("*.toml")):
        spec = Spec.from_path(path)
        assert Spec.from_mapping(tomllib.loads(spec.to_toml())) == spec
        assert Spec.from_mapping(spec.to_mapping()) == spec


def test_to_toml_roundtrips_overlay_and_sparse_months():
    spec = Spec.from_path(Path("examples/nomad-typo-overlay.toml"))
    assert spec.months == tuple(range(1, 13))
    dumped = tomllib.loads(spec.to_toml())
    assert dumped["typography"]["overlay"]["chrome"]["size"] == 9.6
    assert Spec.from_mapping(dumped) == spec

    sparse = Spec(months=(1, 3, 5), title='Say "hi"')
    loaded = Spec.from_mapping(tomllib.loads(sparse.to_toml()))
    assert loaded == sparse
    assert tomllib.loads(sparse.to_toml())["months"] == [1, 3, 5]

    zeroed = Spec(device="kindle-scribe", top_clearance=0.0)
    dumped_zero = tomllib.loads(zeroed.to_toml())
    assert dumped_zero["top_clearance"] == 0
    assert Spec.from_mapping(dumped_zero) == zeroed
    assert Spec.from_mapping(zeroed.to_mapping()) == zeroed


def test_to_toml_includes_schedule_step():
    spec = Spec.from_mapping(
        {"daily": {"schedule": {"from": time(7), "to": time(16), "step": 30}}}
    )
    dumped = tomllib.loads(spec.to_toml())
    assert dumped["daily"]["schedule"]["step"] == 30
    assert Spec.from_mapping(dumped) == spec


def test_daily_schedule_hours_floor_from_ceil_to():
    half = Spec.from_mapping(
        {"daily": {"schedule": {"from": time(7, 30), "to": time(16, 30)}}}
    )
    assert half.schedule_hours == tuple(range(7, 18))
    late = Spec.from_mapping(
        {"daily": {"schedule": {"from": time(23, 30), "to": time(23, 59)}}}
    )
    assert late.schedule_hours == (23,)


def test_daily_work_hours_optional_clock_bound(tmp_path: Path):
    assert Spec().work_hours is None
    assert Spec.from_mapping({}).work_hours is None
    assert Spec.from_path(Path("examples/nomad.toml")).work_hours is None
    assert "work_hours" not in tomllib.loads(Spec().to_toml())["daily"]
    assert "work_hours" not in Spec().to_mapping()["daily"]

    mapped = Spec.from_mapping(
        {"daily": {"work_hours": {"from": time(9, 0), "to": time(17, 0)}}}
    )
    assert mapped.work_hours is not None
    assert mapped.work_hours.domain is Clock.domain
    assert mapped.work_hours.as_tuple() == (time(9, 0), time(17, 0))
    dumped = tomllib.loads(mapped.to_toml())
    assert dumped["daily"]["work_hours"] == {"from": time(9, 0), "to": time(17, 0)}
    assert Spec.from_mapping(dumped) == mapped
    assert Spec.from_mapping(mapped.to_mapping()) == mapped

    path = tmp_path / "work.toml"
    path.write_text(
        "[daily]\nwork_hours = { from = 09:30:00, to = 11:30:00 }\n",
        encoding="utf-8",
    )
    parsed = Spec.from_path(path)
    assert parsed.work_hours is not None
    assert parsed.work_hours.as_tuple() == (time(9, 30), time(11, 30))


def test_daily_work_hours_rejects_bad_tables():
    with pytest.raises(ConfigError, match="expected a table"):
        Spec.from_mapping({"daily": {"work_hours": [9, 17]}})
    with pytest.raises(ConfigError, match="unknown keys"):
        Spec.from_mapping(
            {
                "daily": {
                    "work_hours": {"from": time(9), "to": time(17), "until": time(18)}
                }
            }
        )
    with pytest.raises(ConfigError, match="must have keys"):
        Spec.from_mapping({"daily": {"work_hours": {"from": time(9)}}})
    with pytest.raises(ConfigError, match="is after"):
        Spec.from_mapping({"daily": {"work_hours": {"from": time(17), "to": time(9)}}})
    with pytest.raises(ConfigError, match="expected time, got int"):
        Spec.from_mapping({"daily": {"work_hours": {"from": 9, "to": 17}}})

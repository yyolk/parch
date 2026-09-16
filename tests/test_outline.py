from datetime import date
from pathlib import Path

from inline_snapshot import snapshot
from pypdf import PdfReader
from pypdf.generic import Destination

from parch.books import (
    BulletJournal,
    EngineeringNotebook,
    ProjectsNotebook,
    YearPlanner,
    outline_entries,
    plot_pages,
)
from parch.calendar import MONTH_NAMES
from parch.fonts.ramp import EffectiveRamp
from parch.plotter import RecordingPlotter
from parch.press import press
from parch.sections.engineering import EngineeringPadSection
from parch.spec import Spec

_OUTLINE_HUBS = frozenset(
    {
        "annual",
        "projects_index",
        "meetings_index",
        "tasks_index",
        "review_index",
        "quarter",
        "month",
    }
)

_EXCLUDED_KINDS = frozenset(
    {
        "cover",
        "weekly",
        "daily",
        "daily_notes",
        "project",
        "meeting",
        "task",
        "review",
        "habits",
        "engineering_front",
        "engineering_back",
        "steno",
        "monthly_tasks",
        "rapid_log",
    }
)


def _outline_titles(reader: PdfReader) -> list[str]:
    titles: list[str] = []
    for item in reader.outline:
        if isinstance(item, Destination):
            titles.append(str(item.title))
    return titles


def test_plot_pages_omits_outline_when_disabled():
    spec = Spec(book="engineering-notebook", engineering_sheets=2)
    plotter = RecordingPlotter()
    EngineeringNotebook().plot(spec, plotter)
    assert plotter.outlines() == []
    assert spec.outline is False


def test_engineering_notebook_outline_empty_when_enabled():
    spec = Spec(book="engineering-notebook", engineering_sheets=2, outline=True)
    plotter = RecordingPlotter()
    EngineeringNotebook().plot(spec, plotter)
    assert plotter.outlines() == []
    dests = plotter.dests()
    assert spec.cover_dest in dests
    assert spec.dest_for_engineering_pad(1, "front") in dests


def test_projects_notebook_outlines_index_not_cover():
    spec = Spec(book="projects-notebook", outline=True)
    plotter = RecordingPlotter()
    ProjectsNotebook().plot(spec, plotter)
    dests = [dest for _title, dest in plotter.outlines()]
    assert spec.cover_dest not in dests
    assert spec.projects_index_dest in dests
    assert dests[0] == spec.projects_index_dest
    assert spec.dest_for_project(1) not in dests


def test_year_planner_outlines_annual_indexes_quarter_month():
    spec = Spec(months=(1,), notes_pages=0, outline=True)
    book = YearPlanner()
    pages = book.pages(spec)
    plotter = RecordingPlotter()
    book.plot(spec, plotter)
    dests = [dest for _title, dest in plotter.outlines()]
    dest_kind = {page.dest: page.kind for page in pages}
    outlined_kinds = {dest_kind[dest] for dest in dests}

    assert dests == snapshot(
        [
            "year-2026",
            "projects-index-2026-01",
            "meetings-index-2026",
            "tasks-index-2026-Q1",
            "review-index-2026",
            "quarter-2026-Q1",
            "month-2026-01",
        ]
    )
    assert plotter.outlines() == outline_entries(pages)
    titles = [title for title, _dest in plotter.outlines()]
    assert titles.count("Tasks Q1 2026") == 1
    assert "Tasks" not in titles
    assert outlined_kinds == _OUTLINE_HUBS
    assert outlined_kinds.isdisjoint(_EXCLUDED_KINDS)
    assert spec.cover_dest not in dests
    assert spec.dest_for_habits(1) not in dests
    assert spec.dest_for_project(1) not in dests
    assert spec.dest_for_meeting(1) not in dests
    monday = date(2026, 1, 5)
    assert spec.dest_for_task(monday) not in dests
    assert spec.dest_for_review(monday) not in dests
    assert spec.dest_for_week(monday) not in dests
    assert spec.dest_for_day(monday) not in dests
    assert spec.dest_for_notes(monday, 1) not in dests


def test_year_planner_full_year_outline_once_indexes_each_quarter_month():
    spec = Spec(notes_pages=0, outline=True)
    pages = YearPlanner().pages(spec)
    entries = outline_entries(pages)
    titles = [title for title, _dest in entries]
    dests = [dest for _title, dest in entries]
    dest_kind = {page.dest: page.kind for page in pages}
    outlined_kinds = {dest_kind[dest] for dest in dests}
    month_titles = [f"{name} {spec.year}" for name in MONTH_NAMES]
    quarter_titles = [f"Q{quarter} {spec.year}" for quarter in range(1, 5)]
    tasks_titles = [f"Tasks Q{quarter} {spec.year}" for quarter in range(1, 5)]
    pressed_tasks = [page for page in pages if page.kind == "tasks_index"]

    assert titles == snapshot(
        [
            "2026",
            "Projects",
            "Meetings",
            "Tasks Q1 2026",
            "Tasks Q2 2026",
            "Tasks Q3 2026",
            "Tasks Q4 2026",
            "Review",
            "Q1 2026",
            "Q2 2026",
            "Q3 2026",
            "Q4 2026",
            "January 2026",
            "February 2026",
            "March 2026",
            "April 2026",
            "May 2026",
            "June 2026",
            "July 2026",
            "August 2026",
            "September 2026",
            "October 2026",
            "November 2026",
            "December 2026",
        ]
    )
    assert [title for title, dest in entries if dest_kind[dest] == "tasks_index"] == [
        page.title for page in pressed_tasks
    ]
    assert len(pressed_tasks) == 4
    assert len(set(tasks_titles)) == 4
    assert "Tasks" not in titles
    assert [title for title in titles if title.startswith("Q")] == quarter_titles
    assert [title for title in titles if title in set(month_titles)] == month_titles
    assert outlined_kinds == _OUTLINE_HUBS
    assert outlined_kinds.isdisjoint(_EXCLUDED_KINDS)
    assert spec.cover_dest not in dests
    assert spec.tasks_index_dest in dests
    assert spec.dest_for_quarter(1) in dests
    for quarter in range(1, 5):
        assert spec.dest_for_tasks_index(quarter) in dests
        assert spec.dest_for_quarter(quarter) in dests
    for month in spec.months:
        assert spec.dest_for_month(month) in dests
        assert spec.dest_for_habits(month) not in dests
    monday = date(2026, 1, 5)
    assert spec.dest_for_project(1) not in dests
    assert spec.dest_for_meeting(1) not in dests
    assert spec.dest_for_task(monday) not in dests
    assert spec.dest_for_review(monday) not in dests
    assert spec.dest_for_week(monday) not in dests
    assert spec.dest_for_day(monday) not in dests
    assert spec.dest_for_notes(monday, 1) not in dests


def test_pad_only_plot_pages_outline_empty_for_eng_kinds():
    spec = Spec(engineering_sheets=1, outline=True)
    plotter = RecordingPlotter()
    plot_pages(
        EngineeringPadSection(spec).pages,
        plotter,
        ramp=EffectiveRamp(),
        device=spec.device,
        outline=spec.outline,
    )
    assert plotter.outlines() == []
    assert spec.dest_for_engineering_pad(1, "front") in plotter.dests()
    assert spec.cover_dest not in plotter.dests()


def test_press_pdf_year_planner_outline_when_enabled(tmp_path: Path):
    spec = Spec(months=(1,), notes_pages=0, outline=True)
    out = tmp_path / "year-planner-outline.pdf"
    press(spec, out)
    reader = PdfReader(out)
    titles = _outline_titles(reader)
    assert titles == snapshot(
        [
            "2026",
            "Projects",
            "Meetings",
            "Tasks Q1 2026",
            "Review",
            "Q1 2026",
            "January 2026",
        ]
    )
    assert all(title.lower() != "cover" for title in titles)
    first = next(item for item in reader.outline if isinstance(item, Destination))
    assert reader.get_destination_page_number(first) == 1
    dests = {str(key).lstrip("/") for key in (reader.named_destinations or {})}
    assert spec.year_dest in dests
    assert spec.cover_dest in dests


def test_press_pdf_engineering_outline_empty_when_enabled(tmp_path: Path):
    spec = Spec(book="engineering-notebook", engineering_sheets=2, outline=True)
    out = tmp_path / "eng-outline.pdf"
    press(spec, out)
    reader = PdfReader(out)
    assert reader.outline == []
    dests = {str(key).lstrip("/") for key in (reader.named_destinations or {})}
    assert spec.dest_for_engineering_pad(1, "front") in dests
    assert spec.cover_dest in dests


def test_press_pdf_outline_absent_when_disabled(tmp_path: Path):
    spec = Spec(book="engineering-notebook", engineering_sheets=1)
    out = tmp_path / "eng-plain.pdf"
    press(spec, out)
    assert PdfReader(out).outline == []


def test_example_engineering_toml_enables_outline():
    spec = Spec.from_path(Path("examples/engineering.toml"))
    assert spec.outline is True
    assert spec.book == "engineering-notebook"


def test_bullet_journal_january_outline_hubs():
    spec = Spec(
        book="bullet-journal",
        months=(1,),
        bujo_index_pages=1,
        bujo_collections=2,
        outline=True,
    )
    pages = BulletJournal().pages(spec)
    entries = outline_entries(pages)
    dests = [dest for _title, dest in entries]
    dest_kind = {page.dest: page.kind for page in pages}
    assert [dest_kind[dest] for dest in dests] == snapshot(
        ["bujo_key", "bujo_index", "future_log", "monthly_log", "collection"]
    )
    assert dests == snapshot(
        [
            "bujo-key-2026",
            "bujo-index-2026-01",
            "bujo-future-2026-01",
            "month-2026-01",
            "bujo-col-2026-01",
        ]
    )
    assert spec.cover_dest not in dests
    assert spec.dest_for_habits(1) not in dests
    assert spec.dest_for_month_tasks(1) not in dests
    assert spec.dest_for_day(date(2026, 1, 1)) not in dests
    assert spec.dest_for_bujo_collection(2) not in dests


def test_example_nomad_toml_enables_outline():
    spec = Spec.from_path(Path("examples/nomad.toml"))
    assert spec.outline is True
    assert spec.book == "year-planner"
    assert spec.months == tuple(range(1, 13))

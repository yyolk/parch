from datetime import date
from pathlib import Path

from pypdf import PdfReader
from pypdf.generic import Destination

from parch.books import EngineeringNotebook, ProjectsNotebook, YearPlanner, plot_pages
from parch.fonts.ramp import EffectiveRamp
from parch.plotter import RecordingPlotter
from parch.press import press
from parch.sections.engineering import EngineeringPadSection
from parch.spec import Spec

_OUTLINE_KINDS = frozenset(
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

    assert dests == [
        spec.year_dest,
        spec.projects_index_dest,
        spec.meetings_index_dest,
        spec.tasks_index_dest,
        spec.review_index_dest,
        spec.quarter_dest,
        spec.month_dest,
    ]
    assert outlined_kinds == _OUTLINE_KINDS
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
    out = tmp_path / "nomad-outline.pdf"
    press(spec, out)
    reader = PdfReader(out)
    titles = _outline_titles(reader)
    assert titles == [
        "2026",
        "Projects",
        "Meetings",
        "Tasks",
        "Review",
        "Q1 2026",
        "January 2026",
    ]
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


def test_example_nomad_outline_toml_enables_january_outline():
    spec = Spec.from_path(Path("examples/nomad-outline.toml"))
    assert spec.outline is True
    assert spec.book == "year-planner"
    assert spec.months == (1,)
    assert Spec.from_path(Path("examples/nomad.toml")).outline is False

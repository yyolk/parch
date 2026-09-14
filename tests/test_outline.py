from pathlib import Path

from pypdf import PdfReader

from parch.books import (
    EngineeringNotebook,
    ProjectsNotebook,
    YearPlanner,
    plot_pages,
    section_outline_entries,
)
from parch.fonts.ramp import EffectiveRamp
from parch.plotter import RecordingPlotter
from parch.press import press
from parch.sections.engineering import EngineeringPadSection
from parch.sections.page import Page, PageKind
from parch.sections.steno import StenoPadSection
from parch.spec import Spec


def _page(kind: PageKind, dest: str, title: str = "") -> Page:
    return Page(dest=dest, kind=kind, title=title, nav=(), components=())


def _outline_titles(reader: PdfReader) -> list[str]:
    titles: list[str] = []
    for item in reader.outline or []:
        title = getattr(item, "title", None)
        if title is not None:
            titles.append(str(title))
    return titles


def test_section_outline_entries_skips_cover_and_emits_kind_runs():
    ledger = [
        _page("cover", "cover", "2026"),
        _page("annual", "year-2026", "2026"),
        _page("projects_index", "projects-index-1", "Projects"),
        _page("projects_index", "projects-index-2", "Projects"),
        _page("project", "projects-1", "Projects"),
        _page("project", "projects-2", "Projects"),
        _page("month", "month-01", "January 2026"),
        _page("habits", "month-01-habits", "Habits · January 2026"),
        _page("month", "month-02", "February 2026"),
    ]
    assert section_outline_entries(ledger) == [
        ("Year", "year-2026"),
        ("Projects", "projects-index-1"),
        ("Project", "projects-1"),
        ("January 2026", "month-01"),
        ("Habits · January 2026", "month-01-habits"),
        ("February 2026", "month-02"),
    ]


def test_section_outline_entries_empty_and_cover_only():
    assert section_outline_entries([]) == []
    assert section_outline_entries([_page("cover", "cover", "2026")]) == []


def test_section_outline_entries_year_planner_section_starts():
    spec = Spec(months=(1,), notes_pages=0)
    entries = section_outline_entries(YearPlanner().pages(spec))
    dests = [dest for _, dest in entries]
    assert spec.cover_dest not in dests
    assert entries[0] == ("Year", spec.year_dest)
    assert entries[1] == ("Projects", spec.projects_index_dest)
    assert entries[2] == ("Project", spec.dest_for_project(1))
    assert ("Meetings", spec.meetings_index_dest) in entries
    assert ("Meeting", spec.dest_for_meeting(1)) in entries
    assert ("Tasks", spec.tasks_index_dest) in entries
    assert ("Review", spec.review_index_dest) in entries
    assert ("Q1 2026", spec.dest_for_quarter(1)) in entries
    assert ("January 2026", spec.dest_for_month(1)) in entries
    assert ("Habits · January 2026", spec.dest_for_habits(1)) in entries
    assert any(title.startswith("Week ") for title, _ in entries)
    assert any(title == "Daily" for title, _ in entries)
    assert all(title != "Notes" for title, _ in entries)


def test_section_outline_entries_projects_and_engineering_books():
    projects = section_outline_entries(
        ProjectsNotebook().pages(Spec(book="projects-notebook"))
    )
    assert projects[0] == ("Projects", Spec().projects_index_dest)
    assert projects[1][0] == "Project"
    assert all(title != "Cover" for title, _ in projects)

    eng_spec = Spec(book="engineering-notebook", engineering_sheets=2)
    eng = section_outline_entries(EngineeringNotebook().pages(eng_spec))
    assert eng == [
        ("Engineering", eng_spec.dest_for_engineering_pad(1, "front")),
        ("Computation", eng_spec.dest_for_engineering_pad(1, "back")),
        ("Engineering", eng_spec.dest_for_engineering_pad(2, "front")),
        ("Computation", eng_spec.dest_for_engineering_pad(2, "back")),
    ]


def test_section_outline_entries_pad_only_paths():
    pad_spec = Spec(engineering_sheets=2)
    assert section_outline_entries(EngineeringPadSection(pad_spec).pages()) == [
        ("Engineering", pad_spec.dest_for_engineering_pad(1, "front")),
        ("Computation", pad_spec.dest_for_engineering_pad(1, "back")),
        ("Engineering", pad_spec.dest_for_engineering_pad(2, "front")),
        ("Computation", pad_spec.dest_for_engineering_pad(2, "back")),
    ]
    steno_spec = Spec(steno_sheets=3)
    assert section_outline_entries(StenoPadSection(steno_spec).pages()) == [
        ("Steno", steno_spec.dest_for_steno_pad(1)),
    ]


def test_plot_pages_registers_outline_after_add_dest():
    spec = Spec(engineering_sheets=1, outline=True)
    plotter = RecordingPlotter()
    plot_pages(
        EngineeringPadSection(spec).pages,
        plotter,
        ramp=EffectiveRamp(),
        device=spec.device,
        outline=True,
    )
    names = [op[0] for op in plotter.ops]
    first_begin = names.index("begin_page")
    assert names[:first_begin] == ["reserve_dest", "reserve_dest"]
    assert plotter.outlines() == [
        ("Engineering", spec.dest_for_engineering_pad(1, "front")),
        ("Computation", spec.dest_for_engineering_pad(1, "back")),
    ]
    dest_ops = [i for i, name in enumerate(names) if name == "add_dest"]
    outline_ops = [i for i, name in enumerate(names) if name == "add_outline"]
    assert dest_ops[0] < outline_ops[0] < dest_ops[1] < outline_ops[1]


def test_plot_pages_skips_outline_when_flag_off():
    spec = Spec(engineering_sheets=1)
    plotter = RecordingPlotter()
    plot_pages(
        EngineeringPadSection(spec).pages,
        plotter,
        ramp=EffectiveRamp(),
        device=spec.device,
    )
    assert plotter.outlines() == []


def test_press_outline_example_has_bookmarks_not_extra_pages(tmp_path: Path):
    spec = Spec.from_path(Path("examples/outline.toml"))
    assert spec.outline is True
    expected = section_outline_entries(YearPlanner().pages(spec))
    out = tmp_path / "outline.pdf"
    press(spec, out)
    reader = PdfReader(out)
    assert _outline_titles(reader) == [title for title, _ in expected]
    assert spec.cover_dest not in {title.lower() for title in _outline_titles(reader)}
    dests = {str(key).lstrip("/") for key in (reader.named_destinations or {})}
    assert spec.year_dest in dests
    assert spec.cover_dest in dests
    off = tmp_path / "off.pdf"
    press(Spec.from_mapping({"months": [1], "daily": {"notes_pages": 0}}), off)
    assert len(reader.pages) == len(PdfReader(off).pages)
    assert _outline_titles(PdfReader(off)) == []


def test_press_pad_outline(tmp_path: Path):
    spec = Spec(engineering_sheets=1, outline=True)
    out = tmp_path / "pad.pdf"
    press(spec, out)
    assert _outline_titles(PdfReader(out)) == ["Engineering", "Computation"]
    steno = Spec(steno_sheets=2, outline=True)
    press(steno, tmp_path / "steno.pdf")
    assert _outline_titles(PdfReader(tmp_path / "steno.pdf")) == ["Steno"]

from pathlib import Path

from pypdf import PdfReader

from parch.books import EngineeringNotebook, ProjectsNotebook, YearPlanner
from parch.calendar import months_touching_weeks
from parch.plotter import RecordingPlotter
from parch.press import press
from parch.sections.cover import CoverSection
from parch.sections.engineering import EngineeringPadSection
from parch.sections.month import MonthSection
from parch.sections.steno import StenoPadSection
from parch.spec import Spec


def _outline_titles(reader: PdfReader) -> list[str]:
    return [item.title for item in reader.outline]


def _named_dest_page(reader: PdfReader, name: str) -> int:
    for key, dest in (reader.named_destinations or {}).items():
        if str(key).lstrip("/") == name:
            return reader.get_destination_page_number(dest)
    raise AssertionError(f"missing named dest {name!r}")


def _year_outline_pairs(spec: Spec) -> list[tuple[str, str]]:
    first_week = months_touching_weeks(spec.year, spec.months, spec.weekday_start)[0]
    first_day = next(day for day in first_week if spec.presses_day(day))
    return [
        ("Year", spec.year_dest),
        ("Projects", spec.projects_index_dest),
        ("Meetings", spec.meetings_index_dest),
        ("Tasks", spec.tasks_index_dest),
        ("Review", spec.review_index_dest),
        ("Quarters", spec.dest_for_quarter(spec.pressed_quarters()[0])),
        ("Months", spec.dest_for_month(spec.month)),
        ("Habits", spec.dest_for_habits(spec.month)),
        ("Weeks", spec.dest_for_week(first_week[0])),
        ("Days", spec.dest_for_day(first_day)),
        ("Notes", spec.dest_for_notes(first_day, 1)),
    ]


def test_cover_skips_and_pad_stamps_first_dest():
    cover = CoverSection(Spec(outline=True))
    assert cover.outline_title is None
    assert all(page.outline_title is None for page in cover.pages())

    pad = EngineeringPadSection(Spec(engineering_sheets=2, outline=True))
    assert pad.outline_title == "Engineering"
    pages = pad.pages()
    assert pages[0].outline_title == "Engineering"
    assert pages[0].dest == "engineering-2026-01-front"
    assert all(page.outline_title is None for page in pages[1:])

    off = EngineeringPadSection(Spec(engineering_sheets=1)).pages()
    assert all(page.outline_title is None for page in off)


def test_pages_for_stamps_once_per_section():
    spec = Spec(months=(1, 2), outline=True)
    month = MonthSection(spec)
    january = month.pages_for(1)
    february = month.pages_for(2)
    assert january[0].outline_title == "Months"
    assert january[0].dest == spec.dest_for_month(1)
    assert february[0].outline_title is None


def test_year_planner_stamps_first_page_dest_of_each_section():
    spec = Spec(months=(1,), notes_pages=1, outline=True)
    pages = YearPlanner().pages(spec)
    assert pages[0].kind == "cover"
    assert pages[0].outline_title is None
    assert [
        (page.outline_title, page.dest) for page in pages if page.outline_title
    ] == _year_outline_pairs(spec)


def test_plot_pages_records_outline_without_painter_ops():
    spec = Spec(engineering_sheets=1, outline=True)
    plotter = RecordingPlotter()
    EngineeringNotebook().plot(spec, plotter)
    assert plotter.outlines() == [
        ("Engineering", spec.dest_for_engineering_pad(1, "front"))
    ]
    assert plotter.outlines()[0][1] in plotter.dests()
    assert "cover" in plotter.dests()


def test_sibling_books_skip_cover():
    projects = Spec(book="projects-notebook", outline=True)
    pages = ProjectsNotebook().pages(projects)
    assert pages[0].kind == "cover"
    assert pages[0].outline_title is None
    assert pages[1].outline_title == "Projects"
    assert pages[1].dest == projects.projects_index_dest


def test_press_outline_binds_titles_to_named_dest_pages(tmp_path: Path):
    spec = Spec.from_path(Path("examples/nomad-outline.toml"))
    out = tmp_path / "nomad-outline.pdf"
    press(spec, out)
    reader = PdfReader(out)
    pairs = _year_outline_pairs(spec)
    assert _outline_titles(reader) == [title for title, _ in pairs]
    assert "Cover" not in _outline_titles(reader)
    assert "Contents" not in _outline_titles(reader)
    for item, (title, dest) in zip(reader.outline, pairs, strict=True):
        assert item.title == title
        assert reader.get_destination_page_number(item) == _named_dest_page(
            reader, dest
        )


def test_press_pad_only_outline_and_off(tmp_path: Path):
    on = tmp_path / "pad-on.pdf"
    press(Spec.from_path(Path("examples/engineering-pad.toml")), on)
    reader = PdfReader(on)
    assert _outline_titles(reader) == ["Engineering"]
    dest = Spec(engineering_sheets=1).dest_for_engineering_pad(1, "front")
    assert reader.get_destination_page_number(reader.outline[0]) == _named_dest_page(
        reader, dest
    )
    assert len(reader.pages) == 2

    off = tmp_path / "pad-off.pdf"
    press(Spec(engineering_sheets=1, outline=False), off)
    assert PdfReader(off).outline == []
    assert len(PdfReader(off).pages) == 2

    steno = tmp_path / "steno.pdf"
    press(Spec(steno_sheets=1, outline=True), steno)
    steno_reader = PdfReader(steno)
    assert _outline_titles(steno_reader) == ["Steno"]
    assert StenoPadSection(Spec(steno_sheets=1)).outline_title == "Steno"

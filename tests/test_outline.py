"""Reader outline (bookmarks) — Plotter.outline, no printed TOC page."""

from pathlib import Path

from pypdf import PdfReader

from parch.books import (
    EngineeringNotebook,
    ProjectsNotebook,
    YearPlanner,
    plot_pages,
)
from parch.fonts.ramp import EffectiveRamp
from parch.plotter import RecordingPlotter
from parch.press import press
from parch.sections import outline_starts
from parch.sections.engineering import EngineeringPadSection
from parch.sections.steno import StenoPadSection
from parch.spec import Spec


def _outline_titles(reader: PdfReader) -> list[str]:
    titles: list[str] = []
    for item in reader.outline:
        if isinstance(item, list):
            continue
        titles.append(item.title)
    return titles


def _outline_pages(reader: PdfReader) -> list[int]:
    pages: list[int] = []
    for item in reader.outline:
        if isinstance(item, list):
            continue
        page = reader.get_destination_page_number(item)
        assert page is not None
        pages.append(page)
    return pages


def test_outline_default_off_records_nothing():
    plotter = RecordingPlotter()
    YearPlanner().plot(Spec(months=(1,), notes_pages=0), plotter)
    assert plotter.outlines() == []


def test_year_planner_outline_skips_cover():
    spec = Spec(months=(1,), notes_pages=1, outline=True)
    pages = YearPlanner().pages(spec)
    starts = outline_starts(pages)
    assert pages[0].kind == "cover"
    assert starts[0].kind == "annual"
    assert all(page.kind != "cover" for page in starts)
    first: dict[str, str] = {}
    for page in pages:
        first.setdefault(page.kind, page.dest)
    assert [page.dest for page in starts] == [
        spec.year_dest,
        spec.projects_index_dest,
        spec.meetings_index_dest,
        spec.tasks_index_dest,
        spec.review_index_dest,
        spec.dest_for_quarter(1),
        spec.dest_for_month(1),
        spec.dest_for_habits(1),
        first["weekly"],
        first["daily"],
        first["daily_notes"],
    ]

    plotter = RecordingPlotter()
    YearPlanner().plot(spec, plotter)
    outlines = plotter.outlines()
    assert [dest for _, dest, _ in outlines] == [page.dest for page in starts]
    assert all(level == 0 for _, _, level in outlines)
    assert "cover" not in {dest for _, dest, _ in outlines}


def test_projects_notebook_outline_is_projects_only():
    spec = Spec(book="projects-notebook", outline=True)
    plotter = RecordingPlotter()
    ProjectsNotebook().plot(spec, plotter)
    assert plotter.outlines() == [("Projects", spec.projects_index_dest, 0)]


def test_engineering_notebook_outline_skips_cover():
    spec = Spec(book="engineering-notebook", engineering_sheets=2, outline=True)
    plotter = RecordingPlotter()
    EngineeringNotebook().plot(spec, plotter)
    assert plotter.outlines() == [
        ("Engineering", spec.dest_for_engineering_pad(1, "front"), 0)
    ]


def test_pad_only_plot_pages_emits_section_start():
    spec = Spec(engineering_sheets=1, outline=True)
    plotter = RecordingPlotter()
    plot_pages(
        EngineeringPadSection(spec).pages,
        plotter,
        ramp=EffectiveRamp(),
        device=spec.device,
        outline=spec.outline,
    )
    assert plotter.outlines() == [
        ("Engineering", spec.dest_for_engineering_pad(1, "front"), 0)
    ]
    assert "cover" not in plotter.dests()

    steno = Spec(steno_sheets=2, outline=True)
    recorded = RecordingPlotter()
    plot_pages(
        StenoPadSection(steno).pages,
        recorded,
        ramp=EffectiveRamp(),
        device=steno.device,
        outline=steno.outline,
    )
    assert recorded.outlines() == [("Steno", steno.dest_for_steno_pad(1), 0)]


def test_press_reader_outline_has_sections_not_cover(tmp_path: Path):
    year = Spec(months=(1,), notes_pages=0, outline=True)
    out = tmp_path / "year.pdf"
    press(year, out)
    reader = PdfReader(out)
    titles = _outline_titles(reader)
    pages = _outline_pages(reader)
    assert titles
    assert "Cover" not in titles
    assert pages[0] == 1  # annual, not cover at 0
    dests = {str(key).lstrip("/") for key in (reader.named_destinations or {})}
    assert "cover" in dests
    assert "year-2026" in dests

    projects = Spec.from_path(Path("examples/projects.toml"))
    proj_out = tmp_path / "projects.pdf"
    press(projects, proj_out)
    proj = PdfReader(proj_out)
    assert _outline_titles(proj) == ["Projects"]
    assert _outline_pages(proj) == [1]

    eng = Spec(book="engineering-notebook", engineering_sheets=1, outline=True)
    eng_out = tmp_path / "eng.pdf"
    press(eng, eng_out)
    eng_reader = PdfReader(eng_out)
    assert _outline_titles(eng_reader) == ["Engineering"]
    assert _outline_pages(eng_reader) == [1]

    pad = Spec.from_path(Path("examples/engineering-pad.toml"))
    pad_out = tmp_path / "pad.pdf"
    press(pad, pad_out)
    pad_reader = PdfReader(pad_out)
    assert _outline_titles(pad_reader) == ["Engineering"]
    assert _outline_pages(pad_reader) == [0]

    steno = Spec.from_path(Path("examples/steno-pad.toml"))
    steno_out = tmp_path / "steno.pdf"
    press(steno, steno_out)
    assert _outline_titles(PdfReader(steno_out)) == ["Steno"]

    off = Spec(months=(1,), notes_pages=0, outline=False)
    off_out = tmp_path / "off.pdf"
    press(off, off_out)
    assert _outline_titles(PdfReader(off_out)) == []

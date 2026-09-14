from pathlib import Path
from typing import get_protocol_members

import pytest
from pypdf import PdfReader

from parch import ConfigError
from parch.books import (
    Book,
    EngineeringNotebook,
    OutlineEntry,
    ProjectsNotebook,
    YearPlanner,
    outline_for,
    outline_from_pages,
    plot_pages,
)
from parch.fonts.ramp import EffectiveRamp
from parch.plotter import RecordingPlotter
from parch.press import press
from parch.sections.engineering import EngineeringPadSection
from parch.sections.page import Page
from parch.spec import Spec


def _outline_titles(reader: PdfReader) -> list[str]:
    titles: list[str] = []
    for item in reader.outline:
        if isinstance(item, list):
            continue
        titles.append(item.title)
    return titles


def _outline_pages(reader: PdfReader) -> list[tuple[str, int]]:
    items: list[tuple[str, int]] = []
    for item in reader.outline:
        if isinstance(item, list):
            continue
        items.append((item.title, reader.get_destination_page_number(item)))
    return items


def test_book_protocol_stays_pages_and_plot():
    members = get_protocol_members(Book)
    assert members == {"pages", "plot"}
    assert not getattr(Book, "_is_runtime_protocol", False)


def test_outline_from_pages_skips_cover_and_leaves():
    spec = Spec(months=(1,), notes_pages=0)
    pages = YearPlanner().pages(spec)
    assert pages[0].kind == "cover"
    entries = outline_from_pages(pages)
    assert [entry.title for entry in entries] == [
        "Annual",
        "Projects",
        "Meetings",
        "Tasks",
        "Review",
        "Quarters",
        "Months",
        "Weeks",
        "Days",
    ]
    assert all(entry.level == 0 for entry in entries)
    assert "cover" not in {entry.dest for entry in entries}
    assert entries[0].dest == spec.year_dest
    assert entries[1].dest == spec.projects_index_dest


def test_year_planner_outline_entries_are_section_hubs():
    spec = Spec(months=(1,), notes_pages=0, outline=True)
    book = YearPlanner()
    entries = book.outline_entries(spec)
    assert entries == list(outline_from_pages(book.pages(spec)))
    assert outline_for(book, spec) == tuple(entries)
    assert outline_for(book, Spec(months=(1,), notes_pages=0)) == ()


def test_projects_and_engineering_outline_entries():
    projects = Spec(book="projects-notebook", outline=True)
    assert ProjectsNotebook().outline_entries(projects) == [
        OutlineEntry("Projects", projects.projects_index_dest)
    ]
    engineering = Spec(
        book="engineering-notebook", engineering_sheets=2, outline=True
    )
    assert EngineeringNotebook().outline_entries(engineering) == [
        OutlineEntry("Engineering", engineering.dest_for_engineering_pad(1, "front"))
    ]


def test_outline_for_falls_back_to_pages_without_method():
    spec = Spec(engineering_sheets=1, outline=True)
    ledger = EngineeringPadSection(spec).pages()

    class _Pad:
        def pages(self, given: Spec) -> list[Page]:
            assert given is spec
            return ledger

    assert outline_for(_Pad(), spec) == tuple(outline_from_pages(ledger))
    assert [entry.title for entry in outline_from_pages(ledger)] == ["Engineering"]


def test_plot_records_outlines_after_dests():
    spec = Spec(book="projects-notebook", outline=True)
    plotter = RecordingPlotter()
    ProjectsNotebook().plot(spec, plotter)
    assert plotter.outlines() == [("Projects", spec.projects_index_dest, 0)]
    dest_ops = [op for op in plotter.ops if op[0] == "reserve_dest"]
    outline_ops = [op for op in plotter.ops if op[0] == "add_outline"]
    assert dest_ops
    assert dest_ops[-1][1] == spec.dest_for_project(spec.project_count)
    assert outline_ops[0][2] == spec.projects_index_dest
    add_idx = next(
        i
        for i, op in enumerate(plotter.ops)
        if op[0] == "add_dest" and op[1] == spec.projects_index_dest
    )
    outline_idx = next(i for i, op in enumerate(plotter.ops) if op[0] == "add_outline")
    assert dest_ops[0][1] == "cover"
    assert add_idx < outline_idx


def test_plot_skips_outline_when_spec_off():
    plotter = RecordingPlotter()
    ProjectsNotebook().plot(Spec(book="projects-notebook"), plotter)
    assert plotter.outlines() == []


def test_plot_pages_true_derives_hubs_without_book():
    spec = Spec(engineering_sheets=1, outline=True)
    plotter = RecordingPlotter()
    plot_pages(
        EngineeringPadSection(spec).pages,
        plotter,
        ramp=EffectiveRamp(),
        device=spec.device,
        outline=True,
    )
    assert plotter.outlines() == [
        ("Engineering", spec.dest_for_engineering_pad(1, "front"), 0)
    ]


def test_plot_pages_rejects_missing_dest():
    spec = Spec(engineering_sheets=1)
    with pytest.raises(ConfigError, match="outline dest 'missing'"):
        plot_pages(
            EngineeringPadSection(spec).pages,
            RecordingPlotter(),
            ramp=EffectiveRamp(),
            device=spec.device,
            outline=[OutlineEntry("Ghost", "missing")],
        )


def test_press_projects_toml_outline_has_no_printed_toc(tmp_path: Path):
    spec = Spec.from_path(Path("examples/projects.toml"))
    assert spec.outline is True
    out = tmp_path / "projects.pdf"
    press(spec, out)
    reader = PdfReader(out)
    expected_pages = 1 + spec.project_index_pages + spec.project_count
    assert len(reader.pages) == expected_pages
    assert _outline_titles(reader) == ["Projects"]
    assert _outline_pages(reader) == [("Projects", 1)]
    dests = {str(key).lstrip("/") for key in (reader.named_destinations or {})}
    assert spec.projects_index_dest in dests
    assert "cover" in dests


def test_press_outline_off_writes_no_bookmarks(tmp_path: Path):
    spec = Spec(book="projects-notebook", outline=False)
    out = tmp_path / "plain.pdf"
    press(spec, out)
    reader = PdfReader(out)
    assert _outline_titles(reader) == []
    assert len(reader.pages) == 1 + spec.project_index_pages + spec.project_count


def test_press_year_planner_outline_matches_hubs(tmp_path: Path):
    spec = Spec(months=(1,), notes_pages=0, outline=True)
    off = Spec(months=(1,), notes_pages=0)
    outlined = tmp_path / "year-outline.pdf"
    plain = tmp_path / "year-plain.pdf"
    press(spec, outlined)
    press(off, plain)
    reader = PdfReader(outlined)
    assert len(reader.pages) == len(PdfReader(plain).pages)
    assert _outline_titles(reader) == [
        "Annual",
        "Projects",
        "Meetings",
        "Tasks",
        "Review",
        "Quarters",
        "Months",
        "Weeks",
        "Days",
    ]
    dests = [page.dest for page in YearPlanner().pages(spec)]
    expected = [
        (entry.title, dests.index(entry.dest))
        for entry in YearPlanner().outline_entries(spec)
    ]
    assert _outline_pages(reader) == expected
    assert "Cover" not in _outline_titles(reader)


def test_press_engineering_notebook_outline(tmp_path: Path):
    spec = Spec(book="engineering-notebook", engineering_sheets=2, outline=True)
    out = tmp_path / "eng.pdf"
    press(spec, out)
    reader = PdfReader(out)
    assert len(reader.pages) == 1 + 2 * spec.engineering_sheets
    assert _outline_titles(reader) == ["Engineering"]
    assert _outline_pages(reader) == [("Engineering", 1)]


def test_press_pad_only_outline_from_pages(tmp_path: Path):
    spec = Spec(engineering_sheets=1, outline=True)
    out = tmp_path / "pad.pdf"
    press(spec, out)
    reader = PdfReader(out)
    assert len(reader.pages) == 2
    assert _outline_titles(reader) == ["Engineering"]
    assert _outline_pages(reader) == [("Engineering", 0)]

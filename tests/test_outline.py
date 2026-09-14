from pathlib import Path

from pypdf import PdfReader
from pypdf.generic import Destination

from parch.books import EngineeringNotebook, ProjectsNotebook, YearPlanner, plot_pages
from parch.fonts.ramp import EffectiveRamp
from parch.plotter import RecordingPlotter
from parch.press import press
from parch.sections.engineering import EngineeringPadSection
from parch.spec import Spec


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


def test_engineering_notebook_outlines_section_starts_not_cover():
    spec = Spec(book="engineering-notebook", engineering_sheets=2, outline=True)
    plotter = RecordingPlotter()
    EngineeringNotebook().plot(spec, plotter)
    dests = [dest for _title, dest in plotter.outlines()]
    assert spec.cover_dest not in dests
    assert spec.dest_for_engineering_pad(1, "front") in dests
    assert spec.dest_for_engineering_pad(1, "back") in dests
    assert dests[0] == spec.dest_for_engineering_pad(1, "front")


def test_projects_notebook_outlines_index_not_cover():
    spec = Spec(book="projects-notebook", outline=True)
    plotter = RecordingPlotter()
    ProjectsNotebook().plot(spec, plotter)
    dests = [dest for _title, dest in plotter.outlines()]
    assert spec.cover_dest not in dests
    assert spec.projects_index_dest in dests
    assert dests[0] == spec.projects_index_dest


def test_year_planner_outlines_first_annual_and_projects_index():
    spec = Spec(months=(1,), notes_pages=0, outline=True)
    plotter = RecordingPlotter()
    YearPlanner().plot(spec, plotter)
    dests = [dest for _title, dest in plotter.outlines()]
    assert spec.cover_dest not in dests
    assert spec.year_dest in dests
    assert spec.projects_index_dest in dests
    assert dests[0] == spec.year_dest


def test_pad_only_plot_pages_honors_outline():
    spec = Spec(engineering_sheets=1, outline=True)
    plotter = RecordingPlotter()
    plot_pages(
        EngineeringPadSection(spec).pages,
        plotter,
        ramp=EffectiveRamp(),
        device=spec.device,
        outline=spec.outline,
    )
    dests = [dest for _title, dest in plotter.outlines()]
    assert spec.dest_for_engineering_pad(1, "front") in dests
    assert spec.cover_dest not in dests


def test_press_pdf_outline_when_enabled(tmp_path: Path):
    spec = Spec(book="engineering-notebook", engineering_sheets=2, outline=True)
    out = tmp_path / "eng-outline.pdf"
    press(spec, out)
    reader = PdfReader(out)
    titles = _outline_titles(reader)
    assert titles
    assert all(title.lower() != "cover" for title in titles)
    first = next(item for item in reader.outline if isinstance(item, Destination))
    assert reader.get_destination_page_number(first) == 1
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

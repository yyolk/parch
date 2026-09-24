from pathlib import Path

from parch.books import (
    BulletJournal,
    DotGridNotebook,
    EngineeringNotebook,
    LinedDotGridNotebook,
    LinedNotebook,
    PerspectiveNotebook,
    ProjectsNotebook,
)
from parch.components import CoverTitle
from parch.devices import NOMAD
from parch.layouts.planner.layout import PlannerLayout
from parch.plotter import RecordingPlotter
from parch.sections.cover import CoverSection
from parch.spec import Spec


def _paint_texts(page) -> list[object]:
    plotter = RecordingPlotter()
    PlannerLayout().paint(page, plotter, NOMAD)
    return [op[2] for op in plotter.ops if op[0] == "text"]


def _cover_page(pages: list) -> tuple[object, CoverTitle]:
    page = pages[0]
    cover = page.components[0]
    assert isinstance(cover, CoverTitle)
    return page, cover


def test_year_planner_omitted_title_keeps_year_book_brow():
    spec = Spec()
    assert spec.title is None
    page, cover = _cover_page(CoverSection(spec).pages())
    assert cover.display_title is None
    assert cover.eyebrow == "Year Book"
    texts = _paint_texts(page)
    assert "Year Book" in texts
    assert "Year planner" not in texts


def test_year_planner_title_is_brow():
    spec = Spec(title="Year planner")
    page, cover = _cover_page(CoverSection(spec).pages())
    assert cover.display_title is None
    assert cover.eyebrow == "Year planner"
    texts = _paint_texts(page)
    assert "Year planner" in texts
    assert "Year Book" not in texts


def test_nomad_toml_title_is_brow():
    spec = Spec.from_path(Path("examples/nomad.toml"))
    page, cover = _cover_page(CoverSection(spec).pages())
    assert cover.display_title is None
    assert cover.eyebrow == "Year planner"
    texts = _paint_texts(page)
    assert "Year planner" in texts
    assert "Year Book" not in texts


def test_projects_omitted_title_keeps_projects_headline():
    spec = Spec(book="projects-notebook")
    page, cover = _cover_page(ProjectsNotebook().pages(spec))
    assert cover.display_title == "Projects"
    texts = _paint_texts(page)
    assert "Projects" in texts
    assert "Year Book" not in texts


def test_projects_title_is_headline():
    spec = Spec(book="projects-notebook", title="Studio")
    page, cover = _cover_page(ProjectsNotebook().pages(spec))
    assert cover.display_title == "Studio"
    texts = _paint_texts(page)
    assert "Studio" in texts
    assert "Projects" not in texts
    assert "Year Book" not in texts


def test_engineering_omitted_title_keeps_engineering_headline():
    spec = Spec(book="engineering-notebook", engineering_sheets=1)
    page, cover = _cover_page(EngineeringNotebook().pages(spec))
    assert cover.display_title == "Engineering"
    texts = _paint_texts(page)
    assert "Engineering" in texts
    assert "Year Book" not in texts


def test_dotgrid_omitted_title_keeps_dotgrid_headline():
    spec = Spec(book="dotgrid-notebook", dotgrid_sheets=1)
    page, cover = _cover_page(DotGridNotebook().pages(spec))
    assert cover.display_title == "Dot grid"
    texts = _paint_texts(page)
    assert "Dot grid" in texts
    assert "Year Book" not in texts


def test_dotgrid_title_is_headline():
    spec = Spec(book="dotgrid-notebook", dotgrid_sheets=1, title="Dots")
    page, cover = _cover_page(DotGridNotebook().pages(spec))
    assert cover.display_title == "Dots"
    texts = _paint_texts(page)
    assert "Dots" in texts
    assert "Dot grid" not in texts
    assert "Year Book" not in texts


def test_lined_omitted_title_keeps_lined_headline():
    spec = Spec(book="lined-notebook", lined_sheets=1)
    page, cover = _cover_page(LinedNotebook().pages(spec))
    assert cover.display_title == "Lined"
    texts = _paint_texts(page)
    assert "Lined" in texts
    assert "Year Book" not in texts


def test_perspective_omitted_title_keeps_perspective_headline():
    spec = Spec(book="perspective-notebook", perspective_sheets=1)
    page, cover = _cover_page(PerspectiveNotebook().pages(spec))
    assert cover.display_title == "Perspective"
    texts = _paint_texts(page)
    assert "Perspective" in texts
    assert "Year Book" not in texts


def test_perspective_title_is_headline():
    spec = Spec(book="perspective-notebook", perspective_sheets=1, title="Guide")
    page, cover = _cover_page(PerspectiveNotebook().pages(spec))
    assert cover.display_title == "Guide"
    texts = _paint_texts(page)
    assert "Guide" in texts
    assert "Perspective" not in texts
    assert "Year Book" not in texts


def test_lined_title_is_headline():
    spec = Spec(book="lined-notebook", lined_sheets=1, title="Notes")
    page, cover = _cover_page(LinedNotebook().pages(spec))
    assert cover.display_title == "Notes"
    texts = _paint_texts(page)
    assert "Notes" in texts
    assert "Lined" not in texts
    assert "Year Book" not in texts


def test_lined_dotgrid_omitted_title_keeps_pair_headline():
    spec = Spec(book="lined-dotgrid-mix-notebook", lined_dotgrid_sheets=1)
    page, cover = _cover_page(LinedDotGridNotebook().pages(spec))
    assert cover.display_title == "Lined / Dot grid"
    texts = _paint_texts(page)
    assert "Lined / Dot grid" in texts
    assert "Year Book" not in texts


def test_bullet_journal_omitted_title_keeps_bullet_journal_headline():
    spec = Spec(book="bullet-journal", months=(1,), bujo_collections=0)
    page, cover = _cover_page(BulletJournal().pages(spec))
    assert cover.display_title == "Bullet Journal"
    texts = _paint_texts(page)
    assert "Bullet Journal" in texts
    assert "Year Book" not in texts


def test_bullet_journal_title_is_headline():
    spec = Spec(
        book="bullet-journal",
        months=(1,),
        bujo_collections=0,
        title="Bullet journal",
    )
    page, cover = _cover_page(BulletJournal().pages(spec))
    assert cover.display_title == "Bullet journal"
    texts = _paint_texts(page)
    assert "Bullet journal" in texts
    assert "Bullet Journal" not in texts
    assert "Year Book" not in texts

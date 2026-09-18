from pathlib import Path

from parch.books import BulletJournal, EngineeringNotebook, ProjectsNotebook
from parch.components import CoverTitle
from parch.devices import NOMAD
from parch.layouts.planner.layout import PlannerLayout
from parch.plotter import RecordingPlotter
from parch.sections.cover import CoverSection
from parch.spec import Spec


def _paint_cover(page) -> tuple[list[object], RecordingPlotter]:
    plotter = RecordingPlotter()
    PlannerLayout().paint(page, plotter, NOMAD)
    texts = [op[2] for op in plotter.ops if op[0] == "text"]
    return texts, plotter


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
    texts, plotter = _paint_cover(page)
    assert "Year Book" in texts
    assert "Year planner" not in texts
    year = next(op for op in plotter.ops if op[0] == "text" and op[2] == "2026")
    assert year[3] == 42


def test_year_planner_title_is_brow():
    spec = Spec(title="Year planner")
    page, cover = _cover_page(CoverSection(spec).pages())
    assert cover.display_title is None
    assert cover.eyebrow == "Year planner"
    texts, plotter = _paint_cover(page)
    brow = next(op for op in plotter.ops if op[0] == "text" and op[2] == "Year planner")
    assert brow[3] == 10
    year = next(op for op in plotter.ops if op[0] == "text" and op[2] == "2026")
    assert year[3] == 42
    assert "Year Book" not in texts


def test_nomad_toml_title_is_brow():
    spec = Spec.from_path(Path("examples/nomad.toml"))
    page, cover = _cover_page(CoverSection(spec).pages())
    assert cover.eyebrow == "Year planner"
    texts, _ = _paint_cover(page)
    assert "Year planner" in texts
    assert "Year Book" not in texts


def test_projects_omitted_title_keeps_projects_headline():
    spec = Spec(book="projects-notebook")
    page, cover = _cover_page(ProjectsNotebook().pages(spec))
    assert cover.display_title == "Projects"
    texts, plotter = _paint_cover(page)
    headline = next(op for op in plotter.ops if op[0] == "text" and op[2] == "Projects")
    assert headline[3] == 42
    year = next(op for op in plotter.ops if op[0] == "text" and op[2] == "2026")
    assert year[3] == 10
    assert "Year Book" not in texts


def test_projects_title_is_headline():
    spec = Spec(book="projects-notebook", title="Studio")
    page, cover = _cover_page(ProjectsNotebook().pages(spec))
    assert cover.display_title == "Studio"
    texts, plotter = _paint_cover(page)
    headline = next(op for op in plotter.ops if op[0] == "text" and op[2] == "Studio")
    assert headline[3] == 42
    year = next(op for op in plotter.ops if op[0] == "text" and op[2] == "2026")
    assert year[3] == 10
    assert "Projects" not in texts
    assert "Year Book" not in texts


def test_engineering_omitted_title_keeps_engineering_headline():
    spec = Spec(book="engineering-notebook", engineering_sheets=1)
    page, cover = _cover_page(EngineeringNotebook().pages(spec))
    assert cover.display_title == "Engineering"
    texts, plotter = _paint_cover(page)
    headline = next(
        op for op in plotter.ops if op[0] == "text" and op[2] == "Engineering"
    )
    assert headline[3] == 42
    assert "Year Book" not in texts


def test_bullet_journal_omitted_title_keeps_bullet_journal_headline():
    spec = Spec(book="bullet-journal", months=(1,), bujo_collections=0)
    page, cover = _cover_page(BulletJournal().pages(spec))
    assert cover.display_title == "Bullet Journal"
    texts, plotter = _paint_cover(page)
    headline = next(
        op for op in plotter.ops if op[0] == "text" and op[2] == "Bullet Journal"
    )
    assert headline[3] == 42
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
    texts, plotter = _paint_cover(page)
    headline = next(
        op for op in plotter.ops if op[0] == "text" and op[2] == "Bullet journal"
    )
    assert headline[3] == 42
    assert "Bullet Journal" not in texts
    assert "Year Book" not in texts

from dataclasses import is_dataclass

from parch.books import (
    Book,
    EngineeringNotebook,
    ProjectsNotebook,
    YearPlanner,
    plot_pages,
)
from parch.fonts.ramp import EffectiveRamp
from parch.plotter import RecordingPlotter
from parch.spec import Spec


def test_books_are_dataclasses_that_satisfy_protocol():
    for cls in (YearPlanner, ProjectsNotebook, EngineeringNotebook):
        assert is_dataclass(cls)
        assert Book not in cls.__mro__
        assert isinstance(cls(), Book)


def test_plot_pages_reserves_then_paints():
    spec = Spec(engineering_sheets=1, book="engineering-notebook")
    pages = EngineeringNotebook().pages(spec)
    plotter = RecordingPlotter()
    plot_pages(pages, spec, plotter, ramp=EffectiveRamp())

    reserves = [op[1] for op in plotter.ops if op[0] == "reserve_dest"]
    dests = plotter.dests()
    assert reserves == dests == [page.dest for page in pages]

    first_begin = next(i for i, op in enumerate(plotter.ops) if op[0] == "begin_page")
    assert all(op[0] == "reserve_dest" for op in plotter.ops[:first_begin])
    assert plotter.ops[first_begin] == ("begin_page", 1)
    assert plotter.ops[first_begin + 1] == ("add_dest", "cover", 1)


def test_year_planner_plot_uses_shared_ledger():
    spec = Spec(notes_pages=0, months=(1,))
    book: Book = YearPlanner()
    pages = book.pages(spec)
    plotter = RecordingPlotter()
    book.plot(spec, plotter)
    assert plotter.dests() == [page.dest for page in pages]
    assert [page.kind for page in pages[:3]] == ["cover", "annual", "projects_index"]

from parch import ConfigError
from parch.books.projects import ProjectsNotebook
from parch.books.protocol import Book, plot_book
from parch.books.year_planner import YearPlanner
from parch.fonts.ramp import TypeRamp

__all__ = [
    "BOOK_NAMES",
    "Book",
    "ProjectsNotebook",
    "YearPlanner",
    "book_for",
    "plot_book",
]

BOOK_NAMES = ("year", "projects")


def book_for(name: str, ramp: TypeRamp | None = None) -> Book:
    """Construct a Book by CLI/press name. Unknown names raise ``ConfigError``."""
    match name:
        case "year":
            return YearPlanner(ramp=ramp)
        case "projects":
            return ProjectsNotebook(ramp=ramp)
        case _:
            raise ConfigError(f"unknown book {name!r}")

from parch import ConfigError
from parch.books.engineering_notebook import EngineeringNotebook
from parch.books.outline import OutlineEntry, outline_for, outline_from_pages
from parch.books.projects_notebook import ProjectsNotebook
from parch.books.protocol import Book, plot_pages
from parch.books.year_planner import YearPlanner

__all__ = [
    "Book",
    "EngineeringNotebook",
    "OutlineEntry",
    "ProjectsNotebook",
    "YearPlanner",
    "book_for",
    "outline_for",
    "outline_from_pages",
    "plot_pages",
]


def book_for(name: str) -> type[Book]:
    """Press selection: year-planner, projects-notebook, or engineering-notebook."""
    match name:
        case "year-planner":
            return YearPlanner
        case "projects-notebook":
            return ProjectsNotebook
        case "engineering-notebook":
            return EngineeringNotebook
        case _:
            raise ConfigError(
                "book must be year-planner, projects-notebook, or "
                f"engineering-notebook, not {name!r}"
            )

from parch import ConfigError
from parch.books.engineering_notebook import EngineeringNotebook
from parch.books.projects_notebook import ProjectsNotebook
from parch.books.protocol import Book, outline_entries, plot_pages
from parch.books.year_planner import YearPlanner

__all__ = [
    "Book",
    "EngineeringNotebook",
    "ProjectsNotebook",
    "YearPlanner",
    "book_for",
    "outline_entries",
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

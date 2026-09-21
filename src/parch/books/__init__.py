from parch import ConfigError
from parch.books.bullet_journal import BulletJournal
from parch.books.dot_grid_notebook import DotGridNotebook
from parch.books.engineering_notebook import EngineeringNotebook
from parch.books.lined_notebook import LinedNotebook
from parch.books.projects_notebook import ProjectsNotebook
from parch.books.protocol import Book, outline_entries, plot_pages
from parch.books.year_planner import YearPlanner

__all__ = [
    "Book",
    "BulletJournal",
    "DotGridNotebook",
    "EngineeringNotebook",
    "LinedNotebook",
    "ProjectsNotebook",
    "YearPlanner",
    "book_for",
    "outline_entries",
    "plot_pages",
]


def book_for(name: str) -> type[Book]:
    """Press selection: year-planner, sibling notebooks, or bullet-journal."""
    match name:
        case "year-planner":
            return YearPlanner
        case "projects-notebook":
            return ProjectsNotebook
        case "engineering-notebook":
            return EngineeringNotebook
        case "dot-grid-notebook":
            return DotGridNotebook
        case "lined-notebook":
            return LinedNotebook
        case "bullet-journal":
            return BulletJournal
        case _:
            raise ConfigError(
                "book must be year-planner, projects-notebook, "
                "engineering-notebook, bullet-journal, "
                f"dot-grid-notebook, or lined-notebook, not {name!r}"
            )

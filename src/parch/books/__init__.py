from parch import ConfigError
from parch.books.projects_notebook import ProjectsNotebook
from parch.books.year_planner import YearPlanner

__all__ = ["ProjectsNotebook", "YearPlanner", "book_for"]


def book_for(name: str) -> type[YearPlanner] | type[ProjectsNotebook]:
    """Press selection: ``year-planner`` (default) or ``projects-notebook``."""
    match name:
        case "year-planner":
            return YearPlanner
        case "projects-notebook":
            return ProjectsNotebook
        case _:
            raise ConfigError(
                f"book must be year-planner or projects-notebook, not {name!r}"
            )

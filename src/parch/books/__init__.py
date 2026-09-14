from parch import ConfigError
from parch.books.engineering_pad import EngineeringPad
from parch.books.projects_notebook import ProjectsNotebook
from parch.books.year_planner import YearPlanner

__all__ = ["EngineeringPad", "ProjectsNotebook", "YearPlanner", "book_for"]

type Book = type[YearPlanner] | type[ProjectsNotebook] | type[EngineeringPad]


def book_for(name: str) -> Book:
    """Press selection: year-planner, projects-notebook, or engineering-pad demo."""
    match name:
        case "year-planner":
            return YearPlanner
        case "projects-notebook":
            return ProjectsNotebook
        case "engineering-pad":
            return EngineeringPad
        case _:
            raise ConfigError(
                f"book must be year-planner, projects-notebook, or engineering-pad, not {name!r}"
            )

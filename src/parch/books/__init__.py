from parch import ConfigError
from parch.books.projects_columns import ProjectsColumnsBook
from parch.books.year_planner import YearPlanner
from parch.spec import Spec

type PlannerBook = YearPlanner | ProjectsColumnsBook


def planner_book(spec: Spec) -> PlannerBook:
    """Year walk, or a throwaway one-page experiment."""
    match spec.book:
        case "year":
            return YearPlanner()
        case "projects_columns":
            return ProjectsColumnsBook()
        case _:
            raise ConfigError(f"unknown book {spec.book!r}")


__all__ = ["PlannerBook", "ProjectsColumnsBook", "YearPlanner", "planner_book"]

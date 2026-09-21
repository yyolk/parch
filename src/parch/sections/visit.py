"""Closed visitor over PageKind. ``accept`` is the only kind match."""

from abc import ABC, abstractmethod
from typing import assert_never

from parch.sections.page import Page


class PageVisitor[R](ABC):
    """One abstract ``visit_*`` per PageKind; a new kind is a new method."""

    @abstractmethod
    def visit_cover(self, page: Page) -> R: ...

    @abstractmethod
    def visit_annual(self, page: Page) -> R: ...

    @abstractmethod
    def visit_favorites(self, page: Page) -> R: ...

    @abstractmethod
    def visit_my_100(self, page: Page) -> R: ...

    @abstractmethod
    def visit_checkoff_365(self, page: Page) -> R: ...

    @abstractmethod
    def visit_projects_index(self, page: Page) -> R: ...

    @abstractmethod
    def visit_project(self, page: Page) -> R: ...

    @abstractmethod
    def visit_meetings_index(self, page: Page) -> R: ...

    @abstractmethod
    def visit_meeting(self, page: Page) -> R: ...

    @abstractmethod
    def visit_tasks_index(self, page: Page) -> R: ...

    @abstractmethod
    def visit_task(self, page: Page) -> R: ...

    @abstractmethod
    def visit_review_index(self, page: Page) -> R: ...

    @abstractmethod
    def visit_review(self, page: Page) -> R: ...

    @abstractmethod
    def visit_quarter(self, page: Page) -> R: ...

    @abstractmethod
    def visit_month(self, page: Page) -> R: ...

    @abstractmethod
    def visit_habits(self, page: Page) -> R: ...

    @abstractmethod
    def visit_weekly(self, page: Page) -> R: ...

    @abstractmethod
    def visit_daily(self, page: Page) -> R: ...

    @abstractmethod
    def visit_daily_notes(self, page: Page) -> R: ...

    @abstractmethod
    def visit_engineering_front(self, page: Page) -> R: ...

    @abstractmethod
    def visit_engineering_back(self, page: Page) -> R: ...

    @abstractmethod
    def visit_steno(self, page: Page) -> R: ...

    @abstractmethod
    def visit_dotgrid(self, page: Page) -> R: ...

    @abstractmethod
    def visit_lined(self, page: Page) -> R: ...

    @abstractmethod
    def visit_bujo_key(self, page: Page) -> R: ...

    @abstractmethod
    def visit_bujo_index(self, page: Page) -> R: ...

    @abstractmethod
    def visit_future_log(self, page: Page) -> R: ...

    @abstractmethod
    def visit_monthly_log(self, page: Page) -> R: ...

    @abstractmethod
    def visit_monthly_tasks(self, page: Page) -> R: ...

    @abstractmethod
    def visit_rapid_log(self, page: Page) -> R: ...

    @abstractmethod
    def visit_collection(self, page: Page) -> R: ...


def accept[R](page: Page, visitor: PageVisitor[R]) -> R:
    """Double-dispatch ``page.kind`` onto ``visitor.visit_*``."""
    match page.kind:
        case "cover":
            return visitor.visit_cover(page)
        case "annual":
            return visitor.visit_annual(page)
        case "favorites":
            return visitor.visit_favorites(page)
        case "my_100":
            return visitor.visit_my_100(page)
        case "checkoff_365":
            return visitor.visit_checkoff_365(page)
        case "projects_index":
            return visitor.visit_projects_index(page)
        case "project":
            return visitor.visit_project(page)
        case "meetings_index":
            return visitor.visit_meetings_index(page)
        case "meeting":
            return visitor.visit_meeting(page)
        case "tasks_index":
            return visitor.visit_tasks_index(page)
        case "task":
            return visitor.visit_task(page)
        case "review_index":
            return visitor.visit_review_index(page)
        case "review":
            return visitor.visit_review(page)
        case "quarter":
            return visitor.visit_quarter(page)
        case "month":
            return visitor.visit_month(page)
        case "habits":
            return visitor.visit_habits(page)
        case "weekly":
            return visitor.visit_weekly(page)
        case "daily":
            return visitor.visit_daily(page)
        case "daily_notes":
            return visitor.visit_daily_notes(page)
        case "engineering_front":
            return visitor.visit_engineering_front(page)
        case "engineering_back":
            return visitor.visit_engineering_back(page)
        case "steno":
            return visitor.visit_steno(page)
        case "dotgrid":
            return visitor.visit_dotgrid(page)
        case "lined":
            return visitor.visit_lined(page)
        case "bujo_key":
            return visitor.visit_bujo_key(page)
        case "bujo_index":
            return visitor.visit_bujo_index(page)
        case "future_log":
            return visitor.visit_future_log(page)
        case "monthly_log":
            return visitor.visit_monthly_log(page)
        case "monthly_tasks":
            return visitor.visit_monthly_tasks(page)
        case "rapid_log":
            return visitor.visit_rapid_log(page)
        case "collection":
            return visitor.visit_collection(page)
        case _:
            assert_never(page.kind)

"""Component lookup for family dispatch."""

from collections.abc import Sequence
from typing import Protocol


class NavLike(Protocol):
    """Strip entry. Families only read ``dest``."""

    @property
    def dest(self) -> str: ...


class PageLike(Protocol):
    """Fields a family reads off a page."""

    @property
    def dest(self) -> str: ...

    @property
    def kind(self) -> str: ...

    @property
    def title(self) -> str: ...

    @property
    def nav(self) -> Sequence[NavLike]: ...

    @property
    def components(self) -> Sequence[object]: ...


def one[T](page: PageLike, typ: type[T]) -> T:
    """First component of ``typ`` on the page."""
    for item in page.components:
        if isinstance(item, typ):
            return item
    raise TypeError(f"{page.kind} page missing {typ.__name__}")

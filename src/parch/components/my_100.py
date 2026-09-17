"""My 100 list page — data only. Painters seat the well."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class My100Page:
    """One ``paint_my_100`` well — numbered write-ins for a slice of 1–100."""

    year: int
    dest: str
    page: int
    pages: int
    numbers: tuple[int, ...]
    index_dest: str

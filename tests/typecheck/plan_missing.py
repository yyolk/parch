"""Witness: a PageKind match that drops lined is not exhaustive. Not a sample."""

from typing import assert_never

from parch.sections.page import PageKind


def incomplete(kind: PageKind) -> None:
    match kind:
        case "cover":
            return None
        case _:
            assert_never(kind)

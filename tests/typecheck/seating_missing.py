"""Witness: a Seating match that only arms cover is not exhaustive. Not a sample."""

from typing import assert_never

from parch.components import CoverTitle
from parch.sections.seating import Seating


def incomplete(components: Seating) -> None:
    match components:
        case (CoverTitle(),):
            return None
        case _:
            assert_never(components)

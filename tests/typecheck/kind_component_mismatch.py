"""Witness: kind=\"cover\" does not accept a steno pad. Not a sample."""

from parch.components import StenoPad
from parch.sections.page import Page


def mismatch() -> Page:
    return Page(
        dest="cover",
        kind="cover",
        title="2026",
        nav=(),
        components=(StenoPad(sheet=1, sheets=1),),
    )

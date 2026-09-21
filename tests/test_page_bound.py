"""PK13: a stated kind accepts only its seating, at the type and at runtime."""

import re
from pathlib import Path
from typing import cast, get_args

import pytest

from parch.components import Component, EngineeringPad, StenoPad
from parch.sections.page import Page, PageKind, check_seating


def test_overloads_list_every_kind_in_order() -> None:
    text = Path("src/parch/sections/page.py").read_text()
    found = re.findall(r'kind: Literal\["([a-z0-9_]+)"\]', text)
    assert found == list(get_args(PageKind.__value__))


def test_cover_rejects_a_steno_pad() -> None:
    bad = cast(tuple[Component, ...], (StenoPad(sheet=1, sheets=1),))
    with pytest.raises(TypeError):
        Page(
            dest="cover",
            kind="cover",
            title="2026",
            nav=(),
            components=bad,  # type: ignore[arg-type]
        )


def test_engineering_front_rejects_the_back_face() -> None:
    with pytest.raises(TypeError):
        check_seating(
            "engineering_front",
            (EngineeringPad(face="back", sheet=1, sheets=1),),
        )


def test_steno_rejects_two_pads() -> None:
    pad = StenoPad(sheet=1, sheets=1)
    with pytest.raises(TypeError):
        check_seating("steno", (pad, pad))

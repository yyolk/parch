"""PK5: PageKind is ChromeKind | pad; pad faces are a closed PadComponent union."""

from types import UnionType
from typing import Literal, Union, get_args, get_origin

from parch.components import DotGridPad, EngineeringPad, PadComponent, StenoPad
from parch.dotgrid import dotgrid_pages
from parch.layouts.planner import PlannerLayout
from parch.plotter import RecordingPlotter
from parch.sections.engineering import EngineeringPadSection
from parch.sections.page import ChromeKind, Page, PageKind
from parch.sections.steno import StenoPadSection
from parch.spec import Spec

_GROWN_PAD_STRINGS = frozenset(
    {"engineering_front", "engineering_back", "steno", "dotgrid"}
)


def _closed_strings(alias: object) -> frozenset[str]:
    value = getattr(alias, "__value__", alias)
    origin = get_origin(value)
    args = get_args(value)
    if origin is Literal:
        return frozenset(arg for arg in args if isinstance(arg, str))
    if origin in (Union, UnionType):
        out: set[str] = set()
        for arg in args:
            out |= _closed_strings(arg)
        return frozenset(out)
    raise TypeError(f"not a closed string union: {alias!r}")


def _closed_types(alias: object) -> frozenset[type]:
    value = getattr(alias, "__value__", alias)
    origin = get_origin(value)
    args = get_args(value)
    if origin in (Union, UnionType):
        return frozenset(args)
    raise TypeError(f"not a closed type union: {alias!r}")


def test_pagekind_is_chrome_plus_single_pad():
    chrome = _closed_strings(ChromeKind)
    kinds = _closed_strings(PageKind)
    assert kinds == chrome | {"pad"}
    assert kinds.isdisjoint(_GROWN_PAD_STRINGS)
    assert "pad" not in chrome
    assert "cover" in chrome
    assert "rapid_log" in chrome


def test_pad_component_is_closed_union():
    assert _closed_types(PadComponent) == {EngineeringPad, StenoPad, DotGridPad}


def test_emitters_use_pad_kind_not_face_strings():
    spec = Spec(engineering_sheets=1, steno_sheets=1, dotgrid_sheets=1)
    pages = [
        *EngineeringPadSection(spec).pages(),
        *StenoPadSection(spec).pages(),
        *dotgrid_pages(spec),
    ]
    assert [page.kind for page in pages] == ["pad"] * 4
    faces = [page.components[0] for page in pages]
    assert [type(face) for face in faces] == [
        EngineeringPad,
        EngineeringPad,
        StenoPad,
        DotGridPad,
    ]
    assert faces[0].face == "front"
    assert faces[1].face == "back"


def test_layout_pad_match_is_component_type():
    spec = Spec(engineering_sheets=1, steno_sheets=1, dotgrid_sheets=1)
    pages = [
        *EngineeringPadSection(spec).pages(),
        *StenoPadSection(spec).pages(),
        *dotgrid_pages(spec),
    ]
    from parch.devices.registry import NOMAD

    for page in pages:
        ink = RecordingPlotter()
        PlannerLayout().paint(page, ink, NOMAD)
        assert ink.ops


def test_layout_chrome_well_rejects_unknown_kind():
    from parch.devices.registry import NOMAD

    page = Page(dest="x", kind="annual", title="Year", nav=(), components=())
    object.__setattr__(page, "kind", "not_a_kind")
    ink = RecordingPlotter()
    try:
        PlannerLayout().paint(page, ink, NOMAD)
    except ValueError, AssertionError, TypeError:
        return
    raise AssertionError("unknown chrome kind must fail closed")

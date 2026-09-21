"""PK8 slice: kind tag plus a per-kind payload, not a Component tuple."""

from datetime import date

import pytest

from parch.calendar import month_touching_weeks
from parch.dotgrid import dotgrid_pages
from parch.sections.annual import AnnualSection
from parch.sections.cover import CoverSection
from parch.sections.month import MonthSection
from parch.sections.steno import StenoPadSection
from parch.sections.sumpage import (
    AnnualPage,
    ChromeSeat,
    CoverPage,
    CoverSeat,
    DotgridPage,
    MonthPage,
    PadSeat,
    SumPage,
    WeeklyPage,
    lift,
    pad_sheets,
    planner_title,
    seat,
)
from parch.sections.weekly import WeeklySection
from parch.spec import Spec


def _week_page(spec: Spec):
    week = month_touching_weeks(spec.year, spec.month, spec.weekday_start)[1]
    return WeeklySection(spec).pages_for(list(week))[0]


def test_closed_set_is_the_variant_union():
    variants = set(SumPage.__value__.__args__)
    assert variants == {CoverPage, AnnualPage, MonthPage, WeeklyPage, DotgridPage}
    import parch.sections.sumpage as sumpage

    assert not hasattr(sumpage, "PageKind")


def test_cover_payload_has_no_chrome_frame():
    page = lift(CoverSection(Spec()).pages()[0])
    assert isinstance(page, CoverPage)
    assert page.kind == "cover"
    assert page.payload.year == 2026
    assert page.payload.cta_dest == "year-2026"
    assert not hasattr(page.payload, "chrome")
    assert not hasattr(page, "components")
    seated = seat(page)
    assert isinstance(seated, CoverSeat)
    assert seated == CoverSeat("cover", 2026, "year-2026")


def test_planner_kinds_share_a_chrome_payload():
    spec = Spec()
    annual = lift(AnnualSection(spec).pages()[0])
    month = lift(MonthSection(spec).pages()[0])
    weekly = lift(_week_page(spec))
    assert isinstance(annual, AnnualPage)
    assert isinstance(month, MonthPage)
    assert isinstance(weekly, WeeklyPage)
    assert planner_title(annual) == "2026"
    assert planner_title(month) == "January 2026"
    assert planner_title(weekly) == "Week 02"
    assert annual.payload.well.quarter_dest == spec.quarter_dest
    assert month.payload.well.month == 1
    assert weekly.payload.well.monday == date(2026, 1, 5)
    assert weekly.payload.well.sunday == date(2026, 1, 11)
    annual_seat = seat(annual)
    month_seat = seat(month)
    weekly_seat = seat(weekly)
    assert isinstance(annual_seat, ChromeSeat)
    assert isinstance(month_seat, ChromeSeat)
    assert isinstance(weekly_seat, ChromeSeat)
    assert [annual_seat.mark, month_seat.mark, weekly_seat.mark] == [
        "Year 2026",
        "Mon 1",
        "Week 02",
    ]
    assert annual_seat.nav > 0
    assert month_seat.nav > 0
    assert weekly_seat.nav > 0


def test_dotgrid_payload_is_the_pad_family():
    page = lift(dotgrid_pages(Spec(dotgrid_sheets=3))[1])
    assert isinstance(page, DotgridPage)
    assert page.kind == "dotgrid"
    assert pad_sheets(page) == 3
    assert page.payload.sheet == 2
    assert not hasattr(page.payload, "chrome")
    assert not hasattr(page, "components")
    assert seat(page) == PadSeat(page.dest, 2, 3)


def test_lift_rejects_kinds_outside_the_slice():
    page = StenoPadSection(Spec(steno_sheets=1)).pages()[0]
    with pytest.raises(ValueError, match="does not include steno"):
        lift(page)

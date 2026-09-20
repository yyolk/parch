from datetime import time

import pytest
from tomlrange import Clock

from parch.layouts.planner.hour_shade import painted_hour_bound, shade_painted_hour


def test_omit_work_hours_never_shades():
    assert shade_painted_hour(9, None) is False
    assert shade_painted_hour(7, None) is False


def test_painted_hour_bound_is_closed_clock_hh00_hh59():
    band = painted_hour_bound(9)
    assert band.domain is Clock.domain
    assert band.as_tuple() == (time(9, 0), time(9, 59))
    assert time(9, 0) in band
    assert time(9, 59) in band
    assert time(10, 0) not in band


def test_shade_uses_bound_overlap_not_floor_ceil_labels():
    work = Clock.parse({"from": time(9, 30), "to": time(11, 30)})
    assert shade_painted_hour(8, work) is False
    assert shade_painted_hour(9, work) is True
    assert shade_painted_hour(10, work) is True
    assert shade_painted_hour(11, work) is True
    # 11:30 intersects 11:00–11:59, not the 12:00 label that floor/ceil would add.
    assert shade_painted_hour(12, work) is False


def test_shade_shared_endpoint_on_hour_start():
    work = Clock.parse({"from": time(9, 0), "to": time(17, 0)})
    assert shade_painted_hour(9, work) is True
    assert shade_painted_hour(16, work) is True
    assert shade_painted_hour(17, work) is True
    assert shade_painted_hour(8, work) is False
    assert shade_painted_hour(18, work) is False


def test_shade_disjoint_from_painted_band():
    early = Clock.parse({"from": time(6, 0), "to": time(6, 59)})
    late = Clock.parse({"from": time(17, 1), "to": time(18, 0)})
    assert shade_painted_hour(7, early) is False
    assert shade_painted_hour(16, late) is False


def test_shade_singleton_tick_hits_its_row():
    noon = Clock.parse({"from": time(12, 0), "to": time(12, 0)})
    assert shade_painted_hour(12, noon) is True
    assert shade_painted_hour(11, noon) is False


def test_painted_hour_bound_rejects_out_of_range():
    with pytest.raises(ValueError, match="hour out of range"):
        painted_hour_bound(24)
    with pytest.raises(ValueError, match="hour out of range"):
        painted_hour_bound(-1)

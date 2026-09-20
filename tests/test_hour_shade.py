from datetime import time

from tomlrange import Clock

from parch.layouts.planner.hour_shade import shade_painted_hour


def test_omit_work_hours_never_shades():
    assert shade_painted_hour(9, None) is False


def test_shade_overlaps_hour_band_not_next_label():
    work = Clock.parse({"from": time(9, 30), "to": time(11, 30)})
    assert shade_painted_hour(8, work) is False
    assert shade_painted_hour(9, work) is True
    assert shade_painted_hour(11, work) is True
    assert shade_painted_hour(12, work) is False

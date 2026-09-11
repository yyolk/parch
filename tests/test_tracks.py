import pytest

from parch.geom import Rect
from parch.tracks import columns, rows


def test_columns_equal_fill_parent():
    parent = Rect(10, 20, 70, 15)
    tracks = columns(parent, 7)
    assert len(tracks) == 7
    assert tracks[0].x == pytest.approx(parent.x)
    assert tracks[-1].right == pytest.approx(parent.right)
    assert all(t.y == parent.y and t.h == parent.h for t in tracks)
    assert all(t.w == pytest.approx(10) for t in tracks)


def test_columns_gap_and_weights():
    parent = Rect(0, 0, 22, 8)
    tracks = columns(parent, 2, gap=2)
    assert tracks[0].w == pytest.approx(10)
    assert tracks[1].x == pytest.approx(12)
    assert tracks[1].right == pytest.approx(22)

    weighted = columns(Rect(0, 0, 40, 5), 3, weights=(1, 2, 1))
    assert [t.w for t in weighted] == [pytest.approx(10), pytest.approx(20), pytest.approx(10)]
    assert sum(t.w for t in weighted) == pytest.approx(40)


def test_rows_equal_gap_and_weights():
    parent = Rect(2, 4, 9, 30)
    bands = rows(parent, 3)
    assert len(bands) == 3
    assert bands[0].y == pytest.approx(parent.y)
    assert bands[-1].bottom == pytest.approx(parent.bottom)
    assert all(b.x == parent.x and b.w == parent.w for b in bands)
    assert all(b.h == pytest.approx(10) for b in bands)

    gapped = rows(Rect(0, 0, 4, 22), 2, gap=2)
    assert gapped[0].h == pytest.approx(10)
    assert gapped[1].y == pytest.approx(12)

    weighted = rows(Rect(0, 0, 4, 40), 3, weights=(1, 2, 1))
    assert [b.h for b in weighted] == [pytest.approx(10), pytest.approx(20), pytest.approx(10)]
    assert sum(b.h for b in weighted) == pytest.approx(40)


def test_tracks_reject_bad_args():
    parent = Rect(0, 0, 10, 10)
    with pytest.raises(ValueError, match="n must"):
        columns(parent, 0)
    with pytest.raises(ValueError, match="weights length"):
        rows(parent, 2, weights=(1,))
    with pytest.raises(ValueError, match="sum"):
        columns(parent, 2, weights=(0, 0))
    with pytest.raises(ValueError, match="gap"):
        rows(parent, 2, gap=-1)

from parch.spec import Spec


def test_dest_names_from_tstrings():
    spec = Spec()
    assert spec.cover_dest == "cover"
    assert spec.month_dest == "month-2026-01"
    assert spec.day_dest == "2026-01-05"
    assert spec.notes_dest(1) == "2026-01-05-notes-1"
    assert spec.notes_dest(2) == "2026-01-05-notes-2"


def test_value_bags_are_slotted():
    spec = Spec()
    assert not hasattr(spec, "__dict__")

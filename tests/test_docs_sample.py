from pathlib import Path

from parch.spec import Spec

SAMPLE = Path(__file__).resolve().parents[1] / "docs" / "downloads" / "nomad.toml"


def test_docs_handwritten_sample_parses():
    spec = Spec.from_path(SAMPLE)
    assert spec.year == 2026
    assert spec.device == "supernote-nomad"
    assert spec.book == "year-planner"
    assert spec.title == "Year planner"
    assert spec.months == tuple(range(1, 13))
    assert spec.outline is True

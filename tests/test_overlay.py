"""Thesis S — overlay schema + invariants. Validator is pure (no I/O)."""

from pathlib import Path

import pytest

from parch import ConfigError
from parch.devices import (
    NOMAD,
    NOMAD_CHROME_SIZE,
    NOMAD_CHROME_WEIGHT,
    NOMAD_COVER_BROW_SIZE,
    NOMAD_TYPE_OVERLAY,
)
from parch.fonts import (
    OVERLAY_SCHEMA_VERSION,
    BadWeight,
    EffectiveRamp,
    JostRamp,
    NonpositiveSize,
    OverlayOk,
    SizeOutOfRange,
    TypeInk,
    TypeOverlay,
    TypePatch,
    UnknownStep,
    VersionMismatch,
    bind_ramp,
    compose_overlays,
    jost_defaults,
    require_overlay,
    validate_overlay,
)
from parch.plotter import RecordingPlotter
from parch.press import press
from parch.spec import Spec


def _nomad_like_mapping() -> dict[str, object]:
    return {
        "schema_version": OVERLAY_SCHEMA_VERSION,
        "chrome": {"size": NOMAD_CHROME_SIZE, "weight": NOMAD_CHROME_WEIGHT},
        "cover_brow": {"size": NOMAD_COVER_BROW_SIZE},
    }


def test_accepts_nomad_like_overlay():
    defaults = jost_defaults()
    typed = NOMAD_TYPE_OVERLAY
    mapping = _nomad_like_mapping()
    for overlay in (typed, mapping):
        result = validate_overlay(overlay, defaults)
        assert isinstance(result, OverlayOk)
        assert result.overlay.schema_version == OVERLAY_SCHEMA_VERSION
        assert result.overlay.chrome is not None
        assert result.overlay.chrome.size == NOMAD_CHROME_SIZE
        assert result.overlay.chrome.weight == NOMAD_CHROME_WEIGHT
        assert result.overlay.cover_brow is not None
        assert result.overlay.cover_brow.size == NOMAD_COVER_BROW_SIZE
        assert result.overlay.cover_year is None
        assert result.overlay.page_title is None
    ramp = EffectiveRamp(overlay=validate_overlay(typed, defaults).overlay)
    assert ramp.ink("chrome") == TypeInk(
        family="jost", weight=NOMAD_CHROME_WEIGHT, size=NOMAD_CHROME_SIZE
    )
    assert ramp.ink("cover_brow") == TypeInk(family="jost", weight="medium", size=NOMAD_COVER_BROW_SIZE)
    assert ramp.ink("cover_year") == JostRamp().ink("cover_year")
    assert ramp.ink("page_title") == JostRamp().ink("page_title")


def test_rejects_unknown_step():
    defaults = jost_defaults()
    result = validate_overlay(
        {"schema_version": OVERLAY_SCHEMA_VERSION, "display": {"size": 20}},
        defaults,
    )
    assert result == UnknownStep(step="display")
    caption = validate_overlay(
        {"schema_version": OVERLAY_SCHEMA_VERSION, "caption": {"weight": "book"}},
        defaults,
    )
    assert isinstance(caption, UnknownStep)
    assert caption.step == "caption"


def test_rejects_bad_weight():
    defaults = jost_defaults()
    result = validate_overlay(
        {"schema_version": OVERLAY_SCHEMA_VERSION, "chrome": {"weight": "hairline"}},
        defaults,
    )
    assert result == BadWeight(weight="hairline", step="chrome")
    black = validate_overlay(
        {"schema_version": OVERLAY_SCHEMA_VERSION, "page_title": {"weight": "black"}},
        defaults,
    )
    assert isinstance(black, BadWeight)
    assert black.weight == "black"


def test_rejects_nonpositive_size():
    defaults = jost_defaults()
    zero = validate_overlay(
        {"schema_version": OVERLAY_SCHEMA_VERSION, "chrome": {"size": 0}},
        defaults,
    )
    assert zero == NonpositiveSize(size=0.0, step="chrome")
    negative = validate_overlay(
        TypeOverlay(schema_version=OVERLAY_SCHEMA_VERSION, chrome=TypePatch(size=-1.5)),
        defaults,
    )
    assert negative == NonpositiveSize(size=-1.5, step="chrome")


def test_rejects_size_out_of_range():
    defaults = jost_defaults()
    huge_chrome = validate_overlay(
        {"schema_version": OVERLAY_SCHEMA_VERSION, "chrome": {"size": 42}},
        defaults,
    )
    assert isinstance(huge_chrome, SizeOutOfRange)
    assert huge_chrome.step == "chrome"
    tiny_year = validate_overlay(
        {"schema_version": OVERLAY_SCHEMA_VERSION, "cover_year": {"size": 10}},
        defaults,
    )
    assert isinstance(tiny_year, SizeOutOfRange)
    assert tiny_year.step == "cover_year"


def test_version_mismatch_is_exact_match():
    """Policy: exact schema_version match. No older/newer compat yet."""
    defaults = jost_defaults()
    missing = validate_overlay({"chrome": {"size": 8.6}}, defaults)
    assert missing == VersionMismatch(got=None, expected=OVERLAY_SCHEMA_VERSION)
    old = validate_overlay(
        {"schema_version": 0, "chrome": {"size": 8.6}},
        defaults,
    )
    assert old == VersionMismatch(got=0, expected=1)
    new = validate_overlay(
        TypeOverlay(schema_version=2, chrome=TypePatch(size=8.6)),
        defaults,
    )
    assert new == VersionMismatch(got=2, expected=1)
    assert "exact version match" in str(new)


def test_validate_overlay_is_pure():
    defaults = jost_defaults()
    data = _nomad_like_mapping()
    first = validate_overlay(data, defaults)
    second = validate_overlay(data, defaults)
    assert first == second
    assert data == _nomad_like_mapping()
    typed = TypeOverlay(
        schema_version=OVERLAY_SCHEMA_VERSION,
        chrome=TypePatch(size=8.6, weight="medium"),
    )
    assert validate_overlay(typed, defaults) == validate_overlay(typed, defaults)


def test_require_overlay_raises_config_error():
    with pytest.raises(ConfigError, match="unknown step"):
        require_overlay(
            {"schema_version": OVERLAY_SCHEMA_VERSION, "display": {"size": 12}},
            jost_defaults(),
        )


def test_bind_ramp_validates_before_effective_ramp():
    with pytest.raises(ConfigError, match="hairline"):
        bind_ramp(overlay={"schema_version": OVERLAY_SCHEMA_VERSION, "chrome": {"weight": "hairline"}})
    bound = bind_ramp(overlay=NOMAD_TYPE_OVERLAY)
    assert isinstance(bound, EffectiveRamp)
    assert bound.ink("chrome").size == NOMAD_CHROME_SIZE


def test_press_rejects_bad_overlay_before_paint(tmp_path: Path):
    plotter = RecordingPlotter()
    out = tmp_path / "bad.pdf"
    with pytest.raises(ConfigError, match="type overlay"):
        press(
            Spec(months=(1,), notes_pages=0, project_index_pages=1),
            out,
            plotter=plotter,
            overlay={"schema_version": OVERLAY_SCHEMA_VERSION, "chrome": {"weight": "hairline"}},
        )
    assert plotter.ops == []
    assert not out.exists()


def test_press_rejects_version_mismatch_before_paint(tmp_path: Path):
    plotter = RecordingPlotter()
    out = tmp_path / "ver.pdf"
    with pytest.raises(ConfigError, match="schema_version"):
        press(
            Spec(months=(1,), notes_pages=0, project_index_pages=1),
            out,
            plotter=plotter,
            overlay=TypeOverlay(schema_version=99, chrome=TypePatch(size=8.6)),
        )
    assert plotter.ops == []


def test_press_builds_validated_effective_ramp(tmp_path: Path):
    plotter = RecordingPlotter()
    out = tmp_path / "ok.pdf"
    press(Spec(months=(1,), notes_pages=0, project_index_pages=1), out, plotter=plotter)
    assert plotter.ops
    brow = next(op for op in plotter.ops if op[0] == "text" and op[2] == "Year Book")
    assert brow[3] == NOMAD_COVER_BROW_SIZE
    assert brow[9] == "medium"
    chrome = next(op for op in plotter.ops if op[0] == "text" and op[2] == "Q1–Q4")
    assert chrome[3] == NOMAD_CHROME_SIZE
    assert chrome[9] == NOMAD_CHROME_WEIGHT
    merged = compose_overlays(NOMAD.type_overlay, None)
    assert validate_overlay(merged, jost_defaults()) == OverlayOk(overlay=merged)

"""Overlay schema + TOML knobs keyed by closed TypeSteps. Fail press before paint."""

from dataclasses import replace
from pathlib import Path

import pytest

from parch import ConfigError
from parch.devices import NOMAD, NOMAD_TYPE_OVERLAY
from parch.fonts import (
    OVERLAY_SCHEMA_VERSION,
    TYPE_STEPS,
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
from parch.press import merge_press_overlay, press
from parch.spec import Spec


def test_accepts_identity_and_example_overlay():
    defaults = jost_defaults()
    identity = validate_overlay(TypeOverlay(), defaults)
    assert isinstance(identity, OverlayOk)
    assert identity.overlay == TypeOverlay()
    mapping = {
        "schema_version": OVERLAY_SCHEMA_VERSION,
        "chrome": {"size": 9.6, "weight": "bold"},
        "eyebrow": {"size": 13, "weight": "bold"},
    }
    result = validate_overlay(mapping, defaults)
    assert isinstance(result, OverlayOk)
    assert result.overlay.schema_version == OVERLAY_SCHEMA_VERSION
    assert result.overlay.chrome == TypePatch(size=9.6, weight="bold")
    assert result.overlay.eyebrow == TypePatch(size=13, weight="bold")
    assert result.overlay.display is None
    ramp = EffectiveRamp(overlay=result.overlay)
    assert ramp.ink("chrome") == TypeInk(family="jost", weight="bold", size=9.6)
    assert ramp.ink("chrome", "strong") == TypeInk(family="jost", weight="bold", size=9.6)
    assert ramp.ink("eyebrow") == TypeInk(family="jost", weight="bold", size=13)
    assert ramp.ink("display") == JostRamp().ink("display")
    assert ramp.ink("title") == JostRamp().ink("title")


def test_rejects_unknown_step_including_old_roles():
    defaults = jost_defaults()
    result = validate_overlay(
        {"schema_version": OVERLAY_SCHEMA_VERSION, "cover_year": {"size": 48}},
        defaults,
    )
    assert result == UnknownStep(step="cover_year")
    hero = validate_overlay(
        {"schema_version": OVERLAY_SCHEMA_VERSION, "hero": {"weight": "book"}},
        defaults,
    )
    assert isinstance(hero, UnknownStep)
    assert hero.step == "hero"
    page_title = validate_overlay(
        {"schema_version": OVERLAY_SCHEMA_VERSION, "page_title": {"size": 14}},
        defaults,
    )
    assert page_title == UnknownStep(step="page_title")


def test_closed_typesteps_are_known():
    defaults = jost_defaults()
    assert set(defaults) == set(TYPE_STEPS)
    for step in TYPE_STEPS:
        result = validate_overlay(
            {"schema_version": OVERLAY_SCHEMA_VERSION, step: {"weight": "book"}},
            defaults,
        )
        assert isinstance(result, OverlayOk), step


def test_rejects_bad_weight():
    defaults = jost_defaults()
    result = validate_overlay(
        {"schema_version": OVERLAY_SCHEMA_VERSION, "chrome": {"weight": "hairline"}},
        defaults,
    )
    assert result == BadWeight(weight="hairline", step="chrome")
    black = validate_overlay(
        {"schema_version": OVERLAY_SCHEMA_VERSION, "title": {"weight": "black"}},
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
        {"schema_version": OVERLAY_SCHEMA_VERSION, "eyebrow": {"size": -1.5}},
        defaults,
    )
    assert negative == NonpositiveSize(size=-1.5, step="eyebrow")


def test_rejects_size_out_of_range():
    defaults = jost_defaults()
    huge_chrome = validate_overlay(
        {"schema_version": OVERLAY_SCHEMA_VERSION, "chrome": {"size": 42}},
        defaults,
    )
    assert isinstance(huge_chrome, SizeOutOfRange)
    assert huge_chrome.step == "chrome"
    tiny_display = validate_overlay(
        {"schema_version": OVERLAY_SCHEMA_VERSION, "display": {"size": 10}},
        defaults,
    )
    assert isinstance(tiny_display, SizeOutOfRange)
    assert tiny_display.step == "display"
    typed = validate_overlay(TypeOverlay(chrome=TypePatch(size=16.1)), defaults)
    assert isinstance(typed, SizeOutOfRange)


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
    data = {"schema_version": OVERLAY_SCHEMA_VERSION, "chrome": {"size": 8.6}}
    first = validate_overlay(data, defaults)
    second = validate_overlay(data, defaults)
    assert first == second
    assert data == {"schema_version": OVERLAY_SCHEMA_VERSION, "chrome": {"size": 8.6}}
    typed = TypeOverlay(chrome=TypePatch(size=8.6, weight="medium"))
    assert validate_overlay(typed, defaults) == validate_overlay(typed, defaults)


def test_require_overlay_raises_config_error():
    with pytest.raises(ConfigError, match="unknown step"):
        require_overlay(
            {"schema_version": OVERLAY_SCHEMA_VERSION, "cover_year": {"size": 42}},
            jost_defaults(),
        )


def test_bind_ramp_validates_before_effective_ramp():
    with pytest.raises(ConfigError, match="hairline"):
        bind_ramp(
            overlay={"schema_version": OVERLAY_SCHEMA_VERSION, "chrome": {"weight": "hairline"}}
        )
    bound = bind_ramp(overlay=NOMAD_TYPE_OVERLAY)
    assert isinstance(bound, EffectiveRamp)
    assert bound.ink("chrome") == JostRamp().ink("chrome")


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


def test_press_rejects_unknown_step_before_paint(tmp_path: Path):
    plotter = RecordingPlotter()
    out = tmp_path / "step.pdf"
    with pytest.raises(ConfigError, match="unknown step"):
        press(
            Spec(months=(1,), notes_pages=0, project_index_pages=1),
            out,
            plotter=plotter,
            overlay={"schema_version": OVERLAY_SCHEMA_VERSION, "cover_brow": {"size": 13}},
        )
    assert plotter.ops == []


def test_press_rejects_size_out_of_range_before_paint(tmp_path: Path):
    plotter = RecordingPlotter()
    with pytest.raises(ConfigError, match="not in"):
        press(
            Spec(months=(1,), notes_pages=0, project_index_pages=1),
            tmp_path / "size.pdf",
            plotter=plotter,
            overlay={"schema_version": OVERLAY_SCHEMA_VERSION, "chrome": {"size": 42}},
        )
    assert plotter.ops == []


def test_merge_press_overlay_is_device_then_toml_then_kwarg():
    device = replace(
        NOMAD,
        type_overlay=TypeOverlay(chrome=TypePatch(size=8.6, weight="medium")),
    )
    spec = Spec(
        type_overlay=TypeOverlay(chrome=TypePatch(size=9.6), title=TypePatch(size=14)),
    )
    merged = merge_press_overlay(device, spec, TypeOverlay(title=TypePatch(weight="bold")))
    ramp = EffectiveRamp(overlay=merged)
    assert ramp.ink("chrome") == TypeInk(family="jost", weight="medium", size=9.6)
    assert ramp.ink("title") == TypeInk(family="jost", weight="bold", size=14)
    assert ramp.ink("display") == JostRamp().ink("display")


def test_identity_device_and_empty_toml_stay_jost_defaults(tmp_path: Path):
    plotter = RecordingPlotter()
    press(Spec(months=(1,), notes_pages=0, project_index_pages=1), tmp_path / "id.pdf", plotter=plotter)
    assert plotter.ops
    brow = next(op for op in plotter.ops if op[0] == "text" and op[2] == "Year Book")
    assert brow[3] == 10
    assert brow[9] == "medium"
    chrome = next(op for op in plotter.ops if op[0] == "text" and op[2] == "Q1–Q4")
    assert chrome[3] == 7.4
    assert chrome[9] == "book"
    merged = compose_overlays(NOMAD.type_overlay, Spec().type_overlay)
    assert validate_overlay(merged, jost_defaults()) == OverlayOk(overlay=merged)
    assert NOMAD_TYPE_OVERLAY == TypeOverlay()

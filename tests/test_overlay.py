"""Overlay schema + TOML knobs keyed by closed TypeSteps. Fail press before paint."""

from pathlib import Path

import pytest

from parch import ConfigError
from parch.fonts import (
    OVERLAY_SCHEMA_VERSION,
    TYPE_STEPS,
    EffectiveRamp,
    TypeInk,
    TypeOverlay,
    TypePatch,
    bind_ramp,
    require_overlay,
)
from parch.plotter import RecordingPlotter
from parch.press import merge_press_overlay, press
from parch.spec import Spec


def test_accepts_empty_and_example_overlay():
    empty_overlay = require_overlay(TypeOverlay())
    assert empty_overlay == TypeOverlay()
    mapping = {
        "schema_version": OVERLAY_SCHEMA_VERSION,
        "chrome": {"size": 9.6, "weight": "bold"},
        "eyebrow": {"size": 13, "weight": "bold"},
    }
    result = require_overlay(mapping)
    assert result.schema_version == OVERLAY_SCHEMA_VERSION
    assert result.chrome == TypePatch(size=9.6, weight="bold")
    assert result.eyebrow == TypePatch(size=13, weight="bold")
    assert result.display is None
    ramp = EffectiveRamp(overlay=result)
    empty = EffectiveRamp()
    assert ramp.ink("chrome") == TypeInk(family="jost", weight="bold", size=9.6)
    assert ramp.ink("chrome", "strong") == TypeInk(family="jost", weight="bold", size=9.6)
    assert ramp.ink("eyebrow") == TypeInk(family="jost", weight="bold", size=13)
    assert ramp.ink("display") == empty.ink("display")
    assert ramp.ink("title") == empty.ink("title")


def test_rejects_unknown_step_including_old_roles():
    with pytest.raises(ConfigError, match="unknown step 'cover_year'"):
        require_overlay({"schema_version": OVERLAY_SCHEMA_VERSION, "cover_year": {"size": 48}})
    with pytest.raises(ConfigError, match="unknown step 'hero'"):
        require_overlay({"schema_version": OVERLAY_SCHEMA_VERSION, "hero": {"weight": "book"}})
    with pytest.raises(ConfigError, match="unknown step 'page_title'"):
        require_overlay({"schema_version": OVERLAY_SCHEMA_VERSION, "page_title": {"size": 14}})


def test_closed_typesteps_are_known():
    for step in TYPE_STEPS:
        result = require_overlay({"schema_version": OVERLAY_SCHEMA_VERSION, step: {"weight": "book"}})
        assert result.patch(step) == TypePatch(weight="book")


def test_rejects_bad_weight():
    with pytest.raises(ConfigError, match="bad weight 'hairline'"):
        require_overlay(
            {"schema_version": OVERLAY_SCHEMA_VERSION, "chrome": {"weight": "hairline"}}
        )
    with pytest.raises(ConfigError, match="bad weight 'black'"):
        require_overlay({"schema_version": OVERLAY_SCHEMA_VERSION, "title": {"weight": "black"}})


def test_rejects_nonpositive_size():
    with pytest.raises(ConfigError, match="nonpositive size"):
        require_overlay({"schema_version": OVERLAY_SCHEMA_VERSION, "chrome": {"size": 0}})
    with pytest.raises(ConfigError, match="nonpositive size"):
        require_overlay({"schema_version": OVERLAY_SCHEMA_VERSION, "eyebrow": {"size": -1.5}})


def test_rejects_size_out_of_range():
    with pytest.raises(ConfigError, match="not in"):
        require_overlay({"schema_version": OVERLAY_SCHEMA_VERSION, "chrome": {"size": 42}})
    with pytest.raises(ConfigError, match="not in"):
        require_overlay({"schema_version": OVERLAY_SCHEMA_VERSION, "display": {"size": 10}})
    with pytest.raises(ConfigError, match="not in"):
        require_overlay(TypeOverlay(chrome=TypePatch(size=16.1)))
    with pytest.raises(ConfigError, match="not in"):
        require_overlay({"schema_version": OVERLAY_SCHEMA_VERSION, "micro": {"size": 2.0}})


def test_version_mismatch_is_exact_match():
    """Policy: exact schema_version match. No older/newer compat yet."""
    with pytest.raises(ConfigError, match="schema_version"):
        require_overlay({"chrome": {"size": 8.6}})
    with pytest.raises(ConfigError, match="schema_version 0"):
        require_overlay({"schema_version": 0, "chrome": {"size": 8.6}})
    with pytest.raises(ConfigError, match="exact version match"):
        require_overlay(TypeOverlay(schema_version=2, chrome=TypePatch(size=8.6)))


def test_require_overlay_is_pure():
    data = {"schema_version": OVERLAY_SCHEMA_VERSION, "chrome": {"size": 8.6}}
    first = require_overlay(data)
    second = require_overlay(data)
    assert first == second
    assert data == {"schema_version": OVERLAY_SCHEMA_VERSION, "chrome": {"size": 8.6}}
    typed = TypeOverlay(chrome=TypePatch(size=8.6, weight="medium"))
    assert require_overlay(typed) == require_overlay(typed)


def test_require_overlay_raises_config_error():
    with pytest.raises(ConfigError, match="unknown step"):
        require_overlay({"schema_version": OVERLAY_SCHEMA_VERSION, "cover_year": {"size": 42}})


def test_bind_ramp_validates_before_effective_ramp():
    with pytest.raises(ConfigError, match="hairline"):
        bind_ramp(
            overlay={"schema_version": OVERLAY_SCHEMA_VERSION, "chrome": {"weight": "hairline"}}
        )
    bound = bind_ramp()
    assert isinstance(bound, EffectiveRamp)
    assert bound.ink("chrome") == EffectiveRamp().ink("chrome")


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


def test_merge_press_overlay_is_toml_then_proof_then_kwarg():
    spec = Spec(
        type_overlay=TypeOverlay(chrome=TypePatch(size=9.6, weight="medium"), title=TypePatch(size=14)),
    )
    merged = merge_press_overlay(spec, TypeOverlay(title=TypePatch(weight="bold")))
    ramp = EffectiveRamp(overlay=merged)
    empty = EffectiveRamp()
    assert ramp.ink("chrome") == TypeInk(family="jost", weight="medium", size=9.6)
    assert ramp.ink("title") == TypeInk(family="jost", weight="bold", size=14)
    assert ramp.ink("display") == empty.ink("display")
    proofed = merge_press_overlay(spec, proof=True)
    proof_ramp = EffectiveRamp(overlay=proofed)
    assert proof_ramp.ink("chrome") == TypeInk(family="jost", weight="medium", size=9.2)
    assert proof_ramp.ink("title") == TypeInk(family="jost", weight="medium", size=13)
    assert proof_ramp.ink("display") == TypeInk(family="jost", weight="heavy", size=42)


def test_empty_toml_stays_jost_defaults(tmp_path: Path):
    plotter = RecordingPlotter()
    press(Spec(months=(1,), notes_pages=0, project_index_pages=1), tmp_path / "id.pdf", plotter=plotter)
    assert plotter.ops
    brow = next(op for op in plotter.ops if op[0] == "text" and op[2] == "Year Book")
    assert brow[3] == 10
    assert brow[9] == "medium"
    chrome = next(op for op in plotter.ops if op[0] == "text" and op[2] == "Q1–Q4")
    assert chrome[3] == 7.4
    assert chrome[9] == "book"
    assert require_overlay(Spec().type_overlay) == TypeOverlay()

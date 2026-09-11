from dataclasses import replace
from pathlib import Path

import pytest
from parch.components import CoverTitle
from parch.devices import NOMAD, NOMAD_TYPE_OVERLAY
from parch.fonts import (
    DISPLAY_SIZE,
    JOST_RATIOS,
    JOST_SCALE,
    PROOF_CHROME_SIZE,
    PROOF_EYEBROW_SIZE,
    PROOF_PROFILE,
    PROOF_TITLE_SIZE,
    ROOT_BODY,
    TYPE_STEPS,
    EffectiveRamp,
    FontCatalog,
    JostRamp,
    ProofProfile,
    TypeEmphasis,
    TypeFamily,
    TypeInk,
    TypeOverlay,
    TypePatch,
    TypeRef,
    TypeStep,
    apply_overlay,
    bind_ramp,
    compose_overlays,
    font_dir,
    jost_catalog,
    scale_ink,
    validate_overlay,
)
from parch.geom import Rect
from parch.layouts.planner.painters import paint_cover, paint_header
from parch.plotter import RecordingPlotter
from parch.plotter.fpdf2 import Fpdf2Plotter
from parch.press import _proof_overlay, press
from parch.spec import Spec


def test_jost_weight_files_and_defaults():
    root = font_dir()
    assert (root / "Jost-400-Book.ttf").is_file()
    assert (root / "Jost-500-Medium.ttf").is_file()
    assert (root / "Jost-700-Bold.ttf").is_file()
    assert (root / "Jost-800-Heavy.ttf").is_file()
    assert (root / "LICENSE").is_file()
    assert (root / "AUTHORS").is_file()
    assert not (root / "LiberationSans-Regular.ttf").exists()
    assert not (root / "LiberationSerif-Regular.ttf").exists()
    Fpdf2Plotter(NOMAD)


def test_jost_catalog_is_four_cuts():
    catalog = jost_catalog()
    assert set(catalog.cuts) == {
        ("jost", "book"),
        ("jost", "medium"),
        ("jost", "bold"),
        ("jost", "heavy"),
    }
    assert catalog.register_name("jost", "heavy") == "jost:heavy"
    with pytest.raises(KeyError, match="family='jost' weight='hairline'"):
        catalog.path("jost", "hairline")


def test_jost_scale_table_invariants():
    """Closed ladder: eight used steps, sizes descend, weights stay in catalog."""
    assert TYPE_STEPS == (
        "display",
        "title",
        "eyebrow",
        "body",
        "chrome",
        "label",
        "caption",
        "micro",
    )
    assert set(JOST_SCALE) == set(TYPE_STEPS)
    assert set(JOST_RATIOS) == set(TYPE_STEPS) - {"display"}
    sizes = [JOST_SCALE[step].size for step in TYPE_STEPS]
    assert sizes == sorted(sizes, reverse=True)
    assert len(set(sizes)) == len(sizes)

    catalog = jost_catalog()
    ramp = JostRamp()
    rank = {"book": 0, "medium": 1, "bold": 2, "heavy": 3}
    for step in TYPE_STEPS:
        regular = ramp.ink(step)
        strong = ramp.ink(step, "strong")
        assert regular == ramp.ink(step, emphasis="regular")
        assert regular == scale_ink(step)
        assert regular.family == "jost"
        assert strong.family == "jost"
        assert regular.size == strong.size == JOST_SCALE[step].size
        assert regular.weight == JOST_SCALE[step].regular
        assert strong.weight == JOST_SCALE[step].strong
        catalog.path(regular.family, regular.weight)
        catalog.path(strong.family, strong.weight)
        assert rank[strong.weight] >= rank[regular.weight]

    assert ramp.root_body == ROOT_BODY == 8.5
    assert ramp.ink("display") == TypeInk(family="jost", weight="heavy", size=DISPLAY_SIZE)
    assert ramp.ink("title") == TypeInk(family="jost", weight="medium", size=11)
    assert ramp.ink("title", "strong") == TypeInk(family="jost", weight="bold", size=11)
    assert ramp.ink("eyebrow") == TypeInk(family="jost", weight="medium", size=10)
    assert ramp.ink("body") == TypeInk(family="jost", weight="book", size=8.5)
    assert ramp.ink("chrome") == TypeInk(family="jost", weight="book", size=7.4)
    assert ramp.ink("label") == TypeInk(family="jost", weight="book", size=6.4)
    assert ramp.ink("caption") == TypeInk(family="jost", weight="book", size=5.4)
    assert ramp.ink("micro") == TypeInk(family="jost", weight="book", size=4.3)
    with pytest.raises(KeyError):
        ramp.ink("cover_year")  # type: ignore[arg-type]
    assert set(ramp.catalog.cuts) == set(jost_catalog().cuts)


def _cover() -> CoverTitle:
    return CoverTitle(
        year=2026,
        subtitle="",
        device_name="nomad",
        cta_label="",
        cta_dest="year-2026",
    )


def _family(op: tuple[object, ...]) -> object:
    return op[10]


def test_cover_uses_display_eyebrow_body_steps():
    plotter = RecordingPlotter()
    paint_cover(plotter, NOMAD, _cover(), ramp=JostRamp())
    year = next(op for op in plotter.ops if op[0] == "text" and op[2] == "2026")
    assert year[3] == 42
    assert year[9] == "heavy"
    assert _family(year) == "jost"
    brow = next(op for op in plotter.ops if op[0] == "text" and op[2] == "Year Book")
    assert brow[3] == 10
    assert brow[9] == "medium"
    assert _family(brow) == "jost"
    specs = next(op for op in plotter.ops if op[0] == "text" and "monday weeks" in str(op[2]))
    assert specs[3] == 8.5
    assert specs[9] == "book"
    assert _family(specs) == "jost"


def test_header_uses_title_and_chrome_steps():
    plotter = RecordingPlotter()
    paint_header(
        plotter,
        NOMAD,
        "Year",
        "2026",
        chip="01",
        ramp=JostRamp(),
    )
    title = next(op for op in plotter.ops if op[0] == "text" and op[2] == "Year")
    assert title[3] == 11
    assert title[9] == "medium"
    assert _family(title) == "jost"
    chip = next(op for op in plotter.ops if op[0] == "text" and op[2] == "01")
    assert chip[3] == 7.4
    assert chip[9] == "book"
    assert _family(chip) == "jost"
    meta = next(op for op in plotter.ops if op[0] == "text" and op[2] == "2026")
    assert meta[3] == 7.4
    assert meta[9] == "book"
    assert _family(meta) == "jost"


def test_cover_honors_stub_ramp():
    class StubRamp:
        def __init__(self) -> None:
            self.calls: list[tuple[TypeStep, TypeEmphasis]] = []

        def ink(self, step: TypeStep, emphasis: TypeEmphasis = "regular") -> TypeInk:
            self.calls.append((step, emphasis))
            return TypeInk(family="jost", weight="book", size=12)

    ramp = StubRamp()
    plotter = RecordingPlotter()
    paint_cover(plotter, NOMAD, _cover(), ramp=ramp)
    assert [step for step, _emphasis in ramp.calls] == ["eyebrow", "display", "body"]
    year = next(op for op in plotter.ops if op[0] == "text" and op[2] == "2026")
    assert year[3] == 12
    assert year[9] == "book"
    assert _family(year) == "jost"
    brow = next(op for op in plotter.ops if op[0] == "text" and op[2] == "Year Book")
    assert brow[3] == 12
    assert brow[9] == "book"
    assert _family(brow) == "jost"


def test_header_honors_stub_ramp():
    class StubRamp:
        def __init__(self) -> None:
            self.calls: list[tuple[TypeStep, TypeEmphasis]] = []

        def ink(self, step: TypeStep, emphasis: TypeEmphasis = "regular") -> TypeInk:
            self.calls.append((step, emphasis))
            if step == "title":
                return TypeInk(family="jost", weight="bold", size=9)
            return TypeInk(family="jost", weight="book", size=6)

    ramp = StubRamp()
    plotter = RecordingPlotter()
    paint_header(
        plotter,
        NOMAD,
        "Projects",
        "2026",
        chip="01",
        ramp=ramp,
    )
    assert [step for step, _emphasis in ramp.calls] == ["title", "chrome", "chrome"]
    title = next(op for op in plotter.ops if op[0] == "text" and op[2] == "Projects")
    assert title[3] == 9
    assert title[9] == "bold"
    assert _family(title) == "jost"
    chip = next(op for op in plotter.ops if op[0] == "text" and op[2] == "01")
    assert chip[3] == 6
    assert chip[9] == "book"
    assert _family(chip) == "jost"
    meta = next(op for op in plotter.ops if op[0] == "text" and op[2] == "2026")
    assert meta[3] == 6
    assert meta[9] == "book"
    assert _family(meta) == "jost"


def test_plotter_ink_and_ref_cuts():
    plotter = Fpdf2Plotter(NOMAD)
    plotter.begin_page()
    box = Rect(4, 12, 40, 8)
    plotter.text(box, "body", ref=TypeRef(step="body"))
    assert plotter.pdf.font_family == "jost:book"
    plotter.text(box, "title-strong", ref=TypeRef(step="title", emphasis="strong"))
    assert plotter.pdf.font_family == "jost:bold"
    plotter.text(box, "eyebrow", ref=TypeRef(step="eyebrow"))
    assert plotter.pdf.font_family == "jost:medium"
    plotter.text(box, "ink", ink=TypeInk(family="jost", weight="heavy", size=10))
    assert plotter.pdf.font_family == "jost:heavy"
    plotter.text(box, "smcp", ref=TypeRef(step="label"), small_caps=True)
    assert plotter.pdf.font_family == "jost:book"


def test_fonts_package_does_not_import_plotter():
    import parch.fonts as fonts

    assert "parch.plotter" not in fonts.__dict__
    assert fonts.JostRamp is JostRamp
    assert fonts.TypeInk is TypeInk
    assert fonts.TypeFamily is TypeFamily
    assert fonts.TypeStep is TypeStep
    assert not hasattr(fonts, "FaceBridge")
    assert not hasattr(fonts, "TypeFace")
    assert not hasattr(fonts, "BRIDGE_BACKLOG")
    assert fonts.TypeRef is TypeRef
    assert fonts.jost_catalog is jost_catalog
    assert fonts.FontCatalog is FontCatalog
    assert fonts.EffectiveRamp is EffectiveRamp
    assert fonts.TypeOverlay is TypeOverlay
    assert fonts.TypePatch is TypePatch
    assert fonts.TYPE_STEPS is TYPE_STEPS
    assert fonts.ROOT_BODY is ROOT_BODY
    assert fonts.DISPLAY_SIZE is DISPLAY_SIZE
    assert fonts.JOST_RATIOS is JOST_RATIOS
    assert fonts.validate_overlay is validate_overlay
    assert fonts.ProofProfile is ProofProfile
    assert fonts.PROOF_PROFILE is PROOF_PROFILE


def test_overlay_explicit_size_keeps_default_weight():
    patch = TypePatch(size=9.0)
    base = TypeInk(family="jost", weight="book", size=7.4)
    assert apply_overlay(base, patch) == TypeInk(family="jost", weight="book", size=9.0)
    assert apply_overlay(base, None) == base


def test_overlay_explicit_weight_keeps_default_size():
    patch = TypePatch(weight="bold")
    base = TypeInk(family="jost", weight="book", size=7.4)
    assert apply_overlay(base, patch) == TypeInk(family="jost", weight="bold", size=7.4)


def test_overlay_both_fields_win():
    patch = TypePatch(size=8.6, weight="medium")
    base = TypeInk(family="jost", weight="book", size=7.4)
    assert apply_overlay(base, patch) == TypeInk(family="jost", weight="medium", size=8.6)


def test_overlay_missing_step_keeps_default():
    ramp = EffectiveRamp(overlay=TypeOverlay(chrome=TypePatch(size=9.0)))
    assert ramp.ink("chrome") == TypeInk(family="jost", weight="book", size=9.0)
    assert ramp.ink("chrome", "strong") == TypeInk(family="jost", weight="bold", size=9.0)
    assert ramp.ink("title") == TypeInk(family="jost", weight="medium", size=11)
    assert ramp.ink("display") == TypeInk(family="jost", weight="heavy", size=42)
    assert ramp.ink("eyebrow") == TypeInk(family="jost", weight="medium", size=10)
    assert ramp.ink("body") == TypeInk(family="jost", weight="book", size=8.5)
    assert ramp.ink("label") == TypeInk(family="jost", weight="book", size=6.4)
    assert ramp.ink("caption") == TypeInk(family="jost", weight="book", size=5.4)
    assert ramp.ink("micro") == TypeInk(family="jost", weight="book", size=4.3)


def test_overlay_never_changes_family():
    ramp = EffectiveRamp(overlay=TypeOverlay(chrome=TypePatch(size=9.0, weight="heavy")))
    assert ramp.ink("chrome").family == "jost"
    assert set(ramp.catalog.cuts) == set(jost_catalog().cuts)


def test_compose_overlays_later_explicit_field_wins():
    device = TypeOverlay(chrome=TypePatch(size=8.6, weight="medium"), eyebrow=TypePatch(size=12.0))
    press_over = TypeOverlay(chrome=TypePatch(size=10.0))
    merged = compose_overlays(device, press_over)
    ramp = EffectiveRamp(overlay=merged)
    assert ramp.ink("chrome") == TypeInk(family="jost", weight="medium", size=10.0)
    assert ramp.ink("chrome", "strong") == TypeInk(family="jost", weight="medium", size=10.0)
    assert ramp.ink("eyebrow") == TypeInk(family="jost", weight="medium", size=12.0)
    assert ramp.ink("title").size == 11


def test_empty_effective_ramp_matches_jost_defaults():
    empty = EffectiveRamp()
    jost = JostRamp()
    for step in TYPE_STEPS:
        assert empty.ink(step) == jost.ink(step)
        assert empty.ink(step, "strong") == jost.ink(step, "strong")


def test_bind_ramp_explicit_wins_over_overlay():
    class StubRamp:
        catalog = jost_catalog()

        def ink(self, step: TypeStep, emphasis: TypeEmphasis = "regular") -> TypeInk:
            return TypeInk(family="jost", weight="book", size=3)

    stub = StubRamp()
    bound = bind_ramp(ramp=stub, overlay=TypeOverlay(chrome=TypePatch(size=99)))
    assert bound is stub
    assert bound.ink("chrome").size == 3
    overlay_only = bind_ramp(overlay=TypeOverlay(chrome=TypePatch(size=9.0)))
    assert overlay_only.ink("chrome").size == 9.0


def test_patch_validators_are_pure():
    with pytest.raises(ValueError, match="size must be > 0"):
        TypePatch(size=0)
    with pytest.raises(ValueError, match="unknown weight"):
        TypePatch(weight="hairline")  # type: ignore[arg-type]


def test_nomad_overlay_is_identity():
    assert NOMAD_TYPE_OVERLAY == TypeOverlay()
    assert NOMAD.type_overlay == TypeOverlay()
    ramp = EffectiveRamp(overlay=NOMAD.type_overlay)
    jost = JostRamp()
    for step in TYPE_STEPS:
        assert ramp.ink(step) == jost.ink(step)
        assert ramp.ink(step, "strong") == jost.ink(step, "strong")


def test_identity_effective_ramp_reaches_cover_and_header():
    ramp = EffectiveRamp(overlay=NOMAD.type_overlay)
    header = RecordingPlotter()
    paint_header(header, NOMAD, "Year", "2026", chip="01", ramp=ramp)
    chip = next(op for op in header.ops if op[0] == "text" and op[2] == "01")
    assert chip[3] == 7.4
    assert chip[9] == "book"
    assert _family(chip) == "jost"
    title = next(op for op in header.ops if op[0] == "text" and op[2] == "Year")
    assert title[3] == 11
    assert title[9] == "medium"
    cover = RecordingPlotter()
    paint_cover(cover, NOMAD, _cover(), ramp=ramp)
    brow = next(op for op in cover.ops if op[0] == "text" and op[2] == "Year Book")
    assert brow[3] == 10
    assert brow[9] == "medium"
    year = next(op for op in cover.ops if op[0] == "text" and op[2] == "2026")
    assert year[3] == 42
    assert year[9] == "heavy"


def test_press_wires_identity_effective_ramp(tmp_path: Path):
    plotter = RecordingPlotter()
    press(Spec(months=(1,), notes_pages=0, project_index_pages=1), tmp_path / "id.pdf", plotter=plotter)
    brow = next(op for op in plotter.ops if op[0] == "text" and op[2] == "Year Book")
    assert brow[3] == 10
    assert brow[9] == "medium"
    assert _family(brow) == "jost"
    year = next(op for op in plotter.ops if op[0] == "text" and op[2] == "2026")
    assert year[3] == 42
    assert year[9] == "heavy"
    chrome_meta = next(op for op in plotter.ops if op[0] == "text" and op[2] == "Q1–Q4")
    assert chrome_meta[3] == 7.4
    assert chrome_meta[9] == "book"
    device_ramp = bind_ramp(overlay=compose_overlays(NOMAD.type_overlay, None))
    assert isinstance(device_ramp, EffectiveRamp)
    assert device_ramp.ink("chrome") == JostRamp().ink("chrome")
    assert device_ramp.ink("title") == JostRamp().ink("title")


def test_press_overlay_reaches_header_roles(tmp_path: Path):
    plotter = RecordingPlotter()
    press(
        Spec(months=(1,), notes_pages=0, project_index_pages=1),
        tmp_path / "over.pdf",
        plotter=plotter,
        overlay=TypeOverlay(chrome=TypePatch(size=9.1, weight="medium")),
    )
    chrome_meta = next(op for op in plotter.ops if op[0] == "text" and op[2] == "Q1–Q4")
    assert chrome_meta[3] == 9.1
    assert chrome_meta[9] == "medium"
    assert _family(chrome_meta) == "jost"
    title = next(op for op in plotter.ops if op[0] == "text" and op[2] == "2026" and op[3] == 11)
    assert title[9] == "medium"
    brow = next(op for op in plotter.ops if op[0] == "text" and op[2] == "Year Book")
    assert brow[3] == 10
    assert brow[9] == "medium"


def test_toml_overlay_reaches_cover_and_header():
    spec = Spec.from_path(Path("examples/mvp-typo-overlay.toml"))
    ramp = EffectiveRamp(overlay=spec.type_overlay)
    header = RecordingPlotter()
    paint_header(header, NOMAD, "Year", "2026", chip="01", ramp=ramp)
    chip = next(op for op in header.ops if op[0] == "text" and op[2] == "01")
    assert chip[3] == 9.6
    assert chip[9] == "bold"
    assert _family(chip) == "jost"
    title = next(op for op in header.ops if op[0] == "text" and op[2] == "Year")
    assert title[3] == 14
    assert title[9] == "bold"
    cover = RecordingPlotter()
    paint_cover(cover, NOMAD, _cover(), ramp=ramp)
    brow = next(op for op in cover.ops if op[0] == "text" and op[2] == "Year Book")
    assert brow[3] == 13
    assert brow[9] == "bold"
    year = next(op for op in cover.ops if op[0] == "text" and op[2] == "2026")
    assert year[3] == 48
    assert year[9] == "heavy"


def test_press_loads_toml_overlay(tmp_path: Path):
    spec = replace(
        Spec.from_path(Path("examples/mvp-typo-overlay.toml")),
        months=(1,),
        notes_pages=0,
        project_index_pages=1,
    )
    plotter = RecordingPlotter()
    press(spec, tmp_path / "overlay.pdf", plotter=plotter)
    brow = next(op for op in plotter.ops if op[0] == "text" and op[2] == "Year Book")
    assert brow[3] == 13
    assert brow[9] == "bold"
    assert _family(brow) == "jost"
    year = next(op for op in plotter.ops if op[0] == "text" and op[2] == "2026")
    assert year[3] == 48
    chrome_meta = next(op for op in plotter.ops if op[0] == "text" and op[2] == "Q1–Q4")
    assert chrome_meta[3] == 9.6
    assert chrome_meta[9] == "bold"
    sizes = {op[3] for op in plotter.ops if op[0] == "text" and op[2] == "2026"}
    assert 48 in sizes
    assert 14 in sizes


def test_proof_profile_is_slightly_larger_chrome_and_title():
    assert isinstance(PROOF_PROFILE, ProofProfile)
    ramp = EffectiveRamp(overlay=PROOF_PROFILE.overlay)
    assert ramp.ink("chrome") == TypeInk(family="jost", weight="book", size=PROOF_CHROME_SIZE)
    assert ramp.ink("title") == TypeInk(family="jost", weight="medium", size=PROOF_TITLE_SIZE)
    assert ramp.ink("eyebrow") == TypeInk(family="jost", weight="medium", size=PROOF_EYEBROW_SIZE)
    assert ramp.ink("display") == TypeInk(family="jost", weight="heavy", size=42)
    assert PROOF_PROFILE.overlay.display is None
    assert PROOF_CHROME_SIZE == pytest.approx(JostRamp().ink("chrome").size + 1.8)
    assert PROOF_TITLE_SIZE == pytest.approx(JostRamp().ink("title").size + 2)
    assert PROOF_EYEBROW_SIZE == pytest.approx(JostRamp().ink("eyebrow").size + 2)


def test_proof_stacks_on_device_without_mutating_device_overlay():
    device = TypeOverlay(chrome=TypePatch(size=8.6, weight="medium"))
    before = device.chrome
    merged = compose_overlays(device, PROOF_PROFILE.overlay)
    assert device.chrome is before
    assert device.chrome is not None
    assert device.chrome.size == 8.6
    assert merged.chrome is not None
    assert merged.chrome.size == PROOF_CHROME_SIZE
    assert merged.chrome.weight == "medium"
    assert NOMAD.type_overlay == TypeOverlay()


def test_proof_stacks_after_device_and_toml():
    device = TypeOverlay(chrome=TypePatch(size=8.0, weight="medium"))
    toml = TypeOverlay(chrome=TypePatch(size=8.5), title=TypePatch(size=12.0))
    merged = compose_overlays(device, toml, PROOF_PROFILE.overlay)
    ramp = EffectiveRamp(overlay=merged)
    assert ramp.ink("chrome") == TypeInk(family="jost", weight="medium", size=PROOF_CHROME_SIZE)
    assert ramp.ink("title") == TypeInk(family="jost", weight="medium", size=PROOF_TITLE_SIZE)
    assert ramp.ink("display") == TypeInk(family="jost", weight="heavy", size=42)


def test_proof_overlay_reaches_header_and_cover():
    ramp = EffectiveRamp(overlay=PROOF_PROFILE.overlay)
    header = RecordingPlotter()
    paint_header(header, NOMAD, "Year", "2026", chip="01", ramp=ramp)
    chip = next(op for op in header.ops if op[0] == "text" and op[2] == "01")
    assert chip[3] == PROOF_CHROME_SIZE
    assert chip[9] == "book"
    assert _family(chip) == "jost"
    title = next(op for op in header.ops if op[0] == "text" and op[2] == "Year")
    assert title[3] == PROOF_TITLE_SIZE
    assert title[9] == "medium"
    cover = RecordingPlotter()
    paint_cover(cover, NOMAD, _cover(), ramp=ramp)
    brow = next(op for op in cover.ops if op[0] == "text" and op[2] == "Year Book")
    assert brow[3] == PROOF_EYEBROW_SIZE
    assert brow[9] == "medium"
    year = next(op for op in cover.ops if op[0] == "text" and op[2] == "2026")
    assert year[3] == 42
    assert year[9] == "heavy"


def test_press_proof_flag_applies_proof_profile(tmp_path: Path):
    plotter = RecordingPlotter()
    press(
        Spec(months=(1,), notes_pages=0, project_index_pages=1),
        tmp_path / "proof.pdf",
        plotter=plotter,
        proof=True,
    )
    brow = next(op for op in plotter.ops if op[0] == "text" and op[2] == "Year Book")
    assert brow[3] == PROOF_EYEBROW_SIZE
    chrome_meta = next(op for op in plotter.ops if op[0] == "text" and op[2] == "Q1–Q4")
    assert chrome_meta[3] == PROOF_CHROME_SIZE
    page_title = next(
        op for op in plotter.ops if op[0] == "text" and op[2] == "2026" and op[3] == PROOF_TITLE_SIZE
    )
    assert page_title[9] == "medium"
    cover_year = next(op for op in plotter.ops if op[0] == "text" and op[2] == "2026" and op[3] == 42)
    assert cover_year[9] == "heavy"


def test_press_proof_profile_instance(tmp_path: Path):
    custom = ProofProfile(overlay=TypeOverlay(chrome=TypePatch(size=10.5)))
    plotter = RecordingPlotter()
    press(
        Spec(months=(1,), notes_pages=0, project_index_pages=1),
        tmp_path / "custom.pdf",
        plotter=plotter,
        proof=custom,
    )
    chrome_meta = next(op for op in plotter.ops if op[0] == "text" and op[2] == "Q1–Q4")
    assert chrome_meta[3] == 10.5
    brow = next(op for op in plotter.ops if op[0] == "text" and op[2] == "Year Book")
    assert brow[3] == 10


def test_press_proof_stacks_after_real_toml_overlay(tmp_path: Path):
    spec = replace(
        Spec.from_path(Path("examples/mvp-typo-overlay.toml")),
        months=(1,),
        notes_pages=0,
        project_index_pages=1,
    )
    plotter = RecordingPlotter()
    press(spec, tmp_path / "toml-proof.pdf", plotter=plotter, proof=True)
    brow = next(op for op in plotter.ops if op[0] == "text" and op[2] == "Year Book")
    assert brow[3] == PROOF_EYEBROW_SIZE
    assert brow[9] == "bold"
    chrome_meta = next(op for op in plotter.ops if op[0] == "text" and op[2] == "Q1–Q4")
    assert chrome_meta[3] == PROOF_CHROME_SIZE
    assert chrome_meta[9] == "bold"
    page_title = next(
        op for op in plotter.ops if op[0] == "text" and op[2] == "2026" and op[3] == PROOF_TITLE_SIZE
    )
    assert page_title[9] == "bold"
    year = next(op for op in plotter.ops if op[0] == "text" and op[2] == "2026" and op[3] == 48)
    assert year[9] == "heavy"


def test_press_proof_rejects_unknown_type():
    with pytest.raises(TypeError, match="proof must be bool or ProofProfile"):
        _proof_overlay("yes")  # type: ignore[arg-type]


def test_type_ref_is_frozen_type_step_only():
    from dataclasses import fields

    names = {item.name for item in fields(TypeRef)}
    assert names == {"step", "emphasis", "size"}
    ref = TypeRef(step="chrome", emphasis="strong")
    assert ref.step == "chrome"
    with pytest.raises(AttributeError):
        ref.step = "title"  # type: ignore[misc]
    assert TypeRef(step="micro").step == "micro"
    with pytest.raises(ValueError, match="unknown type step"):
        TypeRef(step="cover_year")  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="size must be > 0"):
        TypeRef(step="chrome", size=0)


def test_ramp_resolve_typeref_uses_type_step():
    ramp = JostRamp()
    assert ramp.resolve(TypeRef(step="display")) == ramp.ink("display")
    assert ramp.resolve(TypeRef(step="title", emphasis="strong")) == ramp.ink("title", "strong")
    assert ramp.resolve(TypeRef(step="chrome", size=7.6)) == TypeInk(
        family="jost", weight="book", size=7.6
    )
    over = EffectiveRamp(overlay=TypeOverlay(chrome=TypePatch(size=9.1, weight="medium")))
    assert over.resolve(TypeRef(step="chrome")) == TypeInk(family="jost", weight="medium", size=9.1)
    assert over.resolve(TypeRef(step="chrome", size=7.6)) == TypeInk(
        family="jost", weight="medium", size=7.6
    )
    proof = EffectiveRamp(overlay=PROOF_PROFILE.overlay)
    assert proof.resolve(TypeRef(step="chrome")) == TypeInk(
        family="jost", weight="book", size=PROOF_CHROME_SIZE
    )
    assert proof.resolve(TypeRef(step="chrome", size=7.6)) == TypeInk(
        family="jost", weight="book", size=7.6
    )
    assert proof.resolve(TypeRef(step="display")) == TypeInk(family="jost", weight="heavy", size=42)


def test_plotter_ref_and_ink_only():
    plotter = Fpdf2Plotter(NOMAD)
    plotter.begin_page()
    plotter.text(Rect(4, 12, 40, 8), "ref", ref=TypeRef(step="title"))
    assert plotter.pdf.font_family == "jost:medium"
    plotter.text(Rect(4, 22, 40, 8), "ink", ink=TypeInk(family="jost", weight="book", size=8))
    assert plotter.pdf.font_family == "jost:book"
    with pytest.raises(TypeError, match="ink= or ref="):
        plotter.text(
            Rect(4, 32, 40, 8),
            "both",
            ink=TypeInk(family="jost", weight="book", size=8),
            ref=TypeRef(step="label"),
        )
    with pytest.raises(TypeError, match="ink= or ref="):
        plotter.text(Rect(4, 42, 40, 8), "neither")

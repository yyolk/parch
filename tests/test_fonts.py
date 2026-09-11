from pathlib import Path

import pytest
from parch.components import CoverTitle
from parch.devices import NOMAD
from parch.fonts import (
    DISPLAY_SIZE,
    JOST_RATIOS,
    JOST_SCALE,
    PROOF_PROFILE,
    ROOT_BODY,
    TYPE_STEPS,
    EffectiveRamp,
    Em,
    FontCatalog,
    Pt,
    ProofProfile,
    TypeEmphasis,
    TypeFamily,
    TypeInk,
    TypeOverlay,
    TypePatch,
    TypeRef,
    TypeStep,
    font_dir,
    jost_catalog,
    pt_from_em,
)
from parch.geom import Rect
from parch.layouts.planner.painters import paint_cover, paint_header
from parch.plotter import RecordingPlotter
from parch.plotter.fpdf2 import Fpdf2Plotter
from parch.press import press
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
    ramp = EffectiveRamp()
    rank = {"book": 0, "medium": 1, "bold": 2, "heavy": 3}
    for step in TYPE_STEPS:
        regular = ramp.ink(step)
        strong = ramp.ink(step, "strong")
        assert regular == ramp.ink(step, emphasis="regular")
        assert regular.family == "jost"
        assert strong.family == "jost"
        assert regular.size == strong.size == JOST_SCALE[step].size
        assert regular.weight == JOST_SCALE[step].regular
        assert strong.weight == JOST_SCALE[step].strong
        catalog.path(regular.family, regular.weight)
        catalog.path(strong.family, strong.weight)
        assert rank[strong.weight] >= rank[regular.weight]

    assert ramp.root_body == ROOT_BODY == Pt(8.5)
    assert ramp.ink("display") == TypeInk(family="jost", weight="heavy", size=DISPLAY_SIZE)
    assert ramp.ink("title") == TypeInk(family="jost", weight="medium", size=Pt(11))
    assert ramp.ink("title", "strong") == TypeInk(family="jost", weight="bold", size=Pt(11))
    assert ramp.ink("eyebrow") == TypeInk(family="jost", weight="medium", size=Pt(10))
    assert ramp.ink("body") == TypeInk(family="jost", weight="book", size=Pt(8.5))
    assert ramp.ink("chrome") == TypeInk(family="jost", weight="book", size=Pt(7.4))
    assert ramp.ink("label") == TypeInk(family="jost", weight="book", size=Pt(6.4))
    assert ramp.ink("caption") == TypeInk(family="jost", weight="book", size=Pt(5.4))
    assert ramp.ink("micro") == TypeInk(family="jost", weight="book", size=Pt(4.3))
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
    paint_cover(plotter, NOMAD, _cover(), ramp=EffectiveRamp())
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
        ramp=EffectiveRamp(),
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
            return TypeInk(family="jost", weight="book", size=Pt(12))

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
                return TypeInk(family="jost", weight="bold", size=Pt(9))
            return TypeInk(family="jost", weight="book", size=Pt(6))

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
    plotter.text(box, "ink", ink=TypeInk(family="jost", weight="heavy", size=Pt(10)))
    assert plotter.pdf.font_family == "jost:heavy"
    plotter.text(box, "smcp", ref=TypeRef(step="label"), small_caps=True)
    assert plotter.pdf.font_family == "jost:book"


def test_fonts_package_does_not_import_plotter():
    import parch.fonts as fonts

    assert "parch.plotter" not in fonts.__dict__
    assert fonts.EffectiveRamp is EffectiveRamp
    assert fonts.TypeInk is TypeInk
    assert fonts.TypeFamily is TypeFamily
    assert fonts.TypeStep is TypeStep
    assert fonts.TypeRef is TypeRef
    assert fonts.jost_catalog is jost_catalog
    assert fonts.FontCatalog is FontCatalog
    assert fonts.TypeOverlay is TypeOverlay
    assert fonts.TypePatch is TypePatch
    assert fonts.TYPE_STEPS is TYPE_STEPS
    assert fonts.ROOT_BODY is ROOT_BODY
    assert fonts.DISPLAY_SIZE is DISPLAY_SIZE
    assert fonts.JOST_RATIOS is JOST_RATIOS
    assert fonts.Em is Em
    assert fonts.Pt is Pt
    assert fonts.pt_from_em is pt_from_em
    assert JOST_RATIOS["body"] == Em(1.0)
    assert ROOT_BODY == Pt(8.5)
    assert DISPLAY_SIZE == Pt(42.0)
    assert fonts.ProofProfile is ProofProfile
    assert fonts.PROOF_PROFILE is PROOF_PROFILE


def test_patch_validators_are_pure():
    with pytest.raises(ValueError, match="size must be > 0"):
        TypePatch(size=Pt(0))
    with pytest.raises(ValueError, match="unknown weight"):
        TypePatch(weight="hairline")  # type: ignore[arg-type]


def test_press_wires_default_ramp(tmp_path: Path):
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


def test_type_ref_is_frozen_type_step_only():
    from dataclasses import fields

    names = {item.name for item in fields(TypeRef)}
    assert names == {"step", "emphasis"}
    ref = TypeRef(step="chrome", emphasis="strong")
    assert ref.step == "chrome"
    with pytest.raises(AttributeError):
        ref.step = "title"  # type: ignore[misc]
    assert TypeRef(step="micro").step == "micro"
    with pytest.raises(ValueError, match="unknown type step"):
        TypeRef(step="cover_year")  # type: ignore[arg-type]


def test_ramp_resolve_typeref_uses_type_step():
    ramp = EffectiveRamp()
    assert ramp.resolve(TypeRef(step="display")) == ramp.ink("display")
    assert ramp.resolve(TypeRef(step="title", emphasis="strong")) == ramp.ink("title", "strong")
    over = EffectiveRamp(overlay=TypeOverlay(chrome=TypePatch(size=Pt(9.1), weight="medium")))
    assert over.resolve(TypeRef(step="chrome")) == TypeInk(family="jost", weight="medium", size=Pt(9.1))
    proof = EffectiveRamp(overlay=PROOF_PROFILE.overlay)
    assert proof.resolve(TypeRef(step="chrome")) == TypeInk(family="jost", weight="book", size=Pt(9.2))
    assert proof.resolve(TypeRef(step="display")) == TypeInk(family="jost", weight="heavy", size=Pt(42))


def test_plotter_ref_and_ink_only():
    plotter = Fpdf2Plotter(NOMAD)
    plotter.begin_page()
    plotter.text(Rect(4, 12, 40, 8), "ref", ref=TypeRef(step="title"))
    assert plotter.pdf.font_family == "jost:medium"
    plotter.text(Rect(4, 22, 40, 8), "ink", ink=TypeInk(family="jost", weight="book", size=Pt(8)))
    assert plotter.pdf.font_family == "jost:book"
    with pytest.raises(TypeError, match="ink= or ref="):
        plotter.text(
            Rect(4, 32, 40, 8),
            "both",
            ink=TypeInk(family="jost", weight="book", size=Pt(8)),
            ref=TypeRef(step="label"),
        )
    with pytest.raises(TypeError, match="ink= or ref="):
        plotter.text(Rect(4, 42, 40, 8), "neither")

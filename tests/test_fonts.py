import pytest
from parch.books import YearPlanner
from parch.components import CoverTitle
from parch.devices.nomad import NOMAD
from parch.fonts import (
    JOST_SCALE,
    TYPE_STEPS,
    FontCatalog,
    JostRamp,
    TypeEmphasis,
    TypeFamily,
    TypeInk,
    TypeStep,
    font_dir,
    jost_catalog,
    scale_ink,
)
from parch.layouts.planner.painters import paint_cover, paint_header
from parch.plotter import RecordingPlotter
from parch.plotter.fpdf2 import Fpdf2Plotter, resolve_weight
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
    assert resolve_weight("sans", False, None) == "book"
    assert resolve_weight("sans", True, None) == "bold"
    assert resolve_weight("serif", False, None) == "medium"
    assert resolve_weight("serif", True, None) == "medium"
    assert resolve_weight("serif", True, "heavy") == "heavy"
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
    """Closed ladder: seven used steps, sizes descend, weights stay in catalog."""
    assert TYPE_STEPS == (
        "display",
        "title",
        "eyebrow",
        "body",
        "chrome",
        "label",
        "caption",
    )
    assert set(JOST_SCALE) == set(TYPE_STEPS)
    sizes = [JOST_SCALE[step].size for step in TYPE_STEPS]
    assert sizes == sorted(sizes, reverse=True)
    assert len(set(sizes)) == len(sizes)

    catalog = jost_catalog()
    ramp = JostRamp()
    _WEIGHT_RANK = {"book": 0, "medium": 1, "bold": 2, "heavy": 3}
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
        assert _WEIGHT_RANK[strong.weight] >= _WEIGHT_RANK[regular.weight]

    assert ramp.ink("display") == TypeInk(family="jost", weight="heavy", size=42)
    assert ramp.ink("title") == TypeInk(family="jost", weight="medium", size=11)
    assert ramp.ink("title", "strong") == TypeInk(family="jost", weight="bold", size=11)
    assert ramp.ink("eyebrow") == TypeInk(family="jost", weight="medium", size=10)
    assert ramp.ink("body") == TypeInk(family="jost", weight="book", size=8.2)
    assert ramp.ink("chrome") == TypeInk(family="jost", weight="book", size=7.4)
    assert ramp.ink("label") == TypeInk(family="jost", weight="book", size=6.4)
    assert ramp.ink("caption") == TypeInk(family="jost", weight="book", size=5.4)
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
    assert specs[3] == 8.2
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
    assert [step for step, _emphasis in ramp.calls] == ["title", "chrome"]
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


def test_year_walk_text_goes_through_scale_ink():
    """Migrated painters pass family+weight from the ramp, not face/bold."""
    plotter = RecordingPlotter()
    YearPlanner().plot(Spec(months=[7], day=15, notes_pages=1), plotter)
    texts = [op for op in plotter.ops if op[0] == "text"]
    assert texts
    bare = [op for op in texts if op[10] is None or op[9] is None]
    assert bare == []
    sizes = {op[3] for op in texts}
    assert sizes <= {cut.size for cut in JOST_SCALE.values()}


def test_fonts_package_does_not_import_plotter():
    import parch.fonts as fonts

    assert "parch.plotter" not in fonts.__dict__
    assert fonts.JostRamp is JostRamp
    assert fonts.TypeInk is TypeInk
    assert fonts.TypeFamily is TypeFamily
    assert fonts.TypeStep is TypeStep
    assert fonts.jost_catalog is jost_catalog
    assert fonts.FontCatalog is FontCatalog
    assert fonts.TYPE_STEPS is TYPE_STEPS

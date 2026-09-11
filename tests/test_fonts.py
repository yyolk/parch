from pathlib import Path

import pytest
from parch.components import CoverTitle
from parch.devices import NOMAD, NOMAD_TYPE_OVERLAY
from parch.fonts import (
    EffectiveRamp,
    FaceBridge,
    FontCatalog,
    JostRamp,
    TypeFace,
    TypeFamily,
    TypeInk,
    TypeOverlay,
    TypePatch,
    TypeRole,
    TypeWeight,
    apply_overlay,
    bind_ramp,
    compose_overlays,
    font_dir,
    jost_catalog,
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


def test_face_bridge_mapping_table():
    bridge = FaceBridge()
    assert bridge.resolve("serif", False, 10) == TypeInk(family="jost", weight="medium", size=10)
    assert bridge.resolve("serif", True, 11) == TypeInk(family="jost", weight="medium", size=11)
    assert bridge.resolve("sans", False, 8) == TypeInk(family="jost", weight="book", size=8)
    assert bridge.resolve("sans", True, 8.5) == TypeInk(family="jost", weight="bold", size=8.5)
    assert bridge.resolve("serif", True, 12, weight="heavy") == TypeInk(
        family="jost", weight="heavy", size=12
    )
    assert bridge.resolve("sans", False, 9, weight="medium") == TypeInk(
        family="jost", weight="medium", size=9
    )
    with pytest.raises(KeyError, match="family='jost' weight='hairline'"):
        bridge.resolve("sans", False, 10, weight="hairline")  # type: ignore[arg-type]


def test_jost_ramp_owns_face_bridge():
    ramp = JostRamp()
    assert ramp.resolve_face("serif", False, 10) == TypeInk(family="jost", weight="medium", size=10)
    assert ramp.resolve_face("sans", False, 7.6) == TypeInk(family="jost", weight="book", size=7.6)
    assert ramp.resolve_face("sans", True, 7.6) == TypeInk(family="jost", weight="bold", size=7.6)
    assert ramp.resolve_face("serif", True, 14, weight="bold") == TypeInk(
        family="jost", weight="bold", size=14
    )


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


def test_jost_ramp_role_map():
    ramp = JostRamp()
    assert ramp.ink("cover_year") == TypeInk(family="jost", weight="heavy", size=42)
    assert ramp.ink("cover_brow") == TypeInk(family="jost", weight="medium", size=10)
    assert ramp.ink("page_title") == TypeInk(family="jost", weight="medium", size=11)
    assert ramp.ink("chrome") == TypeInk(family="jost", weight="book", size=7.4)
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


def test_cover_year_uses_jost_heavy_via_jost_ramp():
    plotter = RecordingPlotter()
    paint_cover(plotter, NOMAD, _cover(), ramp=JostRamp())
    year = next(op for op in plotter.ops if op[0] == "text" and op[2] == "2026")
    assert year[3] == 42
    assert year[9] == "heavy"
    assert _family(year) == "jost"
    brow = next(op for op in plotter.ops if op[0] == "text" and op[2] == "Year Book")
    assert brow[9] == "medium"
    assert _family(brow) == "jost"
    specs = next(op for op in plotter.ops if op[0] == "text" and "monday weeks" in str(op[2]))
    assert _family(specs) is None
    assert specs[6] == "sans"


def test_header_chrome_is_jost_book_via_jost_ramp():
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
            self.roles: list[TypeRole] = []

        def ink(self, role: TypeRole) -> TypeInk:
            self.roles.append(role)
            return TypeInk(family="jost", weight="book", size=12)

    ramp = StubRamp()
    plotter = RecordingPlotter()
    paint_cover(plotter, NOMAD, _cover(), ramp=ramp)
    assert ramp.roles == ["cover_brow", "cover_year"]
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
            self.roles: list[TypeRole] = []

        def ink(self, role: TypeRole) -> TypeInk:
            self.roles.append(role)
            if role == "page_title":
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
    assert ramp.roles == ["page_title", "chrome"]
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


class _SpyRamp:
    """Ramp that records face-bridge traffic; roles stay unused here."""

    def __init__(self) -> None:
        self.catalog = jost_catalog()
        self.faces: list[tuple[TypeFace, bool, float, TypeWeight | None]] = []

    def ink(self, role: TypeRole) -> TypeInk:
        raise AssertionError(f"role path must not run for face+bold text: {role}")

    def resolve_face(
        self,
        face: TypeFace,
        bold: bool,
        size: float,
        *,
        weight: TypeWeight | None = None,
    ) -> TypeInk:
        self.faces.append((face, bold, size, weight))
        return TypeInk(family="jost", weight="heavy", size=size)


def test_plotter_face_path_uses_ramp_policy():
    ramp = _SpyRamp()
    plotter = Fpdf2Plotter(NOMAD, ramp=ramp)
    plotter.begin_page()
    plotter.text(Rect(4, 12, 40, 8), "face", face="serif", bold=False, size=9)
    assert ramp.faces == [("serif", False, 9, None)]
    assert plotter.pdf.font_family == "jost:heavy"

    plotter.text(
        Rect(4, 22, 40, 8),
        "smcp",
        face="sans",
        bold=True,
        size=7.6,
        small_caps=True,
    )
    assert ramp.faces == [("serif", False, 9, None), ("sans", True, 7.6, None)]
    assert plotter.pdf.font_family == "jost:heavy"

    plotter.text(Rect(4, 32, 40, 8), "role", family="jost", weight="book", size=7.4)
    assert ramp.faces == [("serif", False, 9, None), ("sans", True, 7.6, None)]
    assert plotter.pdf.font_family == "jost:book"


def test_plotter_default_face_bridge_cuts():
    plotter = Fpdf2Plotter(NOMAD)
    plotter.begin_page()
    box = Rect(4, 12, 40, 8)
    plotter.text(box, "sans-reg", face="sans", bold=False, size=8)
    assert plotter.pdf.font_family == "jost:book"
    plotter.text(box, "sans-bold", face="sans", bold=True, size=8)
    assert plotter.pdf.font_family == "jost:bold"
    plotter.text(box, "serif", face="serif", bold=False, size=10)
    assert plotter.pdf.font_family == "jost:medium"
    plotter.text(box, "override", face="sans", bold=False, size=10, weight="heavy")
    assert plotter.pdf.font_family == "jost:heavy"


def test_fonts_package_does_not_import_plotter():
    import parch.fonts as fonts

    assert "parch.plotter" not in fonts.__dict__
    assert fonts.JostRamp is JostRamp
    assert fonts.FaceBridge is FaceBridge
    assert fonts.TypeInk is TypeInk
    assert fonts.TypeFamily is TypeFamily
    assert fonts.TypeFace is TypeFace
    assert fonts.jost_catalog is jost_catalog
    assert fonts.FontCatalog is FontCatalog
    assert fonts.EffectiveRamp is EffectiveRamp
    assert fonts.TypeOverlay is TypeOverlay
    assert fonts.TypePatch is TypePatch


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


def test_overlay_missing_role_keeps_default():
    ramp = EffectiveRamp(overlay=TypeOverlay(chrome=TypePatch(size=9.0)))
    assert ramp.ink("chrome") == TypeInk(family="jost", weight="book", size=9.0)
    assert ramp.ink("page_title") == TypeInk(family="jost", weight="medium", size=11)
    assert ramp.ink("cover_year") == TypeInk(family="jost", weight="heavy", size=42)
    assert ramp.ink("cover_brow") == TypeInk(family="jost", weight="medium", size=10)


def test_overlay_never_changes_family():
    ramp = EffectiveRamp(overlay=TypeOverlay(chrome=TypePatch(size=9.0, weight="heavy")))
    assert ramp.ink("chrome").family == "jost"
    assert set(ramp.catalog.cuts) == set(jost_catalog().cuts)


def test_compose_overlays_later_explicit_field_wins():
    device = TypeOverlay(chrome=TypePatch(size=8.6, weight="medium"), cover_brow=TypePatch(size=12.0))
    press_over = TypeOverlay(chrome=TypePatch(size=10.0))
    merged = compose_overlays(device, press_over)
    ramp = EffectiveRamp(overlay=merged)
    assert ramp.ink("chrome") == TypeInk(family="jost", weight="medium", size=10.0)
    assert ramp.ink("cover_brow") == TypeInk(family="jost", weight="medium", size=12.0)
    assert ramp.ink("page_title").size == 11


def test_empty_effective_ramp_matches_jost_defaults():
    empty = EffectiveRamp()
    jost = JostRamp()
    for role in ("cover_year", "cover_brow", "page_title", "chrome"):
        assert empty.ink(role) == jost.ink(role)


def test_bind_ramp_explicit_wins_over_overlay():
    class StubRamp:
        catalog = jost_catalog()

        def ink(self, role: TypeRole) -> TypeInk:
            return TypeInk(family="jost", weight="book", size=3)

        def resolve_face(
            self,
            face: TypeFace,
            bold: bool,
            size: float,
            *,
            weight: TypeWeight | None = None,
        ) -> TypeInk:
            return TypeInk(family="jost", weight="book", size=size)

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
    for role in ("cover_year", "cover_brow", "page_title", "chrome"):
        assert ramp.ink(role) == jost.ink(role)


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
    assert device_ramp.ink("page_title") == JostRamp().ink("page_title")


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


def test_effective_ramp_owns_face_bridge():
    ramp = EffectiveRamp()
    assert ramp.resolve_face("sans", False, 8) == TypeInk(family="jost", weight="book", size=8)
    assert ramp.resolve_face("serif", True, 10, weight="heavy") == TypeInk(
        family="jost", weight="heavy", size=10
    )

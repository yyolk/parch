from pathlib import Path

import pytest
from parch.books import YearPlanner
from parch.components import CoverTitle
from parch.devices.nomad import NOMAD
from parch.fonts import (
    PROOF_CHROME_SIZE,
    PROOF_COVER_BROW_SIZE,
    PROOF_PAGE_TITLE_SIZE,
    PROOF_PROFILE,
    EffectiveRamp,
    FontCatalog,
    JostRamp,
    ProofProfile,
    TypeFamily,
    TypeInk,
    TypeOverlay,
    TypePatch,
    TypeRole,
    apply_overlay,
    bind_ramp,
    compose_overlays,
    font_dir,
    jost_catalog,
)
from parch.layouts.planner import PlannerLayout
from parch.layouts.planner.painters import paint_cover, paint_header, paint_nav
from parch.plotter import RecordingPlotter
from parch.plotter.fpdf2 import Fpdf2Plotter, resolve_weight
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


def test_fonts_package_does_not_import_plotter():
    import parch.fonts as fonts

    assert "parch.plotter" not in fonts.__dict__
    assert fonts.JostRamp is JostRamp
    assert fonts.TypeInk is TypeInk
    assert fonts.TypeFamily is TypeFamily
    assert fonts.jost_catalog is jost_catalog
    assert fonts.FontCatalog is FontCatalog
    assert fonts.EffectiveRamp is EffectiveRamp
    assert fonts.TypeOverlay is TypeOverlay
    assert fonts.TypePatch is TypePatch
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
    proof = PROOF_PROFILE.overlay
    merged = compose_overlays(device, proof)
    ramp = EffectiveRamp(overlay=merged)
    assert ramp.ink("chrome") == TypeInk(family="jost", weight="medium", size=PROOF_CHROME_SIZE)
    assert ramp.ink("cover_brow") == TypeInk(family="jost", weight="medium", size=PROOF_COVER_BROW_SIZE)
    assert ramp.ink("page_title") == TypeInk(family="jost", weight="medium", size=PROOF_PAGE_TITLE_SIZE)


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


def test_proof_profile_is_slightly_larger_chrome_and_title():
    assert isinstance(PROOF_PROFILE, ProofProfile)
    ramp = EffectiveRamp(overlay=PROOF_PROFILE.overlay)
    assert ramp.ink("chrome") == TypeInk(family="jost", weight="book", size=PROOF_CHROME_SIZE)
    assert ramp.ink("page_title") == TypeInk(
        family="jost", weight="medium", size=PROOF_PAGE_TITLE_SIZE
    )
    assert ramp.ink("cover_brow") == TypeInk(
        family="jost", weight="medium", size=PROOF_COVER_BROW_SIZE
    )
    assert ramp.ink("cover_year") == TypeInk(family="jost", weight="heavy", size=42)
    assert PROOF_CHROME_SIZE > JostRamp().ink("chrome").size
    assert PROOF_PAGE_TITLE_SIZE > JostRamp().ink("page_title").size


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


def test_proof_overlay_reaches_header_and_cover():
    ramp = EffectiveRamp(overlay=PROOF_PROFILE.overlay)
    header = RecordingPlotter()
    paint_header(header, NOMAD, "Year", "2026", chip="01", ramp=ramp)
    chip = next(op for op in header.ops if op[0] == "text" and op[2] == "01")
    assert chip[3] == PROOF_CHROME_SIZE
    assert chip[9] == "book"
    assert _family(chip) == "jost"
    title = next(op for op in header.ops if op[0] == "text" and op[2] == "Year")
    assert title[3] == PROOF_PAGE_TITLE_SIZE
    assert title[9] == "medium"
    cover = RecordingPlotter()
    paint_cover(cover, NOMAD, _cover(), ramp=ramp)
    brow = next(op for op in cover.ops if op[0] == "text" and op[2] == "Year Book")
    assert brow[3] == PROOF_COVER_BROW_SIZE
    assert brow[9] == "medium"
    year = next(op for op in cover.ops if op[0] == "text" and op[2] == "2026")
    assert year[3] == 42
    assert year[9] == "heavy"


def test_proof_overlay_reaches_painters_via_layout():
    layout = PlannerLayout(overlay=PROOF_PROFILE.overlay)
    page = next(p for p in YearPlanner().pages(Spec(notes_pages=1)) if p.dest == "year-2026")
    plotter = RecordingPlotter()
    plotter.begin_page()
    layout.paint(page, plotter, NOMAD)
    meta = next(op for op in plotter.ops if op[0] == "text" and op[2] == "Q1–Q4")
    assert meta[3] == PROOF_CHROME_SIZE
    assert meta[9] == "book"
    title = next(op for op in plotter.ops if op[0] == "text" and op[2] == "2026")
    assert title[3] == PROOF_PAGE_TITLE_SIZE
    assert title[9] == "medium"
    nav = next(op for op in plotter.ops if op[0] == "text" and op[2] == "Year")
    assert nav[3] == PROOF_CHROME_SIZE
    assert nav[9] == "book"
    jan = next(op for op in plotter.ops if op[0] == "text" and op[2] == "Jan")
    assert jan[3] == PROOF_CHROME_SIZE
    assert _family(jan) == "jost"


def test_press_device_only_stays_on_defaults(tmp_path: Path):
    plotter = RecordingPlotter()
    out = tmp_path / "device.pdf"
    press(Spec(months=(1,), notes_pages=0, project_index_pages=1), out, plotter=plotter)
    brow = next(op for op in plotter.ops if op[0] == "text" and op[2] == "Year Book")
    assert brow[3] == 10
    assert brow[9] == "medium"
    chrome_meta = next(op for op in plotter.ops if op[0] == "text" and op[2] == "Q1–Q4")
    assert chrome_meta[3] == 7.4
    assert chrome_meta[9] == "book"
    cover_year = next(op for op in plotter.ops if op[0] == "text" and op[2] == "2026")
    assert cover_year[3] == 42
    page_title = next(
        op for op in plotter.ops if op[0] == "text" and op[2] == "2026" and op[3] == 11
    )
    assert page_title[9] == "medium"


def test_press_proof_flag_applies_proof_profile(tmp_path: Path):
    plotter = RecordingPlotter()
    out = tmp_path / "proof.pdf"
    press(
        Spec(months=(1,), notes_pages=0, project_index_pages=1),
        out,
        plotter=plotter,
        proof=True,
    )
    brow = next(op for op in plotter.ops if op[0] == "text" and op[2] == "Year Book")
    assert brow[3] == PROOF_COVER_BROW_SIZE
    chrome_meta = next(op for op in plotter.ops if op[0] == "text" and op[2] == "Q1–Q4")
    assert chrome_meta[3] == PROOF_CHROME_SIZE
    page_title = next(
        op
        for op in plotter.ops
        if op[0] == "text" and op[2] == "2026" and op[3] == PROOF_PAGE_TITLE_SIZE
    )
    assert page_title[9] == "medium"
    cover_year = next(
        op for op in plotter.ops if op[0] == "text" and op[2] == "2026" and op[3] == 42
    )
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


def test_nav_honors_stub_ramp():
    class StubRamp:
        def __init__(self) -> None:
            self.roles: list[TypeRole] = []

        def ink(self, role: TypeRole) -> TypeInk:
            self.roles.append(role)
            return TypeInk(family="jost", weight="bold", size=9.5)

    ramp = StubRamp()
    plotter = RecordingPlotter()
    paint_nav(plotter, NOMAD, (("Year", "year-2026"), ("Mon", "month-2026-01")), "Year", ramp=ramp)
    assert ramp.roles == ["chrome"]
    year = next(op for op in plotter.ops if op[0] == "text" and op[2] == "Year")
    assert year[3] == 9.5
    assert year[9] == "bold"
    assert _family(year) == "jost"


def test_stub_ramp_still_works_on_effective_path():
    class StubRamp:
        catalog = jost_catalog()

        def ink(self, role: TypeRole) -> TypeInk:
            return TypeInk(family="jost", weight="heavy", size=14)

    layout = PlannerLayout(ramp=StubRamp())
    plotter = RecordingPlotter()
    paint_header(plotter, NOMAD, "Year", "2026", ramp=layout.ramp)
    title = next(op for op in plotter.ops if op[0] == "text" and op[2] == "Year")
    assert title[3] == 14
    assert title[9] == "heavy"

"""Nomad Topband is device-gated. Scribe stays Hyperpaper; MOS profiles keep MOS."""

from datetime import date
from pathlib import Path

from parch.config import load
from parch.devices import SUPERNOTE_A6, SUPERNOTE_NOMAD, is_nomad, is_scribe_family
from parch.mos.configurator import Configurator
from parch.mos.nomad_nav import (
    BEZEL,
    CHROME_H,
    CONTENTS_MORE,
    CONTENTS_PRIMARY,
    TEMPO_H,
    contents_rows,
    context_from_page_id,
    habits_month_id,
    nomad_topband,
    review_week_id,
    strip_dest_id,
    strip_key_for_page_id,
    strip_keys,
    tasks_week_id,
)
from parch.mos.preamble import Preamble
from parch.mos.scribe_nav import scribe_hyperpaper_nav
from parch.mos.manifest import Manifest
from parch.sections.habits import Habits
from parch.sections.tasks import Tasks
from parch.services.generate import Generate
from tests.helpers import base_config, load_default, make_day
from tests.toml_fixtures import short_january
from tests.test_toml_omit_sections import compile_pdf


def _cfg(stem: str, *, extras: bool = False):
    return Configurator(load(base_config(stem, extras=extras)))


def _generate(stem: str, *, extras: bool = False) -> str:
    dto = short_january(load(base_config(stem, extras=extras)))
    return Generate(i18n=load_default()).generate(dto)


def _pages(typst: str) -> list[str]:
    return typst.split("#pagebreak()")


def _page_with(typst: str, needle: str) -> str:
    for page in _pages(typst):
        if needle in page:
            return page
    raise AssertionError(f"no page matching {needle!r}")


def test_is_nomad_only_supernote_nomad():
    assert is_nomad("supernote-nomad")
    assert is_nomad("nomad")
    assert not is_nomad("supernote-a6")
    assert not is_nomad("supernote-a6x")
    assert not is_nomad("kindle-scribe")
    assert not is_nomad("158x210")
    assert not is_nomad("scribe")
    assert SUPERNOTE_A6.id != SUPERNOTE_NOMAD.id
    assert not is_scribe_family("supernote-nomad")


def test_nomad_topband_is_device_gated():
    nomad = _cfg("supernote-nomad")
    scribe = _cfg("kindle-scribe")
    paper = _cfg("158x210")
    a6 = _cfg("supernote-a6")
    assert nomad_topband(nomad) is True
    assert nomad_topband(scribe) is False
    assert nomad_topband(paper) is False
    assert nomad_topband(a6) is False
    assert scribe_hyperpaper_nav(nomad) is False
    assert scribe_hyperpaper_nav(scribe) is True
    assert nomad_topband(Configurator({"planner": {"params": {}}})) is False


def test_strip_order_locked_notes_omitted():
    cfg = _cfg("supernote-nomad", extras=True)
    keys = strip_keys(cfg)
    assert keys == [
        "contents",
        "cal",
        "q",
        "mon",
        "wk",
        "day",
        "tasks",
        "habits",
        "review",
    ]
    assert "notes" not in keys
    slim = _cfg("supernote-nomad")
    slim_keys = strip_keys(slim)
    assert slim_keys == ["contents", "cal", "q", "mon", "wk", "day"]
    assert "tasks" not in slim_keys
    assert "habits" not in slim_keys
    assert "review" not in slim_keys


def test_contents_primary_ends_habits_review_more_is_projects_meetings_about():
    assert CONTENTS_PRIMARY[-2:] == ("habits", "review")
    assert CONTENTS_MORE == ("projects", "meetings", "colophon")
    cfg = _cfg("supernote-nomad", extras=True)
    primary, more = contents_rows(cfg)
    assert primary[-2:] == ["habits", "review"]
    assert "tasks" in primary
    assert "projects" not in primary
    assert more == ["projects", "meetings", "colophon"]
    assert "daily_notes" not in primary
    assert "daily_notes" not in more


def test_into_tasks_wiring_contract():
    cfg = _cfg("supernote-nomad", extras=True)
    jan1 = "2026-01-01"
    w01 = "2026W01"
    month = "month-2026-01-01"
    quarter = "quarter-2026-1"
    assert strip_dest_id("tasks", jan1, cfg) == tasks_week_id(
        make_day(jan1).week()
    )
    assert strip_dest_id("tasks", w01, cfg) == "tasks-2026W01"
    assert strip_dest_id("tasks", month, cfg) == "tasks"
    assert strip_dest_id("tasks", quarter, cfg) == "tasks"
    assert strip_dest_id("tasks", "annual", cfg) == "tasks"
    assert strip_dest_id("tasks", "habits-january", cfg) == "tasks"


def test_on_tasks_topband_jumps_week_start_for_mon_q():
    cfg = _cfg("supernote-nomad", extras=True)
    tasks_w01 = "tasks-2026W01"
    week = make_day("2025-12-29").week()
    assert week.id == "2026W01"
    assert strip_dest_id("wk", tasks_w01, cfg) == "2026W01"
    assert strip_dest_id("mon", tasks_w01, cfg) == week.days()[0].month().id
    assert strip_dest_id("q", tasks_w01, cfg) == week.days()[0].quarter().id
    assert strip_dest_id("day", tasks_w01, cfg) == week.days()[0].id
    assert strip_dest_id("day", "2026W01", cfg) == week.days()[0].id


def test_review_cross_boundary_uses_week_end():
    cfg = _cfg("supernote-nomad", extras=True)
    review_w01 = review_week_id(make_day("2025-12-29").week())
    week = make_day("2025-12-29").week()
    assert strip_dest_id("mon", review_w01, cfg) == week.days()[-1].month().id
    assert strip_dest_id("q", review_w01, cfg) == week.days()[-1].quarter().id
    assert strip_dest_id("day", review_w01, cfg) == week.days()[0].id


def test_habits_day_is_first_of_month_and_quarter_lands_first_month():
    cfg = _cfg("supernote-nomad", extras=True)
    assert strip_dest_id("day", "habits-january", cfg) == "2026-01-01"
    assert strip_dest_id("habits", "quarter-2026-1", cfg) == habits_month_id(
        make_day("2026-01-01").month()
    )
    assert strip_dest_id("habits", "2026-01-15", cfg) == "habits-january"
    assert strip_dest_id("habits", "annual", cfg) == "habits"


def test_context_and_active_keys():
    cfg = _cfg("supernote-nomad", extras=True)
    assert strip_key_for_page_id("2026-01-01") == "day"
    assert strip_key_for_page_id("2026W01") == "wk"
    assert strip_key_for_page_id("month-2026-01-01") == "mon"
    assert strip_key_for_page_id("tasks-2026W01") == "tasks"
    assert strip_key_for_page_id("habits-january") == "habits"
    assert strip_key_for_page_id("review-2026W01") == "review"
    assert strip_key_for_page_id("daily-note-2026-01-01-page-1") == "day"
    assert context_from_page_id("tasks-2026W01", cfg).kind == "tasks_week"
    assert context_from_page_id("habits-january", cfg).kind == "habits_month"


def test_nomad_topband_defaults_writing_pattern_to_lined():
    nomad = _cfg("supernote-nomad")
    assert nomad.dig_bang("planner", "params", "scratch_pad") == "lined"
    weekly = _section(nomad, "weekly")
    assert weekly["params"]["pattern"] == "lined"
    monthly = _section(nomad, "monthly")
    assert monthly["params"]["pattern"] == "lined"
    assert _cfg("158x210").dig_bang("planner", "params", "scratch_pad") == "dotted"
    assert _cfg("kindle-scribe").dig_bang("planner", "params", "scratch_pad") == "dotted"
    assert _cfg("supernote-a6").dig_bang("planner", "params", "scratch_pad") == "dotted"


def _section(cfg, name: str):
    return next(s for s in cfg.enabled_sections() if s["name"] == name)


def test_nomad_emit_uses_page_shell_not_mos():
    typst = _generate("supernote-nomad", extras=True)
    assert "page-shell(" in typst
    assert "section-strip(" in typst
    assert "tempo-bar(" in typst
    daily = _page_with(typst, "Thursday · January 1 <2026-01-01>")
    assert "page-shell(" in daily
    assert "section-strip(" in daily
    assert 'active: "day"' in daily
    assert "mos_strip(" not in daily
    assert "mos_frame(" not in daily
    assert "section_rail(" not in daily
    assert "nav_header(" not in daily
    assert "nomad_daily_well(" in daily
    assert "daily_well(left" not in daily
    assert "daily_well(right" not in daily
    assert "[ 7]" in daily
    assert "[16]" in daily
    assert "[ 8]" in daily
    assert "rows: (regular_height,) + (1fr,) * 10" in daily
    assert "place(bottom + left, line(length: 3mm" not in daily
    assert daily.count("task_tick()") == 6
    assert "rows: (24mm, 1fr)" in daily
    assert "stroke: regular_stroke + black" in daily
    assert "lined_well(lined_fill)" in daily
    assert "box(inset: (x: 1.4mm, y: 0.35mm)" in daily
    assert "[More]" in daily
    assert "Notes" not in daily.split("section-strip(")[1].split(")", 1)[0]
    assert 'text(size: h1)[2026]' in daily
    weekly = _page_with(typst, "Week 1 <2026W01>")
    assert 'active: "wk"' in weekly
    assert "nomad_week_bands(" in weekly
    assert "week_matrix(" not in weekly
    assert "pattern: lined_fill" not in weekly
    assert "[Week notes]" in weekly
    assert "Mon · 29" in weekly
    monthly = _page_with(typst, "January<month-2026-01-01>")
    assert 'active: "mon"' in monthly
    assert "nomad_month_well(" in monthly
    assert "[Month notes]" in monthly
    assert "month_weeks(" not in monthly
    assert "columns: (1fr, 1fr, 1fr, 1fr, 1fr, 1fr, 1fr)" in monthly
    assert "rows: (regular_height,) + (1fr,) * 6" in monthly
    assert "lined_well(lined_fill, tile-height: regular_height)" in monthly
    assert "grid.cell(stroke: regular_stroke + luma(160), [])" in monthly
    assert "stroke: regular_stroke + black, [#" in monthly
    # Strip dests also mention tasks-WEEK; title + active chip locate the page.
    tasks = _page_with(typst, "Tasks ·")
    assert 'active: "tasks"' in tasks
    assert "Tasks · Week 1" in tasks
    assert "padded_link(<2026-01-01>" in tasks
    assert "M29" in tasks
    assert "T1" in tasks
    assert "Mon 29" not in tasks
    if date.today() == date(2026, 1, 1):
        assert "text(size: 6pt, fill: white)[T1]" in tasks
        assert "fill: black" in tasks
    else:
        assert "text(size: 6pt, fill: white)[T1]" not in tasks
    habits_index = _page_with(typst, "[Habits <habits>]")
    assert "page-shell(\n  none," in habits_index
    assert 'active: "habits"' not in habits_index
    habits = _page_with(typst, "Habits · January<habits-january>")
    assert "page-shell(\n  none," in habits
    assert 'active: "habits"' not in habits
    assert "padded_link(<2026-01-01>" in habits
    assert "[Day]" in habits
    assert "Thu 1" not in habits
    assert "columns: (auto, 1fr, 1fr, 1fr, 1fr, 1fr)" in habits
    assert habits.count("task_tick()") == 31 * 5
    cover = _pages(typst)[0]
    assert "page-shell(" in cover
    assert "page-shell(\n  none," in cover
    assert "text(size: 48pt" in cover
    assert "line(length: 42mm, stroke: thick_stroke + black)" in cover
    assert "line(length: 42mm, stroke: regular_stroke + luma(25%))" in cover
    assert cover.count("line(length: 42mm, stroke: thick_stroke + black)") == 1
    assert 'text(size: 7.5pt, font: "Liberation Sans", fill: luma(45%))[Supernote Nomad]' in cover
    assert "text(size: h1)[Supernote Nomad]" not in cover
    assert "title: none" in cover
    annual = _page_with(typst, "<annual>]")
    assert "nomad_year_grid(" in annual
    assert "year-month(" in annual
    assert "[January]" in annual
    assert "start-wd:" in annual
    assert "days: 31" in annual
    assert "[Jan]" not in annual
    assert "month_grid(" not in annual
    assert "grid.hline(stroke: regular_stroke + black)" not in annual
    assert "title: none" in annual
    assert 'tempo-bar((' in annual
    assert "[Q1]" in annual
    assert "[Q2]" in annual
    assert "[Q3]" in annual
    assert "[Q4]" in annual
    assert "(<quarter-2026-1>, [Q1], false)" in annual
    assert "(none, [Q2], false)" in annual
    assert "(none, [Q3], false)" in annual
    assert "(none, [Q4], false)" in annual
    assert "(<quarter-2026-1>, [Q1], true)" not in annual
    quarterly = _page_with(typst, "Quarter 1 <quarter-2026-1>")
    assert "nomad_quarter_well(" in quarterly
    assert "quarter_well(left" not in quarterly
    assert "quarter_well(right" not in quarterly
    assert "[January]" in quarterly
    assert "start-wd:" in quarterly
    assert "days: 31" in quarterly
    assert "[Jan]" not in quarterly
    assert "[Focus]" in quarterly
    assert "[Notes]" in quarterly
    focus = quarterly.split("[Focus]")[1].split("[Notes]")[0]
    assert "lined_well(lined_fill)" not in focus
    assert "columns: (auto, 1fr)" in focus
    assert "task_tick()" in focus
    assert "line(length: 100%, stroke: regular_stroke + black)" in focus
    assert "6.2mm" in focus
    assert "lined_well(lined_fill)" in quarterly.split("[Notes]")[1]
    assert "[Q1]" in quarterly
    assert "[Q2]" in quarterly
    assert "[Q3]" in quarterly
    assert "[Q4]" in quarterly
    assert "‹" not in quarterly.split("tempo-bar(")[1].split(")", 1)[0]
    projects = _page_with(typst, "#[] <project-1>")
    assert "page-shell(\n  none," in projects
    assert "[Name]" in projects
    assert projects.count("lined_well(lined_fill)") == 3
    assert "lined_well(dotted_centered)" not in projects
    meetings_index = _page_with(typst, "[Meetings <meetings>]")
    assert "page-shell(\n  none," in meetings_index
    assert "columns: (2em, 1fr, 16mm)" in meetings_index
    assert "column-gutter: 2mm" in meetings_index
    assert "align: (horizon, bottom, bottom)" in meetings_index
    assert "grid.cell(stroke: (bottom: regular_stroke + black), [])" not in meetings_index
    assert "stroke: (bottom: regular_stroke + black)" not in meetings_index
    meeting = _page_with(typst, "#[] <meeting-1>")
    assert "page-shell(\n  none," in meeting
    assert "columns: (1fr, 2fr, 1fr)" not in meeting
    assert "rows: (auto, auto, 1fr, auto)" in meeting
    assert "[Name]" in meeting
    assert "[Date]" in meeting
    assert "lined_well(lined_fill)" in meeting
    assert meeting.count("task_tick()") == 9
    assert "lined_well(dotted_centered)" not in meeting
    review_index = _page_with(typst, "[Review <review>]")
    assert "page-shell(\n  none," in review_index
    assert 'active: "review"' not in review_index
    review = _page_with(typst, "Review · Week 1")
    assert "page-shell(\n  none," in review
    assert 'active: "review"' not in review
    assert "title: grid(columns: 1fr," in review
    assert "text(size: 0.85em)" in review
    assert "Review · Week 1 ·" not in review
    assert "[Week notes]" in review
    assert "M29" in review
    assert "T1" in review
    assert "Mon 29" not in review
    assert "Mon 1" not in review
    colo = _page_with(typst, "[About <colophon>]")
    assert "page-shell(\n  none," in colo
    assert "[*Device*]" in colo
    assert "[*Page*]" in colo
    assert "[*Year*]" in colo
    assert "[*Chrome*]" in colo
    assert "[Topband · no side MOS]" in colo
    assert "[Nomad Topband]" not in colo
    assert "[*Edition*]" in colo
    assert "[*Version*]" not in colo
    notes = _page_with(typst, "[Notes <daily-note-2026-01-01-page-1>]")
    assert "lined_well(lined_fill)" in notes
    assert "lined_well(dotted_centered)" not in notes


def test_nomad_habits_floors_stock_columns_to_five():
    nomad = Habits(
        section_name="habits",
        i18n=load_default(),
        configurator=_cfg("supernote-nomad", extras=True),
        habit_columns=Habits.DEFAULT_COLUMNS,
    )
    assert Habits.DEFAULT_COLUMNS == 4
    assert Habits.NOMAD_COLUMNS == 5
    assert nomad.habit_columns == 5
    wide = Habits(
        section_name="habits",
        i18n=load_default(),
        configurator=_cfg("supernote-nomad", extras=True),
        habit_columns=8,
    )
    assert wide.habit_columns == 8
    paper = Habits(
        section_name="habits",
        i18n=load_default(),
        configurator=_cfg("158x210", extras=True),
        habit_columns=Habits.DEFAULT_COLUMNS,
    )
    assert paper.habit_columns == 4


def _nomad_tasks_short() -> Tasks:
    return Tasks(
        section_name="tasks",
        i18n=load_default(),
        configurator=Configurator(short_january(load(base_config("supernote-nomad", extras=True)))),
    )


def test_nomad_tasks_day_cell_compares_date_today_not_weekday():
    src = Path(__file__).resolve().parents[1].joinpath("src/parch/sections/tasks.py").read_text()
    cell = src[src.index("def _day_cell") : src.index("ink =")]
    assert "today = day.day == date.today()" in cell
    assert "thursday" not in cell
    assert "_focus_date" not in src
    assert "weekday_name == " not in cell


def test_nomad_tasks_inverts_calendar_today_when_on_strip():
    section = _nomad_tasks_short()
    manifest = Manifest()
    today = date.today()
    on = section._day_cell(manifest, make_day(today.isoformat()))
    assert "fill: white" in on
    assert "fill: black" in on
    other = date(2026, 1, 1)
    if today != other:
        off = section._day_cell(manifest, make_day(other.isoformat()))
        assert "fill: white" not in off
        assert "fill: black" not in off


def test_mos_tasks_never_inverts_strip_cell():
    section = Tasks(
        section_name="tasks",
        i18n=load_default(),
        configurator=_cfg("158x210", extras=True),
    )
    cell = section._day_cell(Manifest(), make_day("2026-01-01"))
    assert "Thursday 1" in cell
    assert "fill: white" not in cell
    assert "fill: black" not in cell


def test_other_devices_keep_their_chrome():
    scribe = _generate("kindle-scribe")
    paper = _generate("158x210")
    a6 = _generate("supernote-a6")
    assert "page-shell(" not in scribe
    assert "section-strip(" not in scribe
    assert "section_rail(" in scribe
    assert "nav_header(" in scribe
    assert "page-shell(" not in paper
    assert "mos_strip(" in paper
    assert "page-shell(" not in a6
    assert "mos_strip(" in a6
    assert "mos_frame(" in a6


def test_nomad_preamble_binds_bezel_and_chrome_tokens():
    typst = Preamble(_cfg("supernote-nomad")).generate()
    assert f"bezel: {BEZEL}" in typst
    assert f"height: {CHROME_H}" in typst
    assert f"height: {TEMPO_H}" in typst
    assert "#let lined_fill = lined_fill(paint: black)" in typst
    assert "rail-clearance:" not in typst
    paper = Preamble(_cfg("158x210")).generate()
    assert "#let lined_fill = lined_fill()" in paper
    assert "bezel:" not in paper
    assert "page-shell" in paper
    scribe = Preamble(_cfg("kindle-scribe")).generate()
    assert "bezel:" not in scribe
    assert "rail-clearance:" in scribe


def test_nomad_contents_has_more_and_no_notes_chip():
    typst = _generate("supernote-nomad", extras=True)
    page = _page_with(typst, "[Contents <index>]")
    assert "Habits" in page
    assert "Review" in page
    assert page.index("Habits") < page.index("Review")
    assert page.index("Review") < page.index("MORE")
    assert page.index("MORE") < page.index("Projects")
    assert page.index("Projects") < page.index("Meetings")
    assert page.index("Meetings") < page.index("About")
    assert "About this notebook" not in page
    assert "year glance" in page
    assert "[colophon]" in page
    assert 'text(size: 11pt, fill: luma(50%))[›]' in page
    assert "inset: (x: 2mm, y: 3.2mm)" in page
    assert "rows: (auto, 2mm, 1fr)" in page
    assert 'text(fill: white, size: 14pt, weight: "bold")[Contents <index>]' in page
    assert 'font: "Liberation Sans")[2026]' in page
    assert "rows: (9mm, 9mm, 9mm, 9mm, 9mm, 9mm, 9mm, 9mm)" not in page
    assert "Notes" not in page or "daily_notes" not in page
    assert "page-shell(" not in page
    assert "mos_frame(" not in page


def test_nomad_sample_page_numbers_find_topband_dests():
    from parch.services.preview_svg import sample_page_numbers

    typst = _generate("supernote-nomad", extras=True)
    pages = sample_page_numbers(
        typst,
        year=2026,
        week_id="2026W01",
        jan1="2026-01-01",
        stems=("contents", "daily-jan1", "weekly-w01", "monthly-jan", "tasks-w01", "habits-jan"),
    )
    assert pages["contents"] < pages["monthly-jan"] < pages["weekly-w01"] < pages["daily-jan1"]
    assert pages["habits-jan"] < pages["tasks-w01"]


def test_nomad_short_january_compiles(tmp_path):
    typst = _generate("supernote-nomad", extras=True)
    pdf, stderr = compile_pdf(typst, tmp_path / "nomad-topband", device="supernote-nomad")
    assert pdf.is_file() and pdf.stat().st_size > 0, stderr

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
    assert "tempo-row(" in typst
    assert "tempo-bar(" not in typst
    daily = _page_with(typst, "Thursday  ·  January 1 <2026-01-01>")
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
    assert 'text(size: 10pt, weight: "bold")[Thursday  ·  January 1 <2026-01-01>]' in daily
    assert 'text(size: h1)[Thursday' not in daily
    assert 'text(size: h1)[2026]' not in daily
    assert 'text(size: 7.5pt, weight: "bold")[2026]' in daily
    assert "chip([Wk1]" in daily
    assert "chip([Jan], active: true" in daily
    assert "chip([Q1]" in daily
    assert "place(bottom + left, line(length: 3mm" not in daily
    assert "lined_well(lined_fill)" not in daily
    assert "lined_well(dotted_centered)" not in daily
    assert "padded_link(<daily-note-2026-01-01-page-1>)[More]" in daily
    assert "mini-month(" in daily
    assert "highlight: 1" in daily
    assert "compact: true" in daily
    assert "month_grid(" not in daily
    assert "LittleCalendar" not in daily
    assert "Notes" not in daily.split("section-strip(")[1].split(")", 1)[0]
    weekly = _page_with(typst, "Week 1 <2026W01>")
    assert 'active: "wk"' in weekly
    assert "nomad_week_bands(" in weekly
    assert "week_matrix(" not in weekly
    assert "pattern: lined_fill" not in weekly
    assert "[Week notes]" in weekly
    assert "Mon  ·  29" in weekly
    assert 'text(size: 10pt, weight: "bold")[Week 1 <2026W01>  ·  Dec 29 – Jan 4]' in weekly
    assert 'text(size: h1)[Week 1' not in weekly
    assert 'text(size: h1)[2026]' not in weekly
    assert 'text(size: 7.5pt, weight: "bold")[2026]' in weekly
    monthly = _page_with(typst, "January 2026 <month-2026-01-01>")
    assert 'active: "mon"' in monthly
    assert "nomad_month_well(" in monthly
    assert "[Month notes]" in monthly
    assert "month_weeks(" not in monthly
    assert 'text(size: 10pt, weight: "bold")[January 2026 <month-2026-01-01>]' in monthly
    assert 'text(size: h1)[January' not in monthly
    assert "year: none" in monthly
    assert 'text(size: h1)[2026]' not in monthly
    assert "column-gutter: 0.7mm" in monthly
    assert "row-gutter: 0.7mm" in monthly
    assert "rows: (1fr,) * 6" in monthly
    assert "rows: (regular_height,) + (1fr,) * 6" not in monthly
    assert "lined_well(lined_fill, tile-height: regular_height)" not in monthly
    assert "let tile = 5.2mm" in monthly
    assert "hair + luma(75%)" in monthly
    assert "hair + ink" in monthly
    assert "luma(160)" not in monthly
    assert "grid.cell(stroke: regular_stroke" not in monthly
    assert 'font: "Liberation Sans", size: 7pt' in monthly
    assert 'size: 7.5pt, weight: "bold", font: "Liberation Sans"' in monthly
    assert 'text(weight: "bold", size: 8pt)[Month notes]' in monthly
    assert "chip([Jan], active: true" in monthly
    tasks_index = _page_with(typst, "[Tasks <tasks>]")
    assert "section-strip(" in tasks_index
    assert 'active: "tasks"' in tasks_index
    assert "active: none" not in tasks_index
    assert "page-shell(\n  none," not in tasks_index
    assert 'text(size: 10pt, weight: "bold")[Tasks <tasks>]' in tasks_index
    assert 'text(size: h1)[Tasks' not in tasks_index
    assert 'text(size: h1)[2026]' not in tasks_index
    assert 'text(size: 7.5pt, weight: "bold")[2026]' in tasks_index
    assert "let pack = 7.0mm" in tasks_index
    assert "columns: (10mm, 1fr)" in tasks_index
    assert "column-gutter: 2.5mm" in tasks_index
    assert 'font: "Liberation Sans")[1]' in tasks_index
    assert 'font: "Liberation Sans")[13]' in tasks_index
    assert "[Jan 5 – Jan 11]" in tasks_index
    assert "[Jan 5 – 11]" not in tasks_index
    # Strip dests also mention tasks-WEEK; title + active chip locate the page.
    tasks = _page_with(typst, "Tasks  ·  Week 1")
    assert "section-strip(" in tasks
    assert 'active: "tasks"' in tasks
    assert "active: none" not in tasks
    assert "page-shell(\n  none," not in tasks
    assert 'text(size: 10pt, weight: "bold")[Tasks  ·  Week 1 <tasks-2026W01>  ·  Dec 29 – Jan 4]' in tasks
    assert 'text(size: h1)[Tasks' not in tasks
    assert "padded_link(<2026-01-01>" in tasks
    assert "M29" in tasks
    assert "T1" in tasks
    assert "Mon 29" not in tasks
    assert "chip([Wk1], active: true" in tasks
    assert "column-gutter: 1.0mm" in tasks
    assert "row-gutter: 1.4mm" in tasks
    assert "let min-row = 6.0mm" in tasks
    assert "min-row * 0.55" in tasks
    assert "rows: (top-air,) + (min-row,) * n" in tasks
    assert "let row-h = avail / n" not in tasks
    assert "lined_well(task_fill" not in tasks
    assert 'font: "Liberation Sans"' in tasks
    assert "fill: ink," in tasks
    assert 'fill: white)[T1]' in tasks
    habits_index = _page_with(typst, "[Habits <habits>]")
    assert "section-strip(" in habits_index
    assert 'active: "habits"' in habits_index
    assert "page-shell(\n  none," not in habits_index
    assert "active: none" not in habits_index
    habits = _page_with(typst, "Habits  ·  January<habits-january>")
    assert "section-strip(" in habits
    assert 'active: "habits"' in habits
    assert "page-shell(\n  none," not in habits
    assert "active: none" not in habits
    assert 'text(size: 10pt, weight: "bold")[Habits  ·  January<habits-january>]' in habits
    assert 'text(size: h1)[Habits ·' not in habits
    assert 'text(size: h1)[2026]' not in habits
    assert 'text(size: 7.5pt, weight: "bold")[2026]' in habits
    assert "chip([‹]" in habits
    assert "chip([Jan], active: true" in habits
    assert "chip([›]" in habits
    assert "padded_link(<2026-01-01>" in habits
    assert "[Day]" in habits
    assert "Thu 1" not in habits
    assert "columns: (8mm,) + (1fr,) * 5" in habits
    assert "rows: (5.5mm, 1fr)" in habits
    assert "let row-h = size.height / n" in habits
    assert 'font: "Liberation Sans")[Day]' in habits
    assert "line(length: 100%, stroke: hair + ink)" in habits
    assert habits.count("square(size: 0.8em, stroke: hair + ink)") == 31 * 5
    assert "task_tick()" not in habits
    cover = _pages(typst)[0]
    assert "page-shell(" in cover
    assert "page-shell(\n  none," in cover
    assert 'text(size: 48pt, weight: "bold", tracking: 1.5pt' in cover
    assert "set par(spacing: 0pt)" in cover
    assert "v(5.5mm)" in cover
    assert "ph / 2 - y.height / 2" in cover
    assert "ph * 2 / 3 - r.height / 2" in cover
    assert "footer-bottom = 3mm + 4mm" in cover
    assert "v(1fr)" not in cover
    assert "v(1.15fr)" not in cover
    assert "#v(4mm)" not in cover
    assert "v(0.7mm)" not in cover
    assert "rows: (1fr, 2fr)" not in cover
    assert "line(length: 42mm" not in cover
    assert "box(width: 42mm" in cover
    assert "height: 0.7pt, fill: black" in cover
    assert "height: 0.35pt, fill: luma(25%)" in cover
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
    assert 'tempo-row((' in annual
    assert "chip(" in annual
    assert "tempo-bar(" not in annual
    assert "[Q1]" in annual
    assert "[Q2]" in annual
    assert "[Q3]" in annual
    assert "[Q4]" in annual
    assert "chip([Q1], active: false, dest: <quarter-2026-1>, expand: true)" in annual
    assert "chip([Q2], active: false, expand: true)" in annual
    assert "chip([Q3], active: false, expand: true)" in annual
    assert "chip([Q4], active: false, expand: true)" in annual
    assert "chip([Q1], active: true" not in annual
    assert "(<quarter-2026-1>, [Q1], false)" not in annual
    quarterly = _page_with(typst, "Quarter 1 <quarter-2026-1>")
    assert "nomad_quarter_well(" in quarterly
    assert "quarter_well(left" not in quarterly
    assert "quarter_well(right" not in quarterly
    assert 'text(size: 10pt, weight: "bold")[Quarter 1 <quarter-2026-1>]' in quarterly
    assert 'text(size: h1)[Quarter 1' not in quarterly
    assert 'text(size: h1)[2026]' not in quarterly
    assert 'text(size: 7.5pt, weight: "bold")[2026]' in quarterly
    assert "[January]" in quarterly
    assert "start-wd:" in quarterly
    assert "days: 31" in quarterly
    assert "column-gutter: 2.4mm" in quarterly
    assert "inset: (x: 0.2mm, y: 0.15mm)" in quarterly
    assert "[Jan]" not in quarterly
    assert 'text(weight: "bold", size: 8.5pt)[Focus]' in quarterly
    assert 'text(weight: "bold", size: 8.5pt)[Notes]' in quarterly
    assert "[Focus]" in quarterly
    assert "[Notes]" in quarterly
    focus = quarterly.split("[Focus]")[1].split("[Notes]")[0]
    assert "lined_well(lined_fill)" not in focus
    assert "columns: (auto, 1fr)" in focus
    assert "task_tick()" in focus
    assert "line(length: 100%, stroke: regular_stroke + black)" in focus
    assert "6.2mm" in focus
    notes = quarterly.split("[Notes]")[1]
    assert "lined_well(lined_fill)" not in notes
    assert "lined_well(dotted_centered)" not in notes
    assert "let tile = 5.5mm" in notes
    assert "align(bottom, line(length: 100%, stroke: regular_stroke + black))" in notes
    assert "[Q1]" in quarterly
    assert "[Q2]" in quarterly
    assert "[Q3]" in quarterly
    assert "[Q4]" in quarterly
    assert "‹" not in quarterly.split("tempo-row(")[1].split(")", 1)[0]
    projects_index = _page_with(typst, "[Projects <projects>]")
    assert "section-strip(" in projects_index
    assert "active: none" in projects_index
    assert "page-shell(\n  none," not in projects_index
    assert 'text(size: 10pt, weight: "bold")[Projects <projects>]' in projects_index
    assert 'text(size: h1)[Projects' not in projects_index
    assert 'text(size: h1)[2026]' not in projects_index
    assert 'text(size: 7.5pt, weight: "bold")[2026]' in projects_index
    assert "columns: (9mm, 1fr)" in projects_index
    assert "column-gutter: 2mm" in projects_index
    assert "align: (horizon, bottom)" in projects_index
    assert "let pack = 7.0mm" in projects_index
    assert 'font: "Liberation Sans")[1.]' in projects_index
    assert 'font: "Liberation Sans")[16.]' in projects_index
    assert "2 * regular_height" not in projects_index
    assert "stroke: (bottom: regular_stroke)" not in projects_index
    projects = _page_with(typst, "#[] <project-1>")
    assert "section-strip(" in projects
    assert "active: none" in projects
    assert "page-shell(\n  none," not in projects
    assert 'text(size: 10pt, weight: "bold")[Project 1]' in projects
    assert 'text(size: h1)[1]' not in projects
    assert "[Name]" in projects
    assert "rows: (10mm, 1fr)" in projects
    assert "row-gutter: 1.5mm" in projects
    assert "column-gutter: 1.8mm" in projects
    assert "let tile = 5.5mm" in projects
    assert "rows: (tile,) * n" in projects
    assert "let row-h = size.height / n" not in projects
    assert 'text(weight: "bold", size: 8.5pt)[#label]' in projects
    assert 'let cols = ("To do", "Doing", "Done")' in projects
    assert "lined_well(lined_fill)" not in projects
    assert "lined_well(dotted_centered)" not in projects
    meetings_index = _page_with(typst, "[Meetings <meetings>]")
    assert "section-strip(" in meetings_index
    assert "active: none" in meetings_index
    assert "page-shell(\n  none," not in meetings_index
    assert 'text(size: 10pt, weight: "bold")[Meetings <meetings>]' in meetings_index
    assert 'text(size: h1)[Meetings' not in meetings_index
    assert 'text(size: h1)[2026]' not in meetings_index
    assert 'text(size: 7.5pt, weight: "bold")[2026]' in meetings_index
    assert "columns: (9mm, 1fr, 16mm)" in meetings_index
    assert "column-gutter: 2mm" in meetings_index
    assert "align: (horizon, bottom, bottom)" in meetings_index
    assert "let pack = 7.0mm" in meetings_index
    assert 'font: "Liberation Sans")[1.]' in meetings_index
    assert 'font: "Liberation Sans")[16.]' in meetings_index
    assert "grid.cell(stroke: (bottom: regular_stroke + black), [])" not in meetings_index
    assert "stroke: (bottom: regular_stroke + black)" not in meetings_index
    meeting = _page_with(typst, "#[] <meeting-1>")
    assert "section-strip(" in meeting
    assert "active: none" in meeting
    assert "page-shell(\n  none," not in meeting
    assert 'text(size: 10pt, weight: "bold")[Meeting 1]' in meeting
    assert 'text(size: h1)[1]' not in meeting
    assert "columns: (1.4fr, 0.8fr)" in meeting
    assert "row-gutter: 1.6mm" in meeting
    assert "let tile = 5.5mm" in meeting
    assert 'text(weight: "bold", size: 8.5pt)[Topics]' in meeting
    assert 'text(weight: "bold", size: 8.5pt)[Notes]' in meeting
    assert 'text(weight: "bold", size: 8.5pt)[Action items]' in meeting
    assert "[Name]" in meeting
    assert "[Date]" in meeting
    assert "lined_well(lined_fill)" not in meeting
    assert meeting.count("square(size: 0.8em, stroke: hair + ink)") == 9
    assert "lined_well(dotted_centered)" not in meeting
    review_index = _page_with(typst, "[Review <review>]")
    assert "section-strip(" in review_index
    assert "active: none" in review_index
    assert "page-shell(\n  none," not in review_index
    assert 'active: "review"' not in review_index
    assert 'active: "habits"' not in review_index
    assert 'text(size: 10pt, weight: "bold")[Review <review>]' in review_index
    assert 'text(size: h1)[Review' not in review_index
    assert 'text(size: h1)[2026]' not in review_index
    assert 'text(size: 7.5pt, weight: "bold")[2026]' in review_index
    assert "let pack = 7.0mm" in review_index
    assert "weeks.slice(0, n)" in review_index
    assert "rows: (5fr, 8fr)" not in review_index
    assert 'font: "Liberation Sans")[1]' in review_index
    assert 'font: "Liberation Sans")[13]' in review_index
    assert "columns: (10mm, 1fr)" in review_index
    assert "[Jan 5 – Jan 11]" in review_index
    assert "[Jan 5 – 11]" not in review_index
    review = _page_with(typst, "Review  ·  Week 1")
    assert "section-strip(" in review
    assert "active: none" in review
    assert "page-shell(\n  none," not in review
    assert 'active: "review"' not in review
    assert 'text(size: 10pt, weight: "bold")[Review  ·  Week 1 <review-2026W01>  ·  Dec 29 – Jan 4]' in review
    assert 'text(size: h1)[Review' not in review
    assert "title: grid(columns: 1fr," not in review
    assert "text(size: 0.85em)" not in review
    assert "chip([Wk1], active: true" in review
    assert 'text(weight: "bold", size: 8.5pt)[Week notes]' in review
    assert "let tile = 5.5mm" in review
    assert "lined_well(review_lined)" not in review
    assert "column-gutter: 1.0mm" in review
    assert "row-gutter: 1.6mm" in review
    assert "stroke: hair + ink" in review
    assert "M29" in review
    assert "T1" in review
    assert "Mon 29" not in review
    assert "Mon 1" not in review
    colo = _page_with(typst, "[About this notebook <colophon>]")
    assert "section-strip(" in colo
    assert "active: none" in colo
    assert "page-shell(\n  none," not in colo
    assert 'text(size: 10pt, weight: "bold")[About this notebook <colophon>]' in colo
    assert 'text(size: h1)[About' not in colo
    assert 'text(size: h1)[2026]' not in colo
    assert 'text(size: 7.5pt, weight: "bold")[2026]' in colo
    assert "columns: (32mm, 1fr)" in colo
    assert "column-gutter: 3mm" in colo
    assert "row-gutter: 5.5mm" in colo
    assert "[Device]" in colo
    assert "[Page]" in colo
    assert "[Year]" in colo
    assert "[Chrome]" in colo
    assert 'font: "Liberation Sans")[#label]' in colo
    assert "[Topband · no side MOS]" in colo
    assert "[Nomad Topband]" not in colo
    assert "[Edition]" in colo
    assert "[*Version*]" not in colo
    assert "[118.87 × 158.5 mm]" in colo
    assert "parch · yyolk" in colo
    assert "luma(45%)" in colo
    notes = _page_with(typst, "Notes  ·  Thursday  ·  January 1 <daily-note-2026-01-01-page-1>")
    assert "nomad_notes_well()" in notes
    assert "lined_well(lined_fill)" not in notes
    assert "lined_well(dotted_centered)" not in notes
    assert 'text(size: 10pt, weight: "bold")[Notes  ·  Thursday  ·  January 1 <daily-note-2026-01-01-page-1>]' in notes
    assert 'text(size: h1)[Notes' not in notes
    assert 'text(size: 7.5pt, weight: "bold")[2026]' in notes
    assert "chip([Day], active: true" in notes
    assert "chip([Wk1]" in notes
    assert "chip([Jan]" in notes
    assert "chip([Q1]" not in notes


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
    start = section.configurator.start_date().day
    on = section._nomad_day_chip(manifest, make_day(start.isoformat()))
    assert "fill: ink," in on
    assert "fill: white)" in on
    off = section._nomad_day_chip(manifest, make_day("2026-01-02"))
    assert "fill: white," in off
    assert "fill: ink," not in off


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
    assert "#let chip = chip.with(stroke: hair)" in typst
    assert "page-shell.with(stroke: hair)" in typst
    assert "#let nomad_week_bands = nomad_week_bands.with(stroke: hair + ink)" in typst
    assert f"height: {TEMPO_H}" not in typst
    assert "#let lined_fill = lined_fill(paint: black)" in typst
    assert 'font: "Libertinus Serif"' in typst
    assert "mini-month" in typst
    assert "rail-clearance:" not in typst
    paper = Preamble(_cfg("158x210")).generate()
    assert "#let chip = chip.with(stroke: regular_stroke)" in paper
    assert "page-shell.with(stroke: regular_stroke)" in paper
    assert "#let nomad_week_bands = nomad_week_bands.with(stroke: regular_stroke + black)" in paper
    assert "#let lined_fill = lined_fill()" in paper
    assert "bezel:" not in paper
    assert "page-shell" in paper
    assert 'font: "Libertinus Serif"' not in paper
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
    assert "inset: (x: 2mm)" in page
    assert "rows: (14mm, 2mm, 1fr)" in page
    assert "rows: (auto, 2mm, 1fr)" not in page
    assert "#set par(spacing: 0pt)" in page
    assert "let avail = size.height - gap-h" in page
    assert "let natural = avail / n" in page
    assert "calc.max(9mm, natural)" in page
    assert 'text(fill: white, size: 14pt, weight: "bold")[Contents <index>]' in page
    assert '#set text(font: "Libertinus Serif")' in page
    assert 'font: "Liberation Sans")[2026]' in page
    assert "rows: (9mm, 9mm, 9mm, 9mm, 9mm, 9mm, 9mm, 9mm)" not in page
    assert "Notes" not in page or "daily_notes" not in page
    assert "page-shell(" not in page
    assert "mos_frame(" not in page


def test_nomad_calendar_days_and_daily_tempo_link():
    """Annual / quarterly / daily mini-cal days and daily tempo chips carry dests."""
    typst = _generate("supernote-nomad")
    annual = _page_with(typst, "<annual>]")
    jan = annual.split("year-month(")[1]
    assert "dests:" in jan
    assert "<2026-01-01>" in jan
    assert "<2026-01-14>" in jan
    assert jan.split("dests:")[1].count("none") >= 17
    quarterly = _page_with(typst, "Quarter 1 <quarter-2026-1>")
    qjan = quarterly.split("year-month(")[1]
    assert "dests:" in qjan
    assert "<2026-01-01>" in qjan
    assert "<2026-01-14>" in qjan
    daily = _page_with(typst, "Thursday  ·  January 1 <2026-01-01>")
    cal = daily.split("mini-month(")[1]
    assert "dests:" in cal
    assert "<2026-01-01>" in cal.split("dests:")[1]
    assert "<2026-01-02>" in cal.split("dests:")[1]
    assert "chip([Wk1], active: false, dest: <2026W01>, expand: true)" in daily
    assert "chip([Jan], active: true, dest: <month-2026-01-01>, expand: true)" in daily
    assert "chip([Q1], active: false, dest: <quarter-2026-1>, expand: true)" in daily


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

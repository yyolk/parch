# DO NOT MERGE — fpdf2 greenfield planner spike v2

Throwaway experiment on `yyolk/parch`: **what if the yearly planner had been
written against fpdf2 from scratch**, a second time, applying visual lessons
from the first fpdf2 spike (PR #204) and the ReportLab spike (PR #205). This
branch deletes the Typst/parch application tree. It is **not** a migration
and **must not be merged**.

Source is rebuilt clean — no copy from #204 / #205 branches.

## Assumptions

- One PDF, one calendar year. Default year is **2026**.
- **Monday** is the first day of the week.
- Weeks that touch the year are included (2026: Mon 29 Dec 2025 → Sun 3 Jan 2027, 53 pages).
- Daily pages exist only for days **in** the year (365 in 2026). Adjacent-year
  dates appear on week/month grids but have no day page.
- Page size is **106 × 144 mm**, portrait.
- Navigation is a five-tab strip (Year / Qtr / Mon / Wk / Day) on every page
  **except the cover**. Tabs land on the first page of that section.

Chrome is invented for this spike (black header slab + washed footer tabs).
It does **not** copy MOS / rail / band.

## Install and generate

Python 3.12+.

```shell
python3 -m venv .venv
.venv/bin/pip install -e .
.venv/bin/press --specimen
```

```shell
.venv/bin/press                          # full year N=0 → artifacts/planner-2026.pdf
.venv/bin/press --year 2026 -o out.pdf
.venv/bin/press --notes-pages 2
.venv/bin/press --specimen --notes-pages 2
python -m planner --specimen -o artifacts/specimen-2026.pdf
```

`press` and `python -m planner` are the same CLI.

`--notes-pages N`: **1 daily page + N dedicated lined notes pages per day**.
`N=0` is the day page only, with its on-page notes panel.

## Pages

| Section | Count (2026) | Notes |
| --- | --- | --- |
| Cover | 1 | Title + year; **no** nav bar. Year numeral links to the year page. |
| Year | 1 | 12 mini months. Month title → month page; day cell → day page. |
| Quarterly | 4 | Three mini months + notes. |
| Monthly | 12 | Week-number gutter → week page; day cell → day page. |
| Weekly | 53 | One row per weekday; date chip → day page. |
| Daily | 365 | Lined notes + tiny month calendar. Prev/next day chips. |
| Daily notes | `365 × N` | Optional. `--notes-pages N` (default **0**). |

Internal jumps use fpdf2 **page links** plus **named destinations** bound at
the top of each page. Names look like `year`, `q1`, `month-01`,
`week-2025-12-29`, `day-2026-01-01`, `day-2026-01-01-notes-1`.

## Artifacts

- `artifacts/specimen-2026.pdf` — 6 pages (cover, year, Q1, January, first week, 1 Jan).
- `artifacts/specimen-2026-notes2.pdf` — same + 2 notes pages for 1 Jan (8 pages).
- `artifacts/planner-2026.pdf` — full 2026 book, N=0 (436 pages, ~3.1 MB).
- `artifacts/preview/` — PNG rasters of those landings (`cover`, `year`, `quarter`, `month`, `week`, `day`) plus notes pages.
- Full-year N≥2 PDFs are **not** committed (N=100 was ~76 MB). Numbers: [BENCH.md](BENCH.md).

## CI

Old Typst / pytest / specimen-pages workflows are **removed** on this branch
so they cannot go red against a deleted tree. A stub job only installs the
spike and generates a specimen.

## Notes

See [NOTES.md](NOTES.md) for v2 vs v1 look, and vs ReportLab memory.

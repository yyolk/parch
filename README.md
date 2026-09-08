# DO NOT MERGE — ReportLab greenfield planner spike

Throwaway experiment on `yyolk/parch`: **what if the yearly planner had been
written against open-source ReportLab from scratch**, instead of porting
Ruby/Typst/LYP decisions. This branch deletes the Typst/parch application
tree. It is **not** a migration and **must not be merged**.

Uses `pip install reportlab` only (BSD toolkit). No fpdf2, no Typst, no
ReportLab PLUS / rlextra.

## Assumptions

- One PDF, one calendar year. Default year is **2026**.
- **Monday** is the first day of the week.
- Weeks that touch the year are included (2026: Mon 29 Dec 2025 → Sun 3 Jan 2027, 53 pages).
- Daily pages exist only for days **in** the year (365 in 2026). Adjacent-year
  dates appear on week/month grids but have no day page.
- Page size is **106 × 144 mm**, portrait.
- Navigation is a five-tab strip (Year / Qtr / Mon / Wk / Day) on every page
  **except the cover**. Tabs land on the first page of that section.

Chrome is invented for this spike (header slab + bottom tabs). It does **not**
copy MOS / rail / band or the fpdf2 spike’s drawing code.

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

Internal jumps use ReportLab **`bookmarkPage`** destinations plus
**`linkAbsolute`** tap rectangles (`Border='[0 0 0]'`). Names look like
`year`, `q1`, `month-01`, `week-2025-12-29`, `day-2026-01-01`,
`day-2026-01-01-notes-1`.

Emit is **canvas-only** (not Platypus): fixed millimetre cards, not a
flowable story.

## Artifacts

- `artifacts/specimen-2026.pdf` — 6 pages (cover, year, Q1, January, first week, 1 Jan).
- `artifacts/preview/` — PNG rasters of those landings (`cover`, `year`, `quarter`, `month`, `week`, `day`).
- Full-year N≥2 PDFs are **not** committed. Numbers: [BENCH.md](BENCH.md) (after the bench run).

## CI

Old Typst / pytest / specimen-pages workflows are **removed** on this branch
so they cannot go red against a deleted tree. A stub job only installs the
spike and generates a specimen.

## Notes

See [NOTES.md](NOTES.md) for impressions versus the Typst / fpdf2 paths.

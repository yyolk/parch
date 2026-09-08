# DO NOT MERGE — fpdf2 greenfield planner spike

Throwaway experiment on `yyolk/parch`: **what if the yearly planner had been
written against fpdf2 from scratch**, instead of porting Ruby/Typst/LYP
decisions. This branch deletes the Typst/parch application tree. It is **not**
a migration and **must not be merged**.

## Assumptions

- One PDF, one calendar year. Default year is **2026**.
- **Monday** is the first day of the week.
- Weeks that touch the year are included (2026: Mon 29 Dec 2025 → Sun 3 Jan 2027, 53 pages).
- Daily pages exist only for days **in** the year (365 in 2026). Adjacent-year
  dates appear on week/month grids but have no day page.
- Page size is **106 × 144 mm**, portrait (compact e-ink-ish / Nomad-adjacent,
  not a device profile).
- Navigation is a five-tab strip (Year / Qtr / Mon / Wk / Day) on every page
  **except the cover**. Tabs land on the first page of that section.

## Install and generate

Python 3.12+ (this spike does not need 3.14).

```shell
python3 -m venv .venv
.venv/bin/pip install -e .
.venv/bin/press
```

That writes `artifacts/planner-2026.pdf` (full year).

```shell
.venv/bin/press --specimen          # cover + year + Q1 + Jan + first week + 1 Jan
.venv/bin/press --year 2026 -o out.pdf
python -m planner --specimen -o artifacts/specimen-2026.pdf
```

`press` and `python -m planner` are the same CLI.

## Pages

| Section | Count (2026) | Notes |
| --- | --- | --- |
| Cover | 1 | Title + year; **no** nav bar. Year numeral links to the year page. |
| Year | 1 | 12 mini months. Month title → month page; day cell → day page. |
| Quarterly | 4 | Three mini months + notes. |
| Monthly | 12 | Week-number gutter → week page; day cell → day page. |
| Weekly | 53 | One row per weekday; date chip → day page. |
| Daily | 365 | Lined notes + tiny month calendar. Prev/next day chips. |

Internal jumps use fpdf2 **page links** (`add_link(page=…)`) plus **named
destinations** bound at the top of each page (`add_link(name=…)`). Names look
like `year`, `q1`, `month-01`, `week-2025-12-29`, `day-2026-01-01`.

## Artifacts

- `artifacts/specimen-2026.pdf` — 6 pages (cover, year, Q1, January, first week, 1 Jan).
- `artifacts/planner-2026.pdf` — full 2026 book (436 pages, ~2.6 MB in this environment).
- `artifacts/preview/` — PNG rasters of those section landings for glanceable review.

## CI

Old Typst / pytest / specimen-pages workflows are **removed** on this branch
so they cannot go red against a deleted tree. A stub job only installs the
spike and generates a specimen.

## Notes

See [NOTES.md](NOTES.md) for impressions versus the Typst path.

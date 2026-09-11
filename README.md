# parch (greenfield)

Exploratory rewrite of [yyolk/parch](https://github.com/yyolk/parch) on this branch only.

**Do not merge.** `master` is still the Typst / MOS / house product. This tree is a clean slate until yolk cuts over.

parch generates **fixed e-ink PDF pages**. The MVP target is SuperNote Nomad only.

Python 3.14+ required (language features, not just the pin).

## Architecture

```
Device → Component (data only) → Section (build Page) → Layout (chrome + seat) → Plotter → Press
```

Painters live under `layouts/planner/` and take `plotter: Plotter`. Components do not draw. The only plotter backend is `Fpdf2Plotter`. Tests use `RecordingPlotter`.

```
src/parch/
  press.py spec.py
  calendar/
  components/
  sections/
  layouts/planner/
  plotter/{protocol.py,fpdf2.py,recording.py}
  devices/nomad.py
  books/year_planner.py
```

Nomad: 118.87 × 158.5 mm, 1404×1872 @ 300 PPI. Top toolbar 8 mm is reserved — not a writing well. Writing clearance 4 mm.

## Press the MVP

Needs [uv](https://docs.astral.sh/uv/) and Python 3.14+. No Typst.

```shell
uv sync --group dev
uv run parch press examples/mvp.toml -o artifacts/mvp/nomad-2026.pdf
# or
uv run python -m parch press supernote-nomad -o parch.pdf
```

Default spec is year 2026, Monday week start, **full year** (Jan–Dec). Press walks cover → annual → **ticket index** → **three-card projects pages** → meeting index + dests → **Tasks index C + weekly dests** → **Review index B + dest E** → Q1–Q4 quarters → each month **plus its habit tracker** → each ISO week that touches the year (once) → that week’s pressed days + `notes_pages` wells. Thesis L index pages are dest `projects-index-{year}-{nn}` (Proj lands on `-01`). `[projects] index_pages` is the count of index pages (default 1; MVP sample is 3). `[projects] tickets` is rows per index page (6–10, default 8 — Nomad ticket seating). **G dest count = index_pages × tickets** (one row → one `projects-{year}-{n:02d}`). Each index page lists its slice (page 1: 01–K, page 2: K+1…). Stub + each preview card link to that row’s G `paint_project` well (#215); write-in and strip stay unlinkable. Dest header chip is the global slot number and returns to the **owning** index page; lit **Proj** on a dest does the same. Optional `[projects] cards` (2–4, default 3) and `tasks` (3–6, default 4). The quarter page is **A″**: short year-density three minis, then content-height Focus over flex Notes. Bottom nav is Year · Quar · Mon · Habit · **Proj** · **Meet** · **Task** · **Rev** · Week · Day · Notes (QUAR is provisional). Habit lands on that context’s month tracker. A month header **Habits** chip is a shortcut to the same page. DAY/NOTES land on the current day (daily/notes), the first pressed day of a week, the 1st of a month, or Jan 1 from the year page — not a press-time “today”. All twelve months’ days and headers are linked. `examples/mvp.toml` uses `notes_pages = 1` to keep the artifact smaller; `2` still works. Optional `[habits] columns = 10`.

Committed proof: [`artifacts/mvp/nomad-2026.pdf`](artifacts/mvp/nomad-2026.pdf) (2026) and sample PNG previews (annual, projects index, quarters, July month, July habits, week, daily, notes). Thesis L index p1: [`artifacts/mvp/exp-projects-index-l-tickets.png`](artifacts/mvp/exp-projects-index-l-tickets.png). Index p2: [`artifacts/mvp/exp-projects-index-l-tickets-p2.png`](artifacts/mvp/exp-projects-index-l-tickets-p2.png). Dest: [`artifacts/mvp/exp-projects-index-l-leaf.png`](artifacts/mvp/exp-projects-index-l-leaf.png).

Thesis C (in the year walk, after Meetings): month-banded Tasks index + weekly Tasks dest. **Task** tab → index; dest header chip is the ISO week and returns to the owning quarter index. Proof: [`artifacts/mvp/exp-tasks-index-c-months.png`](artifacts/mvp/exp-tasks-index-c-months.png) and [`artifacts/mvp/exp-tasks-index-c-dest.png`](artifacts/mvp/exp-tasks-index-c-dest.png).

Thesis B index + Thesis E dest (in the year walk, after Tasks): multi-column Review week-chip grid + weekly dest (Mon–Sun mini-write strip over unlabeled week narrative). Month headers sit on the left; hairlines span the well so months read across. **Rev** tab → year index; dest header chip is the ISO week and returns to the index. Dest `review-index-{year}` / `review-{iso_year}-W{nn}`. Proof: [`artifacts/mvp/exp-review-index-b.png`](artifacts/mvp/exp-review-index-b.png) and [`artifacts/mvp/exp-review-dest-e.png`](artifacts/mvp/exp-review-dest-e.png).

```shell
uv run pytest
```

## License / Credits

MIT — see [LICENSE](LICENSE).

Historical inspiration: [Vitaliy Kudryk’s LYP](https://github.com/kudrykv/latex-yearly-planner). This branch is a greenfield rewrite (fpdf2 Plotter architecture); it is not a port of LYP sources.

Runtime dependency [fpdf2](https://github.com/py-pdf/fpdf2) is LGPL-3.0, separate from this MIT license.

Vendored [Jost](https://indestructibletype.com/Jost.html) (Book / Medium / Bold / Heavy) is SIL OFL 1.1 — see `src/parch/fonts/LICENSE`. Weights stay curated. Painters pass a frozen `TypeRef` (step or role + optional emphasis + optional size). `Plotter.text(..., ref=)` asks the bound `JostRamp` to resolve `TypeInk`; `family="jost"` stays on the ink for a later dual-font ramp. Cover / header / nav / migrated wells do not unpack weights.

Thesis N specimens (150 PPI, January dests): [`exp-typeramp-typeref-cover.png`](artifacts/mvp/exp-typeramp-typeref-cover.png), [`year`](artifacts/mvp/exp-typeramp-typeref-year.png), [`month`](artifacts/mvp/exp-typeramp-typeref-month.png), [`week`](artifacts/mvp/exp-typeramp-typeref-week.png), [`daily`](artifacts/mvp/exp-typeramp-typeref-daily.png), [`projects`](artifacts/mvp/exp-typeramp-typeref-projects.png).

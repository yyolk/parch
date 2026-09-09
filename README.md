# parch (greenfield)

Exploratory rewrite of [yyolk/parch](https://github.com/yyolk/parch) on this branch only.

**Do not merge.** `master` is still the Typst / MOS / house product. This tree is a clean slate until yolk cuts over.

parch generates **fixed e-ink PDF pages**. The MVP target is SuperNote Nomad only.

Python 3.14+ required.

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

Default spec is year 2026, Monday week start, January, daily page 5 Jan, `notes_pages = 2`. The PDF is cover → one month → one daily (schedule strip + notes) → two lined daily_notes wells, with named destinations and internal links (daily → notes-1, notes → daily/month/cover).

Committed proof: [`artifacts/mvp/nomad-2026.pdf`](artifacts/mvp/nomad-2026.pdf) and the PNG page previews beside it.

```shell
uv run pytest
```

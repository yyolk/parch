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

Default spec is year 2026, Monday week start, January. Press walks **every day in January**: cover → month (each day linked) → daily + `notes_pages` wells after each day. `examples/mvp.toml` uses `notes_pages = 1` to keep the artifact small; `2` still works.

Committed proof: [`artifacts/mvp/nomad-2026.pdf`](artifacts/mvp/nomad-2026.pdf) (full January) and sample PNG previews (cover, month, one daily, one notes).

```shell
uv run pytest
```

## License / Credits

MIT — see [LICENSE](LICENSE).

Historical inspiration: [Vitaliy Kudryk’s LYP](https://github.com/kudrykv/latex-yearly-planner). This branch is a greenfield rewrite (fpdf2 Plotter architecture); it is not a port of LYP sources.

Runtime dependency [fpdf2](https://github.com/py-pdf/fpdf2) is LGPL-3.0, separate from this MIT license.

Vendored [Liberation Fonts](https://github.com/liberationfonts/liberation-fonts) (Sans + Serif) are SIL OFL 1.1 — see `src/parch/fonts/LICENSE`.

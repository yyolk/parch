# Planner fonts

Vendored static TTF subsets (fpdf2 cannot load variable fonts). Weights stay
**curated** — not a global Hairline→Black expansion.

## Jost 3.7

- `Jost-400-Book.ttf` — weight `book` — step `chrome` (and most `body` rows)
- `Jost-500-Medium.ttf` — weight `medium` — steps `title` / `brow`
- `Jost-700-Bold.ttf` — weight `bold` — `body` on month / week / projects
- `Jost-800-Heavy.ttf` — weight `heavy` — cover `display`

Upstream: https://github.com/indestructible-type/Jost
Specimen: https://indestructibletype.com/Jost.html
SIL OFL 1.1 — `LICENSE` / `AUTHORS`. Reserved Font Name: Jost.

## PageKind table (thesis O)

`TypeInk` is `family` + `weight` + `size`. Painters call `ramp.ink(step)` and
pass those fields to `Plotter.text`. Steps are page-agnostic: `body`, `chrome`,
`title`, `display`, `brow`. The active `PageKind` supplies the default
size/weight for that step unless `ink(step, size=…, weight=…)` overrides it.

Layout binds with `ramp.for_page(kind)` and passes the `BoundRamp` in. No
threadlocals. No `ink(step, kind=…)` — kind is not on the painter signature.

**Cover** is a `PageKind` row in the same table (not a side-channel). Cover
painters ask for `display` (year) and `brow` (eyebrow). Interior rows still
have those keys (aliased to `title` / `chrome`) so the table is rectangular.

`FontCatalog` is an explicit `(family, weight) → ttf` map, owned by the ramp
and handed to `Fpdf2Plotter` at press time. Catalog stays Jost-only.

| PageKind | title | chrome | body | display | brow |
| --- | --- | --- | --- | --- | --- |
| `cover` | Medium 10 | Book 7.4 | Book 8.2 | Heavy 42 | Medium 10 |
| `annual` (year) | Medium 11 | Book 7.4 | Book 6.4 | = title | = chrome |
| `month` | Medium 11 | Book 7.4 | Bold 8.5 | = title | = chrome |
| `weekly` | Medium 11 | Book 7.4 | Bold 11 | = title | = chrome |
| `daily` | Medium 11 | Book 7.4 | Book 7 | = title | = chrome |
| `projects_index` / `project` | Medium 11 | Book 7.4 | Bold 6.6 | = title | = chrome |
| other kinds | Medium 11 | Book 7.4 | Book 6.4 | = title | = chrome |

Daily body ≠ week body — that is the table, not a per-painter special case.

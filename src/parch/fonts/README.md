# Planner fonts

Vendored static TTF subsets (fpdf2 cannot load variable fonts). Weights stay
**curated** — not a global Hairline→Black expansion.

## Jost 3.7

- `Jost-400-Book.ttf` — weight `book` — steps `body` / `chrome` / `label` / `caption` (regular)
- `Jost-500-Medium.ttf` — weight `medium` — steps `title` / `eyebrow` (regular)
- `Jost-700-Bold.ttf` — weight `bold` — `strong` emphasis on those steps
- `Jost-800-Heavy.ttf` — weight `heavy` — step `display`

Upstream: https://github.com/indestructible-type/Jost
Specimen: https://indestructibletype.com/Jost.html
SIL OFL 1.1 — `LICENSE` / `AUTHORS`. Reserved Font Name: Jost.

## Type ramp (thesis C — scale tokens)

`TypeInk` is `family` + `weight` + `size`. Painters call
`ramp.ink(step, emphasis="regular")` and pass those fields to `Plotter.text`.
`family` is a closed key (`TypeFamily = Literal["jost"]` today) so a later
dual-font ramp can pick another catalog family without ripping out the plotter
kwarg.

The closed ladder is **design tokens**, not page-semantic roles. Painters pick
from `display` / `title` / `eyebrow` / `body` / `chrome` / `label` / `caption`.
`TypeRole` (`cover_year`, `cover_brow`, `page_title`) is gone — cover and
header migrated in this PR.

`FontCatalog` is an explicit `(family, weight) → ttf` map, owned by the ramp
and handed to `Fpdf2Plotter` at press time.

| Step | Size | Regular | Strong | Typical use |
| --- | --- | --- | --- | --- |
| `display` | 42 | Heavy | Heavy | Cover year |
| `title` | 11 | Medium | Bold | Page titles; week / review day numbers |
| `eyebrow` | 10 | Medium | Bold | Cover brow |
| `body` | 8.2 | Book | Bold | Cover specs; month-grid day numbers |
| `chrome` | 7.4 | Book | Bold | Header chips / meta; nav; hours; Wnn |
| `label` | 6.4 | Book | Bold | Field labels, notes, weekdays, stubs |
| `caption` | 5.4 | Book | Bold | Mini-month days, habit numerals, cues |

Cover, header, nav, and well painters take the ramp via `PlannerLayout`.

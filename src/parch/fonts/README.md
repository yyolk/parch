# Planner fonts

Vendored static TTF subsets (fpdf2 cannot load variable fonts). Weights stay
**curated** — not a global Hairline→Black expansion.

## Jost 3.7

- `Jost-400-Book.ttf` — weight `book` — steps `body` / `chrome` / `label` / `caption`
- `Jost-500-Medium.ttf` — weight `medium` — steps `title` / `eyebrow` (regular)
- `Jost-700-Bold.ttf` — weight `bold` — `emphasis="strong"` on those steps
- `Jost-800-Heavy.ttf` — weight `heavy` — step `display` / role `cover_year`

Upstream: https://github.com/indestructible-type/Jost
Specimen: https://indestructibletype.com/Jost.html
SIL OFL 1.1 — `LICENSE` / `AUTHORS`. Reserved Font Name: Jost.

## Two-phase TypeRef

Painters construct a frozen `TypeRef` — a closed step or role literal, optional
`emphasis` (`regular` | `strong`), optional `size` override. No family, no
weight on the ref.

`PlannerLayout` binds `plotter.ramp`. `Plotter.text(..., ref=)` asks
`ramp.resolve(ref)` once at the plotter edge and draws the resulting `TypeInk`.
Painters do not unpack ink into `family` / `weight` / `size` kwargs.

`TypeInk.family` stays `"jost"` today so a later dual-font ramp can pick
another catalog family without ripping out the resolved ink.

| Step | Size | Regular | Strong | Role aliases |
| --- | --- | --- | --- | --- |
| `display` | 42 | Heavy | Heavy | `cover_year` |
| `title` | 11 | Medium | Bold | `page_title` |
| `eyebrow` | 10 | Medium | Bold | `cover_brow` |
| `body` | 8.2 | Book | Bold | `cover_specs` |
| `chrome` | 7.4 | Book | Bold | `chrome` |
| `label` | 6.4 | Book | Bold | |
| `caption` | 5.4 | Book | Bold | |

Cover, header, nav, and migrated wells (year minis, month, week, daily,
projects index) pass `TypeRef` only. Unmigrated painters still use `face` +
`bold`; `Fpdf2Plotter.resolve_weight` shims those onto Jost.

`FontCatalog` is an explicit `(family, weight) → ttf` map, owned by the ramp
and handed to `Fpdf2Plotter` at press time.

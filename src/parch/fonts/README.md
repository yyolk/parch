# Planner fonts

Vendored static TTF subsets (fpdf2 cannot load variable fonts). Weights stay
**curated** — not a global Hairline→Black expansion.

## Jost 3.7

- `Jost-400-Book.ttf` — weight `book` — role `chrome`
- `Jost-500-Medium.ttf` — weight `medium` — roles `cover_brow` / `page_title`
- `Jost-700-Bold.ttf` — weight `bold`
- `Jost-800-Heavy.ttf` — weight `heavy` — role `cover_year`

Upstream: https://github.com/indestructible-type/Jost
Specimen: https://indestructibletype.com/Jost.html
SIL OFL 1.1 — `LICENSE` / `AUTHORS`. Reserved Font Name: Jost.

## Type ramp

`TypeInk` is `family` + `weight` + `size`. Painters call `ramp.ink(role)` and
pass those fields to `Plotter.text`. `family` is a closed key
(`TypeFamily = Literal["jost"]` today) so a later dual-font ramp can pick
another catalog family without ripping out the plotter kwarg.

`FontCatalog` is an explicit `(family, weight) → ttf` map, owned by the ramp
and handed to `Fpdf2Plotter` at press time.

| Ramp | chrome | body | cover_brow | page_title | cover_year |
| --- | --- | --- | --- | --- | --- |
| `JostRamp` (default) | Jost Book | Jost Book | Jost Medium | Jost Medium | Jost Heavy |

Cover and header painters take the ramp. Cover specs stay fully literal.

## Context cascade (thesis I)

`TypeContext` is a frozen snapshot with `body` / `chrome` patches. `PlannerLayout`
owns an explicit stack (`push` / `pop` / `with layout.context(...)`). Painters
get `layout.bound()` — a `BoundRamp` pinned to that snapshot. `ink(role)` merges
the role map **over** the current context: role-specified fields win; body and
chrome omit size so a page push can change them without new roles.

| Layer | body size |
| --- | --- |
| root | 8.5 (month day numerals) |
| week page | 11 |
| daily page | 7.6 (slightly smaller than week) |
| mini-month section | 5.3 (year / quarter / daily density) |

No threadlocals. Snapshots are frozen at bind time.

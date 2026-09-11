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

`TypeInk` is `family` + `weight` + `size`. `family` is a closed key
(`TypeFamily = Literal["jost"]` today) so a later dual-font ramp can pick
another catalog family without ripping out the plotter kwarg.

`FontCatalog` is an explicit `(family, weight) → ttf` map, owned by the ramp
and handed to `Fpdf2Plotter` at press time with the ramp itself.

Two ways onto ink — both owned by the ramp, not the plotter:

| Path | Who | API |
| --- | --- | --- |
| Role | cover / header | `ramp.ink(role)` → `family` + `weight` + `size` |
| Face | every other painter (intentional) | `ramp.resolve_face(face, bold, size)` via `FaceBridge` |

`FaceBridge` is a pure table: serif → Medium, sans regular → Book, sans bold
→ Bold. An explicit `weight` wins. Size is carried onto the ink; it is not
a weight axis today. Cover specs stay fully literal (no half-applied chrome).

| Ramp | chrome | cover_brow | page_title | cover_year |
| --- | --- | --- | --- | --- |
| `JostRamp` (default) | Jost Book | Jost Medium | Jost Medium | Jost Heavy |

Later role adoption: add a `TypeRole`, map it on the ramp, switch that
painter from `face=`/`bold=` to `ramp.ink(role)`. Do not grow a massive
role enum in this spike.

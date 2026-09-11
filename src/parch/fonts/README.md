# Planner fonts

Vendored static TTF subsets (fpdf2 cannot load variable fonts). Weights stay
**curated** — not a global Hairline→Black expansion.

## Jost 3.7

- `Jost-400-Book.ttf` — weight `book` — roles `chrome` / `cover_specs` / `nav` / `body`
- `Jost-500-Medium.ttf` — weight `medium` — roles `cover_brow` / `page_title` / `mark`
- `Jost-700-Bold.ttf` — weight `bold` — roles `nav_on` / `emphasis`
- `Jost-800-Heavy.ttf` — weight `heavy` — role `cover_year`

Upstream: https://github.com/indestructible-type/Jost
Specimen: https://indestructibletype.com/Jost.html
SIL OFL 1.1 — `LICENSE` / `AUTHORS`. Reserved Font Name: Jost.

## Type ramp

`TypeInk` is `family` + `weight` + `size`. Painters call `ramp.ink(role)` (or
`.at(size)` when the role default does not fit) and pass the ink to
`Plotter.text`. The plotter does not take `face` or `bold`. `family` is a
closed key (`TypeFamily = Literal["jost"]` today) so a later dual-font ramp
can pick another catalog family without ripping out the plotter argument.

`FontCatalog` is an explicit `(family, weight) → ttf` map, owned by the ramp
and handed to `Fpdf2Plotter` at press time.

| Ramp | chrome | cover_brow | page_title | cover_year | body | emphasis | mark |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `JostRamp` (default) | Jost Book | Jost Medium | Jost Medium | Jost Heavy | Jost Book | Jost Bold | Jost Medium |

Cover, header, and nav take the ramp. Other painters resolve `body` /
`emphasis` / `mark` through the same role map.

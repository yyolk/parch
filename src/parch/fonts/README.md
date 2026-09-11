# Planner fonts

Vendored static TTF subsets (fpdf2 cannot load variable fonts). Weights stay
**curated** — not a global Hairline→Black expansion.

## Jost 3.7

- `Jost-400-Book.ttf` — weight `book` — chrome / nav / body / label / caption
- `Jost-500-Medium.ttf` — weight `medium` — roles `cover_brow` / `page_title`
- `Jost-700-Bold.ttf` — weight `bold` — roles `calendar_num` / `strong`
- `Jost-800-Heavy.ttf` — weight `heavy` — role `cover_year`

Upstream: https://github.com/indestructible-type/Jost
Specimen: https://indestructibletype.com/Jost.html
SIL OFL 1.1 — `LICENSE` / `AUTHORS`. Reserved Font Name: Jost.

## Type ramp

`TypeInk` is `family` + `weight` + `size`. Painters call `ramp.ink(role)` and
pass those fields to `Plotter.text`. Two small ramps share one Jost catalog:
`ChromeRamp` (cover / header / nav) and `BodyRamp` (well). Layout holds both
and passes the relevant object. `family` is a closed key
(`TypeFamily = Literal["jost"]` today) so a later dual-font ramp can pick
another catalog family without ripping out the plotter kwarg.

`FontCatalog` is an explicit `(family, weight) → ttf` map, owned by the ramps
and handed to `Fpdf2Plotter` at press time.

| ChromeRamp | cover_year | cover_brow | page_title | chrome | nav |
| --- | --- | --- | --- | --- | --- |
| `JostChromeRamp` | Jost Heavy 42 | Jost Medium 10 | Jost Medium 11 | Jost Book 7.4 | Jost Book 7.6 |

| BodyRamp | body | label | caption | calendar_num | strong |
| --- | --- | --- | --- | --- | --- |
| `JostBodyRamp` | Jost Book 7 | Jost Book 6.4 | Jost Book 5.8 | Jost Bold 8.5 | Jost Bold 7.2 |

Cover specs stay fully literal.

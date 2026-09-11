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

`TypeInk` is `family` + `weight` + `size`. Components declare the roles they
need with a frozen `TypoNeeds` companion and a `typography()` method. Painters
ask the component, `resolve` through the ramp, then draw — role names sit next
to the data contract, not in geometry code. `family` is a closed key
(`TypeFamily = Literal["jost"]` today) so a later dual-font ramp can pick
another catalog family without ripping out the plotter kwarg.

`FontCatalog` is an explicit `(family, weight) → ttf` map, owned by the ramp
and handed to `Fpdf2Plotter` at press time.

| Ramp | chrome | cover_brow | page_title | cover_year | cover_spec |
| --- | --- | --- | --- | --- | --- |
| `JostRamp` (default) | Jost Book 7.4 | Jost Medium 10 | Jost Medium 11 | Jost Heavy 42 | Jost Book 8.2 |

Cover, header, year, month, week, daily wells, and the projects ticket stub
resolve through component `TypoNeeds`. Jost-only catalog; no signature
inspection.

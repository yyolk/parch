# Planner fonts

Vendored static TTF subsets (fpdf2 cannot load variable fonts). Weights stay
**curated** — not a global Hairline→Black expansion.

## Jost 3.7

- `Jost-400-Book.ttf` — weight `book`
- `Jost-500-Medium.ttf` — weight `medium`
- `Jost-700-Bold.ttf` — weight `bold`
- `Jost-800-Heavy.ttf` — weight `heavy`

Upstream: https://github.com/indestructible-type/Jost
Specimen: https://indestructibletype.com/Jost.html
SIL OFL 1.1 — `LICENSE` / `AUTHORS`. Reserved Font Name: Jost.

## StylePacks (thesis D)

`TypeInk` is `family` + `weight` + `size`. Each section declares a frozen
`StylePack` of the named inks it needs (`CoverPack.year`, `MonthPack.day`,
…). `JostRamp.packs()` stamps every pack from the Jost catalog. 
`PlannerLayout` passes the pack into that section’s painters.

Painters never see `face` / `bold` or a global role enum — only
`pack.body`-style fields. Shared header + nav live on `BaseChrome`,
composed into every well pack. Cover skips chrome.

`FontCatalog` is an explicit `(family, weight) → ttf` map, owned by the
ramp and handed to `Fpdf2Plotter` at press time. Catalog is Jost-only.

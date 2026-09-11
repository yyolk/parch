# Planner fonts

Vendored static TTF subsets (fpdf2 cannot load variable fonts). Weights stay
**curated per family** — not a global Hairline→Black expansion.

## Jost 3.7

- `Jost-400-Book.ttf` — weight `book` — role `chrome`
- `Jost-500-Medium.ttf` — weight `medium` — roles `cover_brow` / `page_title` on `JostRamp`
- `Jost-700-Bold.ttf` — weight `bold`
- `Jost-800-Heavy.ttf` — weight `heavy` — role `cover_year` on `JostRamp`

Upstream: https://github.com/indestructible-type/Jost
Specimen: https://indestructibletype.com/Jost.html
SIL OFL 1.1 — `LICENSE` / `AUTHORS`. Reserved Font Name: Jost.

## Besley 4.0

Regular + Bold only. `book` maps to Regular; `bold` maps to Bold. There is no
Besley Medium or Heavy file — do not invent those keys.

- `Besley-Regular.ttf` — weight `book`
- `Besley-Bold.ttf` — weight `bold`

Upstream: https://github.com/indestructible-type/Besley (`fonts/ttf/`)
Specimen: https://indestructibletype.com/Besley.html
SIL OFL 1.1 — `LICENSE-Besley` / `AUTHORS-Besley`.

## Martian Grotesk

Regular + Bold only (normal width). `book` maps to Regular; `bold` maps to
Bold. There is no Martian Medium or Heavy file — do not invent those keys.

- `martian-grotesk/MartianGrotesk-Regular.ttf` — weight `book` — role `chrome` on `MartianBesleyRamp`
- `martian-grotesk/MartianGrotesk-Bold.ttf` — weight `bold`

Upstream: https://github.com/evilmartians/grotesk
SIL OFL 1.1 — `martian-grotesk/OFL.txt` / `martian-grotesk/AUTHORS.txt`.

## Type ramp

`TypeInk` is `family` + `weight` + `size`. Painters call `ramp.ink(role)` and
pass those fields to `Plotter.text`. Dual-font is a family key, not
`face="sans"|"serif"` overloaded onto one family.

`FontCatalog` is an explicit `(family, weight) → ttf` map, owned by the ramp
and handed to `Fpdf2Plotter` at press time.

| Ramp | chrome | cover_brow | page_title | cover_year |
| --- | --- | --- | --- | --- |
| `JostRamp` (default) | Jost Book | Jost Medium | Jost Medium | Jost Heavy |
| `JostBesleyRamp` | Jost Book | Besley Regular | Besley Bold | Besley Bold |
| `MartianBesleyRamp` | Martian Regular | Besley Regular | Besley Bold | Besley Bold |

`MartianBesleyRamp` mirrors `JostBesleyRamp` with Martian replacing Jost as
chrome. Titles stay Besley so the dual-serif cover story is unchanged.

Swap at press: `parch press … --ramp jost` (default), `--ramp jost-besley`,
or `--ramp martian-besley`.
Or `PlannerLayout(ramp=MartianBesleyRamp())` / `press(..., ramp=MartianBesleyRamp())`.

Cover and header painters take the ramp. Cover specs stay fully literal.

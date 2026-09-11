# Planner fonts

Vendored static TTF subsets (fpdf2 cannot load variable fonts). Weights stay
**curated** — not a global Hairline→Black expansion.

## Jost 3.7

- `Jost-400-Book.ttf` — weight `book` — size-band default + role `chrome`
- `Jost-500-Medium.ttf` — weight `medium` — size-band titles (`≥11`) + role `page_title`
- `Jost-700-Bold.ttf` — weight `bold` — `bold=True` inside body bands
- `Jost-800-Heavy.ttf` — weight `heavy` — size-band display (`≥30`) + role `cover_year`

Upstream: https://github.com/indestructible-type/Jost
Specimen: https://indestructibletype.com/Jost.html
SIL OFL 1.1 — `LICENSE` / `AUTHORS`. Reserved Font Name: Jost.

## Type ramp (thesis F — size-band weights)

`TypeInk` is `family` + `weight` + `size`. Painters call
`ramp.ink(size, role=..., bold=...)` and pass those fields to `Plotter.text`.
They do not pick a cut via `face="serif"` folklore.

`family` is a closed key (`TypeFamily = Literal["jost"]` today) so a later
dual-font ramp can pick another catalog family without ripping out the
plotter kwarg.

`FontCatalog` is an explicit `(family, weight) → ttf` map, owned by the ramp
and handed to `Fpdf2Plotter` at press time.

### Size bands (`JostRamp.bands`)

| Size | Weight |
| --- | --- |
| `≥ 30` | Heavy |
| `≥ 11` | Medium |
| else | Book |

`bold=True` forces Bold when the band is Medium or Book (body). The display
band stays Heavy.

### Role overrides (`JostRamp.roles`)

Small exception set — pins weight, ignores size and bold:

| Role | Weight |
| --- | --- |
| `cover_year` | Heavy |
| `page_title` | Medium |
| `chrome` | Book |

Cover brow / specs / nav / body labels walk the size table. Cover and header
painters take the ramp; other painters receive it from `PlannerLayout`.

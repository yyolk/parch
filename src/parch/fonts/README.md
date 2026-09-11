# Planner fonts

Vendored static TTF subsets (fpdf2 cannot load variable fonts). Weights stay
**curated** — not a global Hairline→Black expansion.

## Jost 3.7

- `Jost-400-Book.ttf` — weight `book` — role `chrome`; slot `copy` + regular
- `Jost-500-Medium.ttf` — weight `medium` — roles `cover_brow` / `page_title`; slot `mark`
- `Jost-700-Bold.ttf` — weight `bold` — slot `copy` + strong
- `Jost-800-Heavy.ttf` — weight `heavy` — role `cover_year`

Upstream: https://github.com/indestructible-type/Jost
Specimen: https://indestructibletype.com/Jost.html
SIL OFL 1.1 — `LICENSE` / `AUTHORS`. Reserved Font Name: Jost.

## Type ramp

`TypeInk` is `family` + `weight` + `size`. Two edges:

- **Roles** — cover / header. `ramp.ink(role)` ignores slots.
- **Slots** — everyone else. `ramp.resolve_slot(slot, emphasis, size)` is the
  typed edge that replaced `TextFace` sans/serif and `resolve_weight`.

`TypeSlot` is a weight-policy enum, not a typeface family:

| Slot | regular | strong |
| --- | --- | --- |
| `copy` | Jost Book | Jost Bold |
| `mark` | Jost Medium | Jost Medium |

`mark` does not promote on emphasis — that used to be the `face="serif"` →
medium folklore. Painters pass resolved ink fields to `Plotter.text`.

`family` is a closed key (`TypeFamily = Literal["jost"]` today) so a later
dual-font ramp can pick another catalog family without ripping out the
plotter kwarg.

`FontCatalog` is an explicit `(family, weight) → ttf` map, owned by the ramp
and handed to `Fpdf2Plotter` at press time.

| Ramp | chrome | cover_brow | page_title | cover_year |
| --- | --- | --- | --- | --- |
| `JostRamp` (default) | Jost Book | Jost Medium | Jost Medium | Jost Heavy |

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

### Closed default table (TypeRole)

Today's four roles stay the closed in-code map. A TypeStep ladder
(display / title / eyebrow / body / chrome / label / caption × emphasis) is
larger; this spike keeps the smaller set. Overlay may change size and/or
weight. Overlay never changes `family`.

| Role | Default ink |
| --- | --- |
| `cover_year` | Jost Heavy 42 |
| `cover_brow` | Jost Medium 10 |
| `page_title` | Jost Medium 11 |
| `chrome` | Jost Book 7.4 |

### Overlay (thesis M)

`TypeOverlay` is frozen pure data: optional `TypePatch(size=, weight=)` per
role. No I/O in validators.

Merge (`defaults ⊕ overlay`, then later overlays):

1. Missing role → keep previous ink.
2. Present role, missing field → that field stays.
3. Present role, explicit field → that field wins.
4. Family is never overlaid.

`EffectiveRamp` is the explicit merged object. Painters only call
`ramp.ink(...)`. They never read the overlay.

Device (`NOMAD.type_overlay`) and/or `press(..., overlay=)` supply overlays.
`press` builds `EffectiveRamp = defaults ⊕ device ⊕ press overlay` and passes
it in. An explicit `ramp=` argument wins the whole object (no compose).
`YearPlanner()` / `PlannerLayout()` with no args still use `JostRamp`
(defaults, no overlay) so tests stay on the closed table.

Nomad overlay (this spike): `chrome` → Medium 8.6; `cover_brow` → Medium 12.

Cover, header, and nav take the ramp. Year minis, month chrome, week
labels/numerals, daily labels, and projects stub/status labels do too
when the layout passes the ramp. Cover specs stay fully literal.

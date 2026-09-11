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

### Overlay stack (thesis Q)

`TypeOverlay` / `TypePatch` are frozen pure data (M spirit). No I/O in
validators. `merge_overlays(*layers)` is the pure merge, bottom → top:

1. `None` layer is skipped (optional house / unused slot).
2. Missing role keeps the lower layer.
3. Present role, missing field keeps the lower field.
4. Present role, explicit field wins (later layer).
5. Family is never implied — `TypePatch` has no family field.

`OverlayStack` names the ordered slots above defaults:

| Layer (bottom → top) | Source | This spike |
| --- | --- | --- |
| 1. defaults | `_JOST` in code | four-role table |
| 2. device | `NOMAD.type_overlay` | chrome Medium 8.6; cover_brow 12 |
| 3. house | optional `house=` | empty / skipped unless supplied |
| 4. press/job | `PRESS_TYPE_OVERLAY` | page_title Bold 13 |
| 5. CLI | — | skipped; `--year`/`--month`/`--day` overlay spec, not type |

`press()` builds the stack and passes one `EffectiveRamp`. Painters only
call `ramp.ink(...)`. An explicit `ramp=` wins the whole object.
`YearPlanner()` / `PlannerLayout()` with no args still use `JostRamp`
(defaults only).

Cover, header, and nav take the ramp. Year minis, month chrome, week
labels/numerals, daily labels, and projects stub/status labels do too
when the layout passes the ramp. Cover specs stay fully literal.

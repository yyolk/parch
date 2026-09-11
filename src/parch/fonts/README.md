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

| Role | Default ink |
| --- | --- |
| `cover_year` | Jost Heavy 42 |
| `cover_brow` | Jost Medium 10 |
| `page_title` | Jost Medium 11 |
| `chrome` | Jost Book 7.4 |

### Overlay (thesis R)

`TypeOverlay` is frozen pure data: optional `TypePatch(size=, weight=)` per
role. Unknown roles, patch keys, or non-Jost weights fail. Overlay never
changes `family`.

Merge (`code defaults ⊕ device ⊕ toml`, then an optional `press(..., overlay=)`):

1. Missing role → keep previous ink.
2. Present role, missing field → that field stays.
3. Present role, explicit field → that field wins.
4. Family is never overlaid.

`EffectiveRamp` is the explicit merged object. Painters only call
`ramp.ink(...)`. Cover and header already do; other painters stay on
literal face/size until a later spike.

Device (`NOMAD.type_overlay`) is the device-owned layer. Nomad stays
identity in this spike. The press job TOML is the yolk-facing knob:

```toml
[typography.overlay.chrome]
size = 9.6
weight = "bold"
```

`examples/mvp.toml` has no typography table (defaults). The spike job is
`examples/mvp-typo-overlay.toml`. `press` builds
`EffectiveRamp = defaults ⊕ device ⊕ spec.type_overlay`. An explicit
`ramp=` argument wins the whole object. `YearPlanner()` / `PlannerLayout()`
with no args still use `JostRamp` so tests stay on the closed table.

Cover specs stay fully literal.

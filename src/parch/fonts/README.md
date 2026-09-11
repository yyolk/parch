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

Today's four roles stay the closed in-code map. Overlay may change size
and/or weight. Overlay never changes `family`.

| Role | Default ink |
| --- | --- |
| `cover_year` | Jost Heavy 42 |
| `cover_brow` | Jost Medium 10 |
| `page_title` | Jost Medium 11 |
| `chrome` | Jost Book 7.4 |

Cover and header painters take the ramp. Cover specs stay fully literal.

### FaceBridge

Unmigrated painters still pass `face` + `bold`. `Fpdf2Plotter` asks
`ramp.resolve_face(face, bold, size)` — a pure table on `FaceBridge`.
An explicit `weight` wins. Size is carried onto the ink; it is not a
weight axis today.

| face | bold | weight | → TypeInk |
| --- | --- | --- | --- |
| `serif` | any | omitted | `jost` / **medium** / *size* |
| `sans` | `False` | omitted | `jost` / **book** / *size* |
| `sans` | `True` | omitted | `jost` / **bold** / *size* |
| any | any | set | `jost` / **that weight** / *size* |

### Overlay

`TypeOverlay` is frozen pure data: optional `TypePatch(size=, weight=)` per
role. No I/O in validators.

Merge (`defaults ⊕ overlay`, then later overlays):

1. Missing role → keep previous ink.
2. Present role, missing field → that field stays.
3. Present role, explicit field → that field wins.
4. Family is never overlaid.

`EffectiveRamp` is the explicit merged object. Painters only call
`ramp.ink(...)` where they already do (cover / header). They never read
the overlay.

`press` builds `EffectiveRamp = defaults ⊕ device overlay ⊕ press overlay`
and passes that one ramp to the book and the plotter. An explicit `ramp=`
argument wins the whole object (no compose). `YearPlanner()` /
`PlannerLayout()` with no args still use `JostRamp` (defaults, no overlay).

Nomad's `type_overlay` is **identity** (`TypeOverlay()`): no size/weight
patches, so specimens stay pixel-identical to tip. The device hook is
wired; a later profile can patch chrome without touching painters.

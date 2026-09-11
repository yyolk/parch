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

### Overlay (thesis U — family-ready)

Thesis M overlaid size/weight only. `TypeInk` already carried `family` for a
later dual-font. This spike extends `TypePatch` so an overlay may set
**optional family** as well:

```python
TypePatch(size: float | None, weight: TypeWeight | None, family: str | None)
TypeOverlay(cover_year=None, cover_brow=None, page_title=None, chrome=None)
```

`family` is a catalog key string. Today only `"jost"` is registered. The
field exists so a future dual-font catalog can plug in without changing
`TypePatch`, painters, or `Plotter.text`.

Merge (`defaults ⊕ overlay`, then later overlays via `compose_overlays`):

1. Missing role → keep previous ink.
2. Present role, missing field → that field stays (including family).
3. Present role, explicit field → that field wins (family overlay wins
   when present).
4. `EffectiveRamp.ink` always calls `catalog.path(family, weight)`.
   Unknown family (or weight) raises `KeyError` there — `TypePatch` does
   **not** pre-validate family. Weight stays curated (`book` / `medium` /
   `bold` / `heavy`).

`EffectiveRamp` is the explicit merged object. Painters only call
`ramp.ink(...)`. They never read the overlay.

Device (`NOMAD.type_overlay`) and/or `press(..., overlay=)` supply overlays.
`press` builds `EffectiveRamp = defaults ⊕ device overlay ⊕ press overlay`.
An explicit `ramp=` argument wins the whole object (no compose).
`YearPlanner()` / `PlannerLayout()` with no args still use `JostRamp`
(defaults, no overlay) so tests stay on the closed table.

Nomad overlay (this spike): `JOST_FAMILY_OVERLAY` — `family="jost"` on every
role, size/weight unset. Specimens still look Jost.

Cover and header take the ramp and already pass `family=` through. Cover
specs stay fully literal.

### Future dual-font catalog — no painter changes

Painters already pass `family=` from `ramp.ink(role)`. To add a second
family later:

1. Vendor static TTFs next to Jost (do **not** add Besley / Martian in
   this spike — stay Jost-only cuts).
2. Register cuts on `FontCatalog`: `("besley", "medium") → Besley-….ttf`.
3. Widen `TypeFamily = Literal["jost", "besley"]`.
4. Overlay `TypePatch(family="besley")` on the roles that should switch,
   or ship a dual-font default table. `EffectiveRamp.ink` resolves
   `catalog.path(family, weight)` — unknown pairs still `KeyError`.
5. Hand the catalog to `Fpdf2Plotter` at press time (already does this).

Painters, `Plotter.text`, and the role table stay as they are. The overlay
API already accepts `family=`.

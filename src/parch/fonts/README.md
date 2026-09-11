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

### Closed default table (TypeRole / TypeStep)

Today's four roles stay the closed in-code map. Overlay keys are the same
closed step set. A TypeStep ladder (display / title / eyebrow / body /
chrome / label / caption × emphasis) is larger; unknown names fail
validation — they do not invent a role.

| Role | Default ink |
| --- | --- |
| `cover_year` | Jost Heavy 42 |
| `cover_brow` | Jost Medium 10 |
| `page_title` | Jost Medium 11 |
| `chrome` | Jost Book 7.4 |

### Overlay schema (thesis S)

`TypeOverlay` is frozen pure data: `schema_version` plus optional
`TypePatch(size=, weight=)` per closed step. Overlay never changes `family`.

`validate_overlay(overlay, defaults)` is **pure** (no I/O). `overlay` may be a
`TypeOverlay` or a mapping (the shape later `parch new` / `parch edit` can
emit). Result is `OverlayOk` or a typed issue:

| Issue | When |
| --- | --- |
| `UnknownStep` | key is not in `defaults` (closed step/role set) |
| `BadWeight` | weight is not `book` / `medium` / `bold` / `heavy` |
| `NonpositiveSize` | size ≤ 0 |
| `SizeOutOfRange` | size outside the step's closed band |
| `VersionMismatch` | `schema_version` is not exactly `OVERLAY_SCHEMA_VERSION` |

**Version policy (today): exact match.** Current `OVERLAY_SCHEMA_VERSION` is
`1`. Missing, older, or newer versions fail. No forward/backward compat yet —
that is what version-lock is for.

Size bands (pt, inclusive):

| Step | Range |
| --- | --- |
| `cover_year` | 18–72 |
| `cover_brow` | 6–24 |
| `page_title` | 8–24 |
| `chrome` | 5–16 |

`get_device` and `press` call `require_overlay` **before** `bind_ramp` builds
`EffectiveRamp`. A bad overlay raises `ConfigError` before paint.

Merge (`defaults ⊕ overlay`, then later overlays):

1. Missing role → keep previous ink.
2. Present role, missing field → that field stays.
3. Present role, explicit field → that field wins.
4. Family is never overlaid.

`EffectiveRamp` is the explicit merged object. Painters only call
`ramp.ink(...)`.

Nomad overlay (this spike): `schema_version = 1`; `chrome` → Medium 8.6;
`cover_brow` → Medium 12.

Cover, header, nav, year minis, and month weekday letters take the ramp.
Cover specs stay fully literal.

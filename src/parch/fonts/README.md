# Planner fonts

Vendored static TTF subsets (fpdf2 cannot load variable fonts). Weights stay
**curated** — not a global Hairline→Black expansion.

## Jost 3.7

- `Jost-400-Book.ttf` — weight `book` — steps `body` / `chrome` / `label` / `caption` (regular)
- `Jost-500-Medium.ttf` — weight `medium` — steps `title` / `eyebrow` (regular)
- `Jost-700-Bold.ttf` — weight `bold` — `strong` emphasis on those steps
- `Jost-800-Heavy.ttf` — weight `heavy` — step `display`

Upstream: https://github.com/indestructible-type/Jost
Specimen: https://indestructibletype.com/Jost.html
SIL OFL 1.1 — `LICENSE` / `AUTHORS`. Reserved Font Name: Jost.

## Type ramp

`TypeInk` is `family` + `weight` + `size`. Migrated painters call
`ramp.ink(step, emphasis="regular")` and pass those fields to `Plotter.text`.
`family` is a closed key (`TypeFamily = Literal["jost"]` today) so a later
dual-font ramp can pick another catalog family without ripping out the plotter
kwarg.

The closed ladder is **design tokens**, not page-semantic roles. Painters pick
from `display` / `title` / `eyebrow` / `body` / `chrome` / `label` / `caption`.
Today's four roles map as `cover_year` → `display`, `cover_brow` → `eyebrow`,
`page_title` → `title`, `chrome` → `chrome`.

`FontCatalog` is an explicit `(family, weight) → ttf` map, owned by the ramp
and handed to `Fpdf2Plotter` at press time.

### Closed scale (TypeStep × emphasis)

| Step | Size | Regular | Strong | Typical use |
| --- | --- | --- | --- | --- |
| `display` | 42 | Heavy | Heavy | Cover year |
| `title` | 11 | Medium | Bold | Page titles; week day numbers |
| `eyebrow` | 10 | Medium | Bold | Cover brow |
| `body` | 8.2 | Book | Bold | Cover specs; month-grid day numbers |
| `chrome` | 7.4 | Book | Bold | Header chips / meta; nav; hours |
| `label` | 6.4 | Book | Bold | Field labels, notes, weekdays, stubs |
| `caption` | 5.4 | Book | Bold | Mini-month days, week numbers, cues |

Nearby one-offs snap to the nearest step. Overlay may change size and/or
weight. Overlay never changes `family`.

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

`TypeOverlay` is frozen pure data: `schema_version` plus optional
`TypePatch(size=, weight=)` per closed `TypeStep` — the same keys `ink()`
takes. No I/O in validators. A patch applies to both emphases of that
step; an explicit weight replaces the emphasis-derived cut. Overlay never
changes `family`.

`validate_overlay(overlay, defaults)` is **pure**. `overlay` may be a
`TypeOverlay` or a mapping (press TOML shape). Result is `OverlayOk` or a
typed issue:

| Issue | When |
| --- | --- |
| `UnknownStep` | key is not in `defaults` (closed TypeStep set; old roles fail) |
| `BadWeight` | weight is not `book` / `medium` / `bold` / `heavy` |
| `NonpositiveSize` | size ≤ 0 |
| `SizeOutOfRange` | size outside the step's closed band |
| `VersionMismatch` | `schema_version` is not exactly `OVERLAY_SCHEMA_VERSION` |

**Version policy (today): exact match.** Current `OVERLAY_SCHEMA_VERSION` is
`1`. Missing, older, or newer versions on a mapping fail. Typed
`TypeOverlay()` defaults to `1`. No forward/backward compat yet.

Size bands (pt, inclusive):

| Step | Range |
| --- | --- |
| `display` | 18–72 |
| `title` | 8–24 |
| `eyebrow` | 6–24 |
| `body` | 6–16 |
| `chrome` | 5–16 |
| `label` | 4–12 |
| `caption` | 4–10 |

Merge (`defaults ⊕ device ⊕ toml ⊕ proof`, then an optional `press(..., overlay=)`):

1. Missing step → keep previous ink.
2. Present step, missing field → that field stays.
3. Present step, explicit field → that field wins.
4. Family is never overlaid.

`get_device` and `press` call `require_overlay` **before** `bind_ramp`
builds `EffectiveRamp`. A bad overlay raises `ConfigError` before paint.

`EffectiveRamp` is the explicit merged object. Painters only call
`ramp.ink(...)`. They never read the overlay.

The press job TOML is the yolk-facing knob:

```toml
[typography.overlay]
schema_version = 1

[typography.overlay.chrome]
size = 9.6
weight = "bold"
```

`examples/mvp.toml` has no typography table (identity / defaults). Side
example: `examples/mvp-typo-overlay.toml`. `press` builds
`EffectiveRamp = defaults ⊕ device ⊕ spec.type_overlay ⊕ proof`. An
explicit `ramp=` argument wins the whole object. `YearPlanner()` /
`PlannerLayout()` with no args still use `JostRamp` (defaults, no overlay).

Nomad's `type_overlay` is **identity** (`TypeOverlay()`): no size/weight
patches. The device hook is wired; a later profile can patch chrome
without touching painters.

### ProofProfile

A separate press-mode layer for on-screen review. Modest size bumps on
TypeStep keys; `display` stays Heavy 42. Weights stay on the closed
defaults. Family is never overlaid. Device overlay is not mutated.

| Step | Default | Proof |
| --- | --- | --- |
| `chrome` | Book 7.4 | Book **9.2** |
| `title` | Medium 11 | Medium **13** |
| `eyebrow` | Medium 10 | Medium **12** |
| `display` | Heavy 42 | unchanged |

Invoke:

```shell
uv run parch proof examples/mvp.toml -o artifacts/mvp/exp-typeramp-proof.pdf
# or
uv run parch press examples/mvp.toml --proof -o artifacts/mvp/exp-typeramp-proof.pdf
```

API: `press(spec, out, proof=True)` or `press(spec, out, proof=ProofProfile())`.
Allowlisted painters already call `ramp.ink(step)`; this PR does not sweep
the FaceBridge backlog.

### Strangler allowlist

`MigratedSurface` / `MIGRATED_SURFACES` lists painter entrypoints that
**must** call `ramp.ink(step)` and emit `family` + `weight` + `size`.
`RecordingPlotter.face_only_text()` fails CI if a listed painter still
emits face-only text.

| Surface | Entrypoint |
| --- | --- |
| cover | `paint_cover` |
| header | `paint_header` |
| nav | `paint_nav` |
| annual / year | `paint_annual` |
| month | `paint_month_grid` |
| week | `paint_week` |
| daily | `paint_daily` |
| projects index | `paint_projects_index` |

**FaceBridge backlog** (documented, not migrated this cut):

- `paint_habit_grid` (+ comparison variants)
- `paint_meetings_index` / `paint_meeting`
- `paint_review_index` / `paint_review`
- `paint_tasks_index` / `paint_task`

Nav is on the allowlist. Quarter dest, project dest, and daily-notes wells
are not. Shared helpers they call (`_paint_mini_month`, `paint_notes`)
speak steps only when the caller passes `ramp=`.

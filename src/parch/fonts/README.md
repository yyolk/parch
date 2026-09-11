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

`TypeOverlay` is frozen pure data: optional `TypePatch(size=, weight=)` per
`TypeStep` — the same keys `ink()` takes. No I/O in validators. A patch
applies to both emphases of that step; an explicit weight replaces the
emphasis-derived cut.

Merge (`defaults ⊕ overlay`, then later overlays):

1. Missing step → keep previous ink.
2. Present step, missing field → that field stays.
3. Present step, explicit field → that field wins.
4. Family is never overlaid.

`EffectiveRamp` is the explicit merged object. Painters only call
`ramp.ink(...)`. They never read the overlay.

`press` builds `EffectiveRamp = defaults ⊕ device overlay ⊕ press overlay`
and passes that one ramp to the book and the plotter. An explicit `ramp=`
argument wins the whole object (no compose). `YearPlanner()` /
`PlannerLayout()` with no args still use `JostRamp` (defaults, no overlay).

Nomad's `type_overlay` is **identity** (`TypeOverlay()`): no size/weight
patches. The device hook is wired; a later profile can patch chrome
without touching painters. `press(..., overlay=)` is a Python-only
test/caller hook, not TOML.

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

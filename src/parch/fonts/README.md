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

`TypeInk` is `family` + `weight` + `size`. Migrated painters call
`ramp.ink(role)` and pass those fields to `Plotter.text`. `family` is a closed
key (`TypeFamily = Literal["jost"]` today) so a later dual-font ramp can pick
another catalog family without ripping out the plotter kwarg.

Unlisted painters keep `face` + `bold` through `ramp.faces` (`FaceBridge` →
`FaceInk`). Dual path is intentional and typed — same explicit ramp, two
methods. No ambient container.

`FontCatalog` is an explicit `(family, weight) → ttf` map, owned by the ramp
and handed to `Fpdf2Plotter` at press time.

| Ramp | chrome | cover_brow | page_title | cover_year | cover_specs |
| --- | --- | --- | --- | --- | --- |
| `JostRamp` (default) | Jost Book 7.4 | Jost Medium 10 | Jost Medium 11 | Jost Heavy 42 | Jost Book 8.2 |

Body roles on migrated wells: `label` / `label_on` 6.4, `quiet` 6.6,
`week_num` 5.8, `micro` 4.3, `grid` / `grid_on` 5.3, `day_num` 8.5,
`week_day` 11, `hour` 7, `ticket` Medium 6.6.

### Strangler allowlist

`MigratedSurface` / `MIGRATED_SURFACES` lists painter entrypoints that must
use `ramp.ink`. A `RecordingPlotter.face_only_text()` assertion fails CI if a
listed painter still emits face-only text ops.

Migrated this spike: `paint_cover`, `paint_header`, `paint_annual`,
`paint_month_grid`, `paint_week`, `paint_daily`, `paint_projects_index`.

### Bridge backlog

These stay on `FaceBridge` (face/bold ops) until a later cut:

- `paint_habit_grid` (and comparison variants)
- `paint_meetings_index` / `paint_meeting`
- `paint_review_index` / `paint_review`
- `paint_tasks_index` / `paint_task`

Nav, quarter dest, project dest, and daily-notes wells are not on the
allowlist either; shared helpers they call may already speak roles.

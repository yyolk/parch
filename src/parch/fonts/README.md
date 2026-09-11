# Planner fonts

Vendored static TTF subsets (fpdf2 cannot load variable fonts). Weights stay
**curated** — not a global Hairline→Black expansion.

## Jost 3.7

- `Jost-400-Book.ttf` — weight `book` — `chrome`, `nav`, `label`, `cue`, …
- `Jost-500-Medium.ttf` — weight `medium` — `cover_brow`, `page_title`, stubs
- `Jost-700-Bold.ttf` — weight `bold` — `nav_on`, day numerals, `cal_month`
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

Thesis J froze 28 roles from a RecordingPlotter audit of the MVP press
(see `AUDIT.md`). `JostRamp.ink(role)` is the only type table. Cover
specs, nav, wells, and chrome all paint by role.

| weight | roles |
| --- | --- |
| Heavy | `cover_year` |
| Medium | `cover_brow` `page_title` `tasks_week` `review_week` `project_stub` `meeting_stub` |
| Bold | `week_day` `review_day` `month_day` `nav_on` `cal_month` `index_month` `cal_day_on` |
| Book | `cover_spec` `nav` `chrome` `hour` `weekday` `label` `week_range` `cue` `review_dow` `status` `cal_day` `priority_mark` `habit_day` `cal_dow` |

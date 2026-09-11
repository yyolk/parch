# Thesis J — MVP text-op audit → frozen TypeRole map

RecordingPlotter over `examples/mvp.toml` (2026 full year, 968 pages, 38523
text ops). Cluster key: `(size to 0.1pt, bold, face, weight, family)`.
Names come from sample strings. Sizes stay exact — clustering discovered
roles; it did not average them.

Serif + bold (no family) resolved to Jost Medium via `resolve_weight`.
Those roles freeze as `medium`.

| n | size | bold | face | resolved | samples | role |
| ---: | ---: | --- | --- | --- | --- | --- |
| 1 | 42.0 | no | — | heavy / jost | 2026 | `cover_year` |
| 967 | 11.0 | no | — | medium / jost | Year, Projects, July, Q1 2026 | `page_title` |
| 371 | 11.0 | yes | sans | bold | 29, 1, 2 (week strip) | `week_day` |
| 1 | 10.0 | no | — | medium / jost | Year Book | `cover_brow` |
| 371 | 9.2 | yes | sans | bold | 29, 1 (review dest) | `review_day` |
| 365 | 8.5 | yes | sans | bold | 1–31 (month grid) | `month_day` |
| 1 | 8.2 | no | sans | book | monday weeks · 118.87 × 158.5 mm | `cover_spec` |
| 9670 | 7.6 | no | sans | book | Quar Mon Habit Proj… | `nav` |
| 967 | 7.6 | yes | sans | bold | Year / active tab | `nav_on` |
| 1133 | 7.4 | no | — | book / jost | Q1–Q4, 2026, 01, W01 | `chrome` |
| 53 | 7.2 | yes | serif | medium | W01 (tasks index) | `tasks_week` |
| 3650 | 7.0 | no | sans | book | 7–16 (schedule hours) | `hour` |
| 53 | 7.0 | yes | serif | medium | W01 (review chips) | `review_week` |
| 473 | 6.6 | no | sans | book | M T W; Mon; Dec | `weekday` |
| 24 | 6.6 | yes | serif | medium | 01–24 (project tickets) | `project_stub` |
| 1601 | 6.4 | no | sans | book | Title Date Agenda Notes Focus Schedule | `label` |
| 401 | 6.4 | yes | sans | bold | Jan… / January (tasks bands) | `cal_month` |
| 53 | 6.2 | no | sans | book | 29 Dec–4 Jan | `week_range` |
| 12 | 6.2 | yes | sans | bold | January (review index) | `index_month` |
| 16 | 6.2 | yes | serif | medium | 01–16 (meeting stubs) | `meeting_stub` |
| 79 | 5.8 | no | sans | book | Date; W01 (month gutter) | `cue` |
| 371 | 5.6 | no | sans | book | Mon–Sun (review dest) | `review_dow` |
| 216 | 5.4 | no | sans | book | Todo / In Progress / Done | `status` |
| 2308 | 5.3 | no | sans | book | muted mini-month days | `cal_day` |
| 11841 | 5.3 | yes | sans | bold | linked / highlight mini days | `cal_day_on` |
| 72 | 5.2 | no | sans | book | P | `priority_mark` |
| 730 | 4.4 | no | sans | book | 1 T 2 F (habit grid) | `habit_day` |
| 2723 | 4.3 | no | sans | book | M T W F S (mini-month) | `cal_dow` |

No 0.5pt merge: 7.6 nav / 7.4 chrome / 7.2 tasks week stay distinct.
Comparison-only habit heads (3.3–3.8) never appeared; no roles for them.

`JOST_ROLES` in `ramp.py` is the freeze. Tests lock the table and that
every MVP text op uses one of those inks.

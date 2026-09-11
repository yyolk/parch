# Planner fonts

Vendored static TTF subsets (fpdf2 cannot load variable fonts). Weights stay
**curated** — not a global Hairline→Black expansion.

## Jost 3.7

- `Jost-400-Book.ttf` — weight `book`
- `Jost-500-Medium.ttf` — weight `medium`
- `Jost-700-Bold.ttf` — weight `bold`
- `Jost-800-Heavy.ttf` — weight `heavy`

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

`PlannerLayout` holds the ramp and threads it into every painter that emits
text. Catalog stays Jost Book / Medium / Bold / Heavy only.

| Role | Weight | Size | Used for |
| --- | --- | --- | --- |
| `cover_year` | heavy | 42 | Cover year |
| `cover_brow` | medium | 10 | Cover “Year Book” |
| `cover_specs` | book | 8.2 | Cover device line |
| `page_title` | medium | 11 | Header title |
| `chrome` | book | 7.4 | Header chip / meta |
| `nav_item` | book | 7.6 | Inactive nav |
| `nav_item_active` | bold | 7.6 | Active nav |
| `label` | book | 6.4 | Field / section labels; unpressed mini-month name |
| `section_heading` | bold | 6.4 | Index month bands; pressed mini-month name |
| `caption` | book | 5.8 | Date cues, W stubs, status, review DOW |
| `body` | book | 7.0 | Schedule hours |
| `weekday` | book | 6.6 | Month / week weekday letters |
| `weekday_mini` | book | 4.3 | Annual mini-month DOW |
| `calendar_num` | bold | 8.5 | Month-grid day numbers |
| `day_num` | bold | 11 | Week-strip day numbers |
| `review_num` | bold | 9.2 | Review day-cue numbers |
| `calendar_num_mini` | book | 5.3 | Mini-month days |
| `calendar_num_mini_on` | bold | 5.3 | Mini-month today / linked days |
| `chip_label` | medium | 7.0 | `Wnn` chips (tasks / review) |
| `index_mark` | medium | 6.4 | Project / meeting stub numbers |
| `habit_num` | book | 4.4 | Habit day numbers (locked transposed) |
| `habit_dow` | book | 4.4 | Habit weekday letters (locked transposed) |
| `clone_mark` | book | 5.2 | Project-card “P” |

`Plotter.text` still accepts `face=` / `bold=` for unmigrated callers.
MVP painters do not use that path.

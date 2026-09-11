# Planner fonts

Vendored static TTF subsets (fpdf2 cannot load variable fonts). Weights stay
**curated** — not a global Hairline→Black expansion.

## Jost 3.7

- `Jost-400-Book.ttf` — weight `book` — steps `chrome` / `caption` / `cell` / `micro`
- `Jost-500-Medium.ttf` — weight `medium` — steps `title` / `brow`
- `Jost-700-Bold.ttf` — weight `bold` — step `body`
- `Jost-800-Heavy.ttf` — weight `heavy` — step `display`

Upstream: https://github.com/indestructible-type/Jost
Specimen: https://indestructibletype.com/Jost.html
SIL OFL 1.1 — `LICENSE` / `AUTHORS`. Reserved Font Name: Jost.

## Type ramp (em-relative)

`TypeInk` is `family` + `weight` + `size`. Painters call `ramp.ink(step)` and
pass those fields to `Plotter.text`. They do not hardcode pt on migrated sites.

`family` is a closed key (`TypeFamily = Literal["jost"]` today) so a later
dual-font ramp can pick another catalog family without ripping out the plotter
kwarg.

`FontCatalog` is an explicit `(family, weight) → ttf` map, owned by the ramp
and handed to `Fpdf2Plotter` at press time.

Root body is **8.5pt** on Nomad (`Device.root_body` / `parch.devices.ROOT_BODY`).
`press` and `YearPlanner.plot` construct `JostRamp(root_body=device.root_body)`.
Size is pure math: `root_body * STEP_RATIO[step]`, except `display`.

| Step | Ratio | Weight | At 8.5pt root |
| --- | --- | --- | --- |
| `body` | 1.0em | Bold | 8.5pt |
| `title` | 1.3em | Medium | 11.05pt |
| `chrome` | 0.87em | Book | 7.395pt |
| `brow` | 10/8.5 em | Medium | 10pt |
| `caption` | 0.75em | Book | 6.375pt |
| `cell` | 0.62em | Book | 5.27pt |
| `micro` | 0.51em | Book | 4.335pt |
| `display` | **fixed 42pt** | Heavy | 42pt |

**`display` is a fixed-pt exception** (cover year). It does not track
`root_body`. 5em of 8.5 would be 42.5pt; the lockup stays 42pt so the cover
numeral does not reflow when the body scale moves. Documented here so a later
ramp can switch it to `5em` if that proves better.

Bump `root_body` and `title` / `chrome` / `body` / `caption` / `cell` /
`micro` / `brow` rescale together. `display` stays 42pt.

Migrated painters: cover, header, nav, year (annual + mini-months), month,
week, daily (schedule / mini / priorities / notes), projects (index + dest).
Cover specs stay fully literal. Meeting / tasks / review / habits unique
labels are still hardcoded pt — shared note/checklist helpers take the ramp
when called from a migrated site.

No ambient container. No fluent DSL. Math lives in `JostRamp.ink`.

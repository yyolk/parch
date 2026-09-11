# Planner fonts

Vendored static TTF subsets (fpdf2 cannot load variable fonts). Weights stay
**curated** — not a global Hairline→Black expansion.

## Jost 3.7

- `Jost-400-Book.ttf` — weight `book` — steps `body` / `chrome` / `label` / `caption` / `micro` (regular)
- `Jost-500-Medium.ttf` — weight `medium` — steps `title` / `eyebrow` (regular)
- `Jost-700-Bold.ttf` — weight `bold` — `strong` emphasis on those steps
- `Jost-800-Heavy.ttf` — weight `heavy` — step `display`

Upstream: https://github.com/indestructible-type/Jost
Specimen: https://indestructibletype.com/Jost.html
SIL OFL 1.1 — `LICENSE` / `AUTHORS`. Reserved Font Name: Jost.

## Type ramp

`TypeRef` is a frozen `TypeStep` + optional `emphasis` + optional `size`.
No family, no weight on the ref. Painters pass `ref=` (or `ink=`).
`Plotter.text` resolves a ref once at the edge via `plotter.ramp`.
`TypeInk` is the resolved `family` + `weight` + `size`. `family` is a closed
key (`TypeFamily = Literal["jost"]` today) so a later dual-font ramp can
pick another catalog family without ripping out the plotter path.

The closed ladder is **design tokens**, not page-semantic roles. Painters pick
from `display` / `title` / `eyebrow` / `body` / `chrome` / `label` / `caption`
/ `micro`. Today's four roles map as `cover_year` → `display`,
`cover_brow` → `eyebrow`, `page_title` → `title`, `chrome` → `chrome`.

Sizes are **em-relative**. Ratio-driven steps are
`pt_from_em(root_body, JOST_RATIOS[step])`. Nomad / default `root_body` is **8.5pt**
(month day numbers). `display` is a **fixed 42pt** exception — it does not
track root, so the cover year does not reflow when the body scale moves.
`Device.root_body` is the device hook; press builds the ramp at that root.
`Em` is a multiple of `root_body`; `Pt` is an absolute PDF point.

`FontCatalog` is an explicit `(family, weight) → ttf` map, owned by the ramp
and handed to `Fpdf2Plotter` at press time.

### Closed scale (TypeStep × emphasis)

At Nomad `root_body` 8.5pt:

| Step | Ratio | Size | Regular | Strong | Typical use |
| --- | --- | --- | --- | --- | --- |
| `display` | *(fixed)* | 42 | Heavy | Heavy | Cover year |
| `title` | 11/8.5 | 11 | Medium | Bold | Page titles; week day numbers |
| `eyebrow` | 10/8.5 | 10 | Medium | Bold | Cover brow |
| `body` | 1.0 | 8.5 | Book | Bold | Cover specs; month-grid day numbers |
| `chrome` | 7.4/8.5 | 7.4 | Book | Bold | Header chips / meta |
| `label` | 6.4/8.5 | 6.4 | Book | Bold | Field labels, notes, weekdays |
| `caption` | 5.4/8.5 | 5.4 | Book | Bold | Clone status; caption-ish cues |
| `micro` | 4.3/8.5 | 4.3 | Book | Bold | Mini-month dow; habit day nums |

A root bump rescales every ratio-driven step together; `display` stays 42.
True one-offs (nav 7.6, schedule hours 7.0, review day 9.2, habit denser
cuts) use `TypeRef.size` as an absolute per-call override — last resort,
not new semantic roles.

Overlay may change size and/or weight. Overlay never changes `family`.

`Plotter.text` is ink|ref only. There is no `face` / `bold` path and no
`FaceBridge`.

### Overlay

`TypeOverlay` is frozen pure data: `schema_version` plus optional
`TypePatch(size=, weight=)` per closed `TypeStep` — the same keys `ink()`
takes. No I/O in validators. A patch applies to both emphases of that
step; an explicit weight replaces the emphasis-derived cut. Overlay never
changes `family`.

**Overlay size is an absolute `Pt` override for that step.** It does not
change `root_body` and does not rescale sibling steps. A chrome
`size=9.6` patch leaves title / body / micro at their em-derived sizes.
`TypeRef.size` wins over both the em size and an overlay size.

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
| `micro` | 2.5–8 |

Merge (`defaults ⊕ device ⊕ toml ⊕ proof`, then an optional `press(..., overlay=)`):

1. Missing step → keep previous ink.
2. Present step, missing field → that field stays.
3. Present step, explicit field → that field wins.
4. Family is never overlaid.

`get_device` and `press` call `require_overlay` **before** `bind_ramp`
builds `EffectiveRamp`. A bad overlay raises `ConfigError` before paint.

`EffectiveRamp` is the explicit merged object. Painters call
`ramp.ink(...)` or pass `TypeRef`; they never read the overlay.

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
`EffectiveRamp = defaults ⊕ device ⊕ spec.type_overlay ⊕ proof` at
`device.root_body`. An explicit `ramp=` argument wins the whole object.
`YearPlanner()` / `PlannerLayout()` with no args still use `JostRamp`
(default root 8.5, no overlay).

Nomad's `type_overlay` is **identity** (`TypeOverlay()`): no size/weight
patches. Nomad `root_body` is 8.5pt. The device hook is wired; a later
profile can patch chrome or bump root without touching painters.

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
Every text-emitting painter is on the allowlist and speaks steps.

### Strangler allowlist

`MigratedSurface` / `MIGRATED_SURFACES` lists every text-emitting painter
entrypoint. Each must pass `TypeRef` / ink and emit `family` + `weight` +
`size`. `RecordingPlotter.face_only_text()` fails CI if a listed painter
still emits text without a resolved family.

Layout wells (cover, header, nav, annual, quarter, month, week, daily,
daily notes, projects index/dest, habit, meetings, review, tasks) are listed.
Shared helpers (`_paint_mini_month`, `_paint_note_box`,
`_paint_checklist_box`, clone tracks) always ink.

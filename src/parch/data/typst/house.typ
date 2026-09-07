#let page-margin(side, toolbar-edge: none, toolbar-clearance: none, writing-clearance: none, rail-clearance: 0mm, bezel: none) = (
  top: if toolbar-edge == top { toolbar-clearance } else { 0mm },
  bottom: if bezel != none { bezel } else { 0mm },
  left: if bezel != none { bezel } else if side == right { writing-clearance } else { rail-clearance },
  right: if bezel != none { bezel } else if side == left { writing-clearance } else { rail-clearance },
)

// House paper is a tiling fill. dotted_centered, lined_fill, and
// task_fill are the live tiles; lined_well is the full-bleed writing field.
#let dotted_centered(regular_height: none) = tiling(
  size: (regular_height, regular_height),
  // place(center + horizon) does not resolve against a tiling cell
  // (circles sit on the origin and clip to quarters). Size the cell
  // first so align can actually center the 0.141mm circle.
  block(
    width: regular_height,
    height: regular_height,
    align(
      center + horizon,
      circle(
        radius: 0.141mm,
        fill: black
      )
    )
  ),
)

#let lined_fill(regular_height: none, regular_stroke: none, paint: luma(130)) = tiling(
  size: (regular_height, regular_height),
  line(
    start: (0pt, regular_height - 0.15mm),
    end: (regular_height, regular_height - 0.15mm),
    stroke: regular_stroke + paint,
  ),
)

#let task_tick(regular_stroke: none) = square(
  size: 0.8em,
  fill: none,
  stroke: regular_stroke + black,
)

#let task_fill(page-width: none, regular_height: none, regular_stroke: none) = tiling(
  size: (page-width, regular_height),
  relative: "self",
  block(
    width: page-width,
    height: regular_height,
    stroke: (bottom: regular_stroke + black),
    align(
      horizon + start,
      task_tick(regular_stroke: regular_stroke),
    )
  ),
)

#let padded_link(padding: none, target, content) = box(
  inset: -padding,
  link(target)[#box(inset: padding, content)]
)

// Hit square: transparent fill so the link covers the box, not only the strokes.
#let contents_bars(thick_stroke: none, size: none) = {
  let cap = 0.7 * size
  let wide = 0.844 * size
  let gap = (cap - 5 * thick_stroke) / 4
  box(
    width: wide,
    height: wide,
    fill: luma(0%, 0%),
    align(center + horizon, stack(
      dir: ttb,
      spacing: gap,
      line(length: wide, stroke: thick_stroke + black),
      line(length: wide, stroke: thick_stroke + black),
      line(length: wide, stroke: thick_stroke + black),
      line(length: wide, stroke: thick_stroke + black),
      line(length: wide, stroke: thick_stroke + black),
    ))
  )
}

#let lead_pair(mark, title, spacing: 6pt) = stack(
  dir: ltr,
  spacing: spacing,
  align(horizon, mark),
  align(horizon, title),
)

// Title shrinks in the 1fr when it overflows; skip scale when it fits.
#let trail_heading(title, mark, shrink: false) = grid(
  columns: (1fr, auto),
  align: horizon + start,
  if shrink {
    layout(size => context {
      let wanted = measure(title)
      if wanted.width == 0pt or wanted.width <= size.width {
        title
      } else {
        // Natural-size box first so a leftover h1 digit cannot wrap (weekly "4").
        scale(
          size.width / wanted.width * 100%,
          origin: start + horizon,
          reflow: true,
          box(width: wanted.width, height: wanted.height, title),
        )
      }
    })
  } else {
    title
  },
  mark,
)

#let mos_frame(side, mos, well, mos-width: none, column-gutter: none) = if side == left {
  grid(
    columns: (mos-width, 1fr),
    rows: 1fr,
    column-gutter: column-gutter,
    mos,
    well,
  )
} else {
  grid(
    columns: (1fr, mos-width),
    rows: 1fr,
    column-gutter: column-gutter,
    well,
    mos,
  )
}

// Descender floor: heading row grows by stroke air. No clip.
#let well_frame(heading, body, heading-height: none, row-gutter: none, heading-stroke: none) = {
  let gap = if heading-stroke == none { 0pt } else { stroke(heading-stroke).thickness }
  grid(
    columns: 1fr,
    rows: (heading-height + gap, 1fr),
    row-gutter: row-gutter,
    grid.cell(
      align: horizon,
      inset: (bottom: gap),
      {
        set text(bottom-edge: "descender")
        box(width: 100%, height: 100%, heading)
      },
    ),
    body,
  )
}

// MOS strip: one column, n 1fr rows; rotate bare cells only.
#let mos_tabs(stroke: none, turn: none, columns: none, ..cells) = {
  let gap = if stroke == none { 0pt } else { std.stroke(stroke).thickness }
  let items = cells.pos()
  set text(bottom-edge: "descender")
  table(
    stroke: stroke,
    inset: gap,
    columns: 1fr,
    rows: (1fr,) * items.len(),
    align: horizon + center,
    ..items.map(c => if c.func() == table.cell {
      table.cell(
        fill: c.at("fill", default: none),
        align: horizon + center,
        c.body,
      )
    } else {
      rotate(turn, origin: center + horizon, c)
    }),
  )
}

// Q/month split; house owns the 1fr/3fr tracks.
#let mos_rail(quarters, months, reverse: false, gutter: none) = grid(
  columns: 1fr,
  rows: if reverse { (3fr, 1fr) } else { (1fr, 3fr) },
  row-gutter: gutter,
  ..if reverse { (months, quarters) } else { (quarters, months) },
)

// Year dests bind once; per page is highlights only.
#let mos_strip(months: none, quarters: none, highlight-months: (), highlight-quarters: (), reverse: false, show-quarters: true, stroke: none, turn: none, gutter: none, padding: none) = {
  // months/quarters: array of (dest, label). dest is none when the page does not exist.
  // highlight-* are dests. show-quarters: false is habits (months only).
  // Full-cell hit: width 100% + v(1fr) sandwich; rotate the ink inside.
  let tabs(items, highlights) = mos_tabs(
    stroke: stroke,
    turn: turn,
    ..items.map(item => {
      let dest = item.at(0)
      let label = item.at(1)
      let on = highlights.contains(dest)
      let ink = if on { text(white)[#label] } else { label }
      let seated = box(width: 100%, fill: if on { black } else { luma(0%, 0%) }, {
        v(1fr)
        align(center, rotate(turn, origin: center + horizon, ink))
        v(1fr)
      })
      let body = if dest != none { padded_link(padding: 0pt, dest, seated) } else { seated }
      if on {
        table.cell(fill: black, body)
      } else {
        table.cell(body)
      }
    }),
  )
  let month-tabs = tabs(months, highlight-months)
  if show-quarters {
    mos_rail(tabs(quarters, highlight-quarters), month-tabs, reverse: reverse, gutter: gutter)
  } else {
    month-tabs
  }
}

// Week cell is always first in each 8-cell row. MOS-right moves it to the end.
#let _order_week_rows(side, cells) = if side == left {
  cells
} else {
  let out = ()
  for i in range(0, cells.len(), step: 8) {
    let row = cells.slice(i, count: 8)
    out += row.slice(1) + (row.at(0),)
  }
  out
}

// Name + weekdays are auto; week-rows are equal 1fr tracks. Never `rows: 1fr`
// alone (5-week vs 6-week months would move the weekday rule). Columns are
// 8×1fr. Name is caller-owned (colspan 8). House owns the MOS week rail.
#let month_grid(
  side,
  name,
  inset: none,
  week-rows: 6,
  hline-stroke: none,
  ..rows,
) = grid(
  align: center + horizon,
  inset: inset,
  stroke: (x, _) => if x == (if side == left { 1 } else { 7 }) { (left: hline-stroke) },
  columns: (1fr,) * 8,
  rows: (auto, auto) + (1fr,) * week-rows,
  grid.hline(y: 1, stroke: hline-stroke),
  grid.hline(y: 2, stroke: hline-stroke),
  name,
  .._order_week_rows(side, rows.pos()),
)

// Monthly-page calendar. Rows stay caller-owned (live week count). House
// owns week-col seating. Same side token as mos_frame. Block height is
// 1fr so leftover 1fr body rows receive the outer calendar track.
#let month_weeks(side, rows: none, week-col: none, stroke: none, ..cells) = block(
  width: 100%,
  height: 1fr,
  grid(
    stroke: stroke,
    columns: if side == left { (week-col,) + (1fr,) * 7 } else { (1fr,) * 7 + (week-col,) },
    rows: rows,
    .._order_week_rows(side, cells.pos()),
  ),
)

// Full-bleed writing field. Parent is well_frame's 1fr body (bounded).
// Tiling fill. Optional tile-height floors to whole tiles; remnant is blank.
#let lined_well(pattern, tile-height: none) = if tile-height == none {
  box(width: 100%, height: 100%, fill: pattern)
} else {
  layout(size => {
    let n = calc.floor(size.height / tile-height)
    grid(
      columns: 1fr,
      rows: (tile-height,) * n + (1fr,),
      ..((box(width: 100%, height: 100%, fill: pattern),) * n),
      [],
    )
  })
}

// Header on auto; bottom inset is the rule's own thickness. Clipped
// lined_well fills the 1fr.
// Not exported — week_matrix is the only weekly overview entry.
#let week_cell(header, header-stroke: none, pattern: none) = {
  let gap = if header-stroke == none { 0pt } else { stroke(header-stroke).thickness }
  grid(
    columns: 1fr,
    rows: (auto, 1fr),
    grid.cell(
      inset: (bottom: gap),
      stroke: (bottom: header-stroke),
      text(bottom-edge: "descender", header),
    ),
    box(
      width: 100%,
      height: 100%,
      clip: true,
      inset: (top: 0.25em, bottom: 0.25em),
      lined_well(pattern),
    ),
  )
}

// 3×3 of equal 1fr tracks. column-gutter only (no row-gutter). Notes is
// colspan: 2 on the eighth cell so the first column stays one vertical.
#let week_matrix(
  column-gutter: none,
  header-stroke: none,
  pattern: none,
  ..contents,
) = {
  let headers = contents.pos()
  let painted = headers.map(header => week_cell(
    header,
    header-stroke: header-stroke,
    pattern: pattern,
  ))
  grid(
    columns: (1fr, 1fr, 1fr),
    rows: (1fr, 1fr, 1fr),
    column-gutter: column-gutter,
    ..painted.slice(0, 7),
    grid.cell(colspan: 2, painted.at(7)),
  )
}

// Parent is well_frame's 1fr body (bounded). House owns the 3fr/5fr
// split. Same side token as mos_frame.
#let daily_well(side, hours, writing, column-gutter: none) = if side == left {
  grid(columns: (3fr, 5fr), rows: 1fr, column-gutter: column-gutter, hours, writing)
} else {
  grid(columns: (5fr, 3fr), rows: 1fr, column-gutter: column-gutter, writing, hours)
}

// Parent is well_frame's 1fr body (bounded). House owns the 2fr/3fr
// split. Same side token as mos_frame.
#let quarter_well(side, months, pad, column-gutter: none) = if side == left {
  grid(columns: (2fr, 3fr), rows: 1fr, column-gutter: column-gutter, months, pad)
} else {
  grid(columns: (3fr, 2fr), rows: 1fr, column-gutter: column-gutter, pad, months)
}

// Scribe Hyperpaper explor: 5mm air + soft ~10mm crumb track (grows, no clip).
// Nomad does not call this. Header owns top air (page-margin top stays 0mm).
// Contents is the rail-adjacent auto track (flips with section_rail). Crumb
// stays in the well 1fr. Q/month chips sit on the far side, away from the rail.
// Shrink is trail_heading(..., shrink: true) at the call site.
#let nav_header(home, crumb, far, height: 10mm, air: 5mm, stroke: none, side: left) = {
  let cells = if side == left { (home, crumb, far) } else { (far, crumb, home) }
  grid(
    columns: 1fr,
    rows: (air, auto),
    [],
    grid(
      columns: (auto, 1fr, auto),
      align: horizon + start,
      column-gutter: 2mm,
      inset: (x: 2mm, y: 1mm),
      ..cells,
    ),
    grid.hline(y: 2, stroke: stroke),
  )
}

// Scribe section rail: rotated section links, full-cell hit, pad from page edge.
// pad insets the link (not only the ink) so MOS-right annots stay off the
// Kindle page-turn strip. items: array of (dest, label). highlight is a dest.
#let section_rail(items, highlight: none, stroke: none, turn: none, pad: 4mm, side: left) = {
  let edge = if side == left { (left: pad) } else { (right: pad) }
  mos_tabs(
    stroke: stroke,
    turn: turn,
    ..items.map(item => {
      let dest = item.at(0)
      let label = item.at(1)
      let on = dest != none and dest == highlight
      let ink = if on { text(white)[#label] } else { label }
      let seated = box(width: 100%, height: 100%, fill: luma(0%, 0%), {
        v(1fr)
        align(center, rotate(turn, origin: center + horizon, ink))
        v(1fr)
      })
      let hit = if dest != none { padded_link(padding: 0pt, dest, seated) } else { seated }
      let body = box(width: 100%, inset: edge, hit)
      if on {
        table.cell(fill: black, body)
      } else {
        table.cell(body)
      }
    }),
  )
}

// Nomad Topband. MOS / Scribe do not call these. Icons are Lucide-style
// strokes; -on is inversion via the chip fill, not a second path set.
#let _strip-ink(on) = if on { white } else { black }
#let _strip-sw = 0.22mm

#let icon-menu(on: false, size: 3.4mm) = {
  let paint = _strip-ink(on)
  let w = size * 0.70
  box(width: size, height: size, align(center + horizon, stack(
    dir: ttb,
    spacing: size * 0.18,
    line(length: w, stroke: _strip-sw + paint),
    line(length: w, stroke: _strip-sw + paint),
    line(length: w, stroke: _strip-sw + paint),
  )))
}

#let icon-cal(on: false, size: 3.4mm) = {
  let paint = _strip-ink(on)
  let w = size * 0.70
  let h = size * 0.62
  box(width: size, height: size, align(center + horizon, {
    rect(width: w, height: h, stroke: _strip-sw + paint, radius: 0.15mm)
    place(top + center, dy: h * 0.18, circle(radius: 0.18mm, fill: paint))
  }))
}

#let icon-q(on: false, size: 3.4mm) = {
  let paint = _strip-ink(on)
  let w = size * 0.68
  box(width: size, height: size, align(center + horizon, stack(
    dir: ttb,
    spacing: size * 0.10,
    line(length: w, stroke: _strip-sw + paint),
    line(length: w, stroke: _strip-sw + paint),
    line(length: w, stroke: _strip-sw + paint),
  )))
}

#let icon-mon(on: false, size: 3.4mm) = {
  let paint = _strip-ink(on)
  let w = size * 0.70
  let h = size * 0.62
  let cell = w / 4
  box(width: size, height: size, align(center + horizon, {
    rect(width: w, height: h, stroke: _strip-sw + paint, radius: 0.15mm)
    place(dx: (size - w) / 2 + cell * 1.2, dy: (size - h) / 2 + h * 0.42, {
      for i in range(2) {
        for j in range(2) {
          place(dx: i * cell * 0.9, dy: j * cell * 0.7, circle(radius: 0.16mm, fill: paint))
        }
      }
    })
  }))
}

#let icon-wk(on: false, size: 3.4mm) = {
  let paint = _strip-ink(on)
  let w = size * 0.70
  let h = size * 0.62
  box(width: size, height: size, align(center + horizon, {
    rect(width: w, height: h, stroke: _strip-sw + paint, radius: 0.15mm)
    place(top + center, dy: h * 0.32, stack(
      dir: ttb,
      spacing: h * 0.18,
      circle(radius: 0.16mm, fill: paint),
      circle(radius: 0.16mm, fill: paint),
      circle(radius: 0.16mm, fill: paint),
    ))
  }))
}

#let icon-day(on: false, size: 3.4mm) = {
  let paint = _strip-ink(on)
  box(width: size, height: size, align(center + horizon, {
    circle(radius: size * 0.16, stroke: _strip-sw + paint)
    for i in range(8) {
      let turn = i * 45deg
      place(center + horizon, rotate(turn, line(
        start: (0mm, size * 0.24),
        end: (0mm, size * 0.36),
        stroke: _strip-sw + paint,
      )))
    }
  }))
}

#let icon-tasks(on: false, size: 3.4mm) = {
  let paint = _strip-ink(on)
  let w = size * 0.62
  box(width: size, height: size, align(center + horizon, stack(
    dir: ttb,
    spacing: size * 0.14,
    ..range(3).map(_ => stack(
      dir: ltr,
      spacing: size * 0.12,
      circle(radius: 0.18mm, fill: paint),
      line(length: w * 0.72, stroke: _strip-sw + paint),
    )),
  )))
}

#let icon-habits(on: false, size: 3.4mm) = {
  let paint = _strip-ink(on)
  let d = size * 0.10
  box(width: size, height: size, align(center + horizon, grid(
    columns: (auto, auto, auto),
    rows: (auto, auto, auto),
    gutter: size * 0.12,
    ..((circle(radius: d / 2, fill: paint),) * 9),
  )))
}

#let icon-review(on: false, size: 3.4mm) = {
  let paint = _strip-ink(on)
  let w = size * 0.58
  let h = size * 0.70
  box(width: size, height: size, align(center + horizon, {
    rect(width: w, height: h, stroke: _strip-sw + paint, radius: 0.15mm)
    place(center + horizon, stack(
      dir: ttb,
      spacing: h * 0.16,
      line(length: w * 0.55, stroke: _strip-sw + paint),
      line(length: w * 0.55, stroke: _strip-sw + paint),
      line(length: w * 0.40, stroke: _strip-sw + paint),
    ))
  }))
}

#let strip-icon(name, on: false, size: 3.4mm) = {
  if name == "contents" { icon-menu(on: on, size: size) }
  else if name == "cal" { icon-cal(on: on, size: size) }
  else if name == "q" { icon-q(on: on, size: size) }
  else if name == "mon" { icon-mon(on: on, size: size) }
  else if name == "wk" { icon-wk(on: on, size: size) }
  else if name == "day" { icon-day(on: on, size: size) }
  else if name == "tasks" { icon-tasks(on: on, size: size) }
  else if name == "habits" { icon-habits(on: on, size: size) }
  else if name == "review" { icon-review(on: on, size: size) }
  else { [] }
}

// items: array of (dest, key). dest is none when the page does not exist.
#let section-strip(items, active: none, height: 6.5mm, stroke: none) = {
  let gap = 0.55mm
  let n = items.len()
  if n == 0 { [] } else {
    grid(
      columns: (1fr,) * n,
      rows: height,
      column-gutter: gap,
      ..items.map(item => {
        let dest = item.at(0)
        let name = item.at(1)
        let on = dest != none and name == active
        let seated = box(
          width: 100%,
          height: 100%,
          fill: if on { black } else { luma(0%, 0%) },
          stroke: stroke,
          align(center + horizon, strip-icon(name, on: on)),
        )
        if dest != none { padded_link(padding: 0pt, dest, seated) } else { seated }
      }),
    )
  }
}

// items: array of (dest, label, on)
#let tempo-bar(items, height: 6mm, stroke: none) = {
  let n = items.len()
  if n == 0 { [] } else {
    grid(
      columns: (1fr,) * n,
      rows: height,
      column-gutter: 0.8mm,
      ..items.map(item => {
        let dest = item.at(0)
        let label = item.at(1)
        let on = item.at(2)
        let ink = if on { text(fill: white, label) } else { label }
        let seated = box(
          width: 100%,
          height: 100%,
          fill: if on { black } else { luma(0%, 0%) },
          stroke: stroke,
          align(center + horizon, ink),
        )
        if dest != none { padded_link(padding: 0pt, dest, seated) } else { seated }
      }),
    )
  }
}

// Topband under the toolbar dead zone. No side MOS.
// rows: strip → hair → optional tempo → hair → crumb → hair → 1fr body
#let page-shell(strip, body, tempo: none, title: none, year: none, stroke: none) = {
  let crumb = if title == none {
    []
  } else {
    block(
      width: 100%,
      inset: (top: 1.2mm, bottom: 1.0mm),
      grid(
        columns: (1fr, auto),
        align: horizon,
        title,
        if year == none { [] } else { year },
      ),
    )
  }
  grid(
    columns: 1fr,
    rows: (auto, auto, auto, auto, auto, auto, 1fr),
    strip,
    line(length: 100%, stroke: stroke),
    if tempo == none { [] } else { tempo },
    if tempo == none { [] } else { line(length: 100%, stroke: stroke) },
    crumb,
    if title == none { [] } else { line(length: 100%, stroke: stroke) },
    body,
  )
}

// Nomad daily: schedule 2fr | rail 1fr, notes floor. MOS keeps daily_well.
#let nomad_daily_well(schedule, rail, notes, column-gutter: none, notes-height: 20mm) = grid(
  columns: 1fr,
  rows: (1fr, notes-height),
  row-gutter: 1.2mm,
  grid(
    columns: (2fr, 1fr),
    rows: 1fr,
    column-gutter: column-gutter,
    schedule,
    rail,
  ),
  notes,
)

// Nomad weekly: 7×1fr day bands + 18mm week-notes floor. One ink hair
// per band. No rule above Week notes. MOS keeps week_matrix.
#let nomad_week_band(header, stroke: none) = {
  grid(
    columns: 1fr,
    rows: (auto, 1fr),
    block(
      inset: (top: 0.35mm, bottom: 0.2mm),
      text(weight: "bold", bottom-edge: "descender", header),
    ),
    align(horizon, line(length: 100%, stroke: stroke)),
  )
}

#let nomad_week_bands(stroke: none, notes-height: 18mm, ..contents) = {
  let headers = contents.pos()
  let days = calc.max(headers.len() - 1, 0)
  let day-headers = headers.slice(0, count: days)
  let notes = if headers.len() > days { headers.at(days) } else { [] }
  grid(
    columns: 1fr,
    rows: (1fr,) * days + (notes-height,),
    ..range(days).map(i => {
      let band = nomad_week_band(day-headers.at(i), stroke: stroke)
      // Hair between days only — not above Week notes.
      if i + 1 < days { grid.cell(stroke: (bottom: stroke), band) } else { band }
    }),
    nomad_week_band(notes, stroke: stroke),
  )
}

// Nomad monthly: 7×6 day cells + short Month notes floor. MOS keeps month_weeks.
#let nomad_month_well(calendar, notes, notes-height: 20mm) = grid(
  columns: 1fr,
  rows: (1fr, notes-height),
  calendar,
  notes,
)

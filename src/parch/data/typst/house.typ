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

// Nomad Topband. MOS / Scribe do not call these. Glyphs are locked SVGs
// (icons/*.svg + icons/*-on.svg). Notes is not a chip.
//
// Spacing contract (named tokens — Typst 0.15 default rhythm, not 0pt):
#let bezel = 3mm
#let toolbar = 8mm
#let top-air = 0.4mm
#let chrome-h = 6.5mm
#let tempo-h = 6mm
#let hair = 0.4pt
#let chip-gutter = 1.2mm
#let chip-inset-x = 0.9mm
#let chip-inset-y = 1.2mm
#let icon-chip-inset-x = 0.6mm
#let icon-chip-inset-y = 1.1mm
#let strip-tempo-gap = 0mm
#let well-top = 2.5mm
#let rhythm = 1.2em

#let _strip-id(name) = if name == "contents" { "menu" } else { name }

#let icon-chip(id, active: false, expand: true, stroke: hair) = {
  let src = if active { "icons/" + id + "-on.svg" } else { "icons/" + id + ".svg" }
  let edge = if stroke != none { stroke } else { hair }
  box(
    width: if expand { 100% } else { auto },
    inset: (x: icon-chip-inset-x, y: icon-chip-inset-y),
    fill: if active { black } else { white },
    stroke: edge + black,
    align(center + horizon, image(src, height: 3.1mm)),
  )
}

#let strip-icon(name, on: false, size: 3.4mm) = {
  icon-chip(_strip-id(name), active: on, expand: false)
}

// items: array of (dest, key). dest is none when the page does not exist.
#let section-strip(items, active: none, height: chrome-h, stroke: none) = {
  let edge = if stroke != none { stroke } else { hair }
  let n = items.len()
  if n == 0 { [] } else {
    grid(
      columns: (1fr,) * n,
      rows: (auto,),
      column-gutter: chip-gutter,
      align: (center, horizon),
      ..items.map(item => {
        let dest = item.at(0)
        let name = item.at(1)
        let on = dest != none and name == active
        let seated = icon-chip(_strip-id(name), active: on, expand: true, stroke: edge)
        if dest != none { padded_link(padding: 0pt, dest, seated) } else { seated }
      }),
    )
  }
}

// Discrete tempo chip. Natural height from chip-inset-y — not tempo-h.
#let chip(label, active: false, dest: none, expand: false, stroke: hair) = {
  let edge = if stroke != none { stroke } else { hair }
  let body = box(
    width: if expand { 100% } else { auto },
    inset: (x: chip-inset-x, y: chip-inset-y),
    fill: if active { black } else { white },
    stroke: edge + black,
    align(center + horizon,
      text(
        font: "Liberation Sans",
        size: 7.5pt,
        fill: if active { white } else { black },
        weight: if active { "bold" } else { "regular" },
      )[#label],
    ),
  )
  if dest != none { padded_link(padding: 0pt, dest, body) } else { body }
}

// items: already-built chip(...) nodes from emit.
#let tempo-row(items) = {
  let n = items.len()
  if n == 0 { [] } else {
    grid(
      columns: (1fr,) * n,
      rows: (auto,),
      column-gutter: chip-gutter,
      align: (center, horizon),
      ..items,
    )
  }
}

// Topband under the toolbar dead zone. No side MOS.
// Chrome only when present: strip → hair → tempo → hair → crumb → hair → body.
// strip/tempo/title of none emit no phantom hairlines (cover is strip-none).
#let page-shell(strip, body, tempo: none, title: none, year: none, stroke: none) = {
  set text(font: "Libertinus Serif")
  set par(spacing: rhythm)
  set block(spacing: rhythm)
  let crumb = if title == none {
    []
  } else {
    block(
      width: 100%,
      inset: (top: 1.2mm, bottom: 1.0mm),
      {
        set text(font: "Libertinus Serif")
        grid(
          columns: (1fr, auto),
          align: horizon,
          title,
          if year == none { [] } else { year },
        )
      },
    )
  }
  grid(
    columns: 1fr,
    rows: (auto, 1fr),
    row-gutter: 0pt,
    {
      if strip != none {
        v(top-air)
        block(width: 100%, inset: (x: bezel, y: strip-tempo-gap), strip)
        line(length: 100%, stroke: stroke)
      }
      if tempo != none {
        block(width: 100%, inset: (x: bezel, y: strip-tempo-gap), tempo)
        line(length: 100%, stroke: stroke)
      }
      if title != none {
        crumb
        line(length: 100%, stroke: stroke)
      }
    },
    box(width: 100%, height: 100%, inset: (top: well-top), body),
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

// Nomad weekly: 7×1fr day bands + 18mm week-notes floor. Each band
// and the Week-notes floor fill with multiple 3.8mm ink hairs (not
// one centered rule). No rule above Week notes. MOS keeps week_matrix.
#let nomad_week_hairs(stroke: none, tile: 3.8mm) = layout(size => {
  let n = calc.max(calc.floor(size.height / tile), 0)
  box(width: size.width, height: size.height, clip: true, {
    for i in range(n) {
      place(top + start, dy: (i + 1) * tile, line(
        length: size.width,
        stroke: stroke,
      ))
    }
  })
})

#let nomad_week_band(header, stroke: none, tile: 3.8mm) = {
  grid(
    columns: 1fr,
    rows: (auto, 1fr),
    block(
      inset: (top: 0.35mm, bottom: 0.2mm),
      text(weight: "bold", bottom-edge: "descender", header),
    ),
    box(
      width: 100%,
      height: 100%,
      clip: true,
      nomad_week_hairs(stroke: stroke, tile: tile),
    ),
  )
}

#let nomad_week_bands(stroke: none, notes-height: 18mm, tile: 3.8mm, ..contents) = {
  let headers = contents.pos()
  let days = calc.max(headers.len() - 1, 0)
  let day-headers = headers.slice(0, count: days)
  let notes = if headers.len() > days { headers.at(days) } else { [] }
  // Air between days only — no cell bottom stroke (that doubled in-band hairs).
  grid(
    columns: 1fr,
    rows: (1fr,) * days + (notes-height,),
    row-gutter: 0.8mm,
    ..day-headers.map(h => nomad_week_band(h, stroke: stroke, tile: tile)),
    nomad_week_band(notes, stroke: stroke, tile: tile),
  )
}

// Daily rail glance. Fonts stay fixed so day-h → height is linear.
#let mini-month(name, start-wd: 3, days: 31, highlight: none, day-h: 2.6mm, weeks: auto, compact: false) = {
  let day-sz = if compact { 5.5pt } else { 6.5pt }
  let wd-sz = if compact { 4.8pt } else { 5.5pt }
  let title-sz = if compact { 6.5pt } else { 7pt }
  let title-gap = if compact { 0.3mm } else { 0.45mm }
  let rg = if compact { calc.max(0.25mm, day-h * 0.18) } else { calc.max(0.35mm, day-h * 0.16) }
  let wd-h = day-h * 0.72
  set text(font: "Liberation Sans", size: day-sz)
  let wd = ("M", "T", "W", "T", "F", "S", "S")
  let cells = ()
  for i in range(start-wd) { cells.push(none) }
  for d in range(1, days + 1) { cells.push(d) }
  let wks = if weeks == auto {
    calc.max(5, calc.ceil(cells.len() / 7))
  } else { weeks }
  while cells.len() < wks * 7 { cells.push(none) }
  block(width: 100%, {
    text(weight: "bold", size: title-sz)[#name]
    v(title-gap)
    grid(
      columns: (1fr,) * 7,
      column-gutter: 0pt,
      row-gutter: rg,
      ..wd.map(w => box(
        width: 100%,
        height: wd-h,
        align(center + horizon, text(size: wd-sz, fill: luma(40%), weight: "bold")[#w]),
      )),
      ..cells.map(c => {
        let inner = if c == none {
          []
        } else if highlight != none and c == highlight {
          box(
            width: 88%,
            height: 88%,
            fill: black,
            radius: 0.2mm,
            align(center + horizon, text(fill: white, size: day-sz, weight: "bold")[#c]),
          )
        } else {
          text(size: day-sz)[#c]
        }
        box(width: 100%, height: day-h, align(center + horizon, inner))
      }),
    )
  })
}

#let mini-month-fit(name, start-wd: 3, days: 31, highlight: none, compact: false) = {
  box(width: 100%, height: 100%, clip: true, layout(size => {
    let wks = 6
    let title-sz = if compact { 6.5pt } else { 7pt }
    let title-gap = if compact { 0.3mm } else { 0.45mm }
    let rg-k = if compact { 0.18 } else { 0.16 }
    let fixed = title-sz + title-gap
    let coef = 0.72 + wks + rg-k * (1 + wks)
    let day-h = calc.max(2.0mm, (size.height - fixed) / coef)
    mini-month(
      name,
      start-wd: start-wd,
      days: days,
      highlight: highlight,
      day-h: day-h,
      weeks: wks,
      compact: compact,
    )
  }))
}

// Nomad annual/quarter glance. Locked densify — not LittleCalendar / month_grid.
#let year-month(name, start-wd: 3, days: 31) = {
  set text(font: "Liberation Sans")
  box(width: 100%, height: 100%, clip: true, layout(size => {
    let wks = 6
    let title-sz = 6.5pt
    let wd-sz = 4.5pt
    let day-sz = 5.5pt
    let title-gap = 0.3mm
    let rg-k = 0.28
    let fixed = title-sz + title-gap
    let coef = 0.6 + wks + rg-k * wks
    let day-h = calc.max(1.8mm, (size.height - fixed) / coef)
    let wd-h = day-h * 0.6
    let rg = day-h * rg-k
    let wd = ("M", "T", "W", "T", "F", "S", "S")
    let cells = ()
    for i in range(start-wd) { cells.push(none) }
    for d in range(1, days + 1) { cells.push(d) }
    while cells.len() < wks * 7 { cells.push(none) }
    block(width: 100%, {
      text(weight: "bold", size: title-sz)[#name]
      v(title-gap)
      grid(
        columns: (1fr,) * 7,
        column-gutter: 0pt,
        row-gutter: rg,
        ..wd.map(w => box(
          width: 100%,
          height: wd-h,
          align(center + horizon, text(size: wd-sz, fill: luma(45%), weight: "bold")[#w]),
        )),
        ..cells.map(c => box(
          width: 100%,
          height: day-h,
          align(center + horizon, if c == none { [] } else { text(size: day-sz)[#c] }),
        )),
      )
    })
  }))
}

#let nomad_year_grid(..cells) = grid(
  columns: (1fr, 1fr, 1fr),
  rows: (1fr, 1fr, 1fr, 1fr),
  column-gutter: 2.4mm,
  row-gutter: 1.5mm,
  ..cells.pos().map(c => box(
    width: 100%,
    height: 100%,
    clip: true,
    inset: (x: 0.25mm, y: 0.15mm),
    c,
  )),
)

// Nomad quarterly: 26mm month strip + Focus / Notes wells. MOS keeps quarter_well.
#let nomad_quarter_well(months, focus, notes, strip-height: 26mm) = grid(
  columns: 1fr,
  rows: (strip-height, 0.9fr, 1.2fr),
  row-gutter: 1.5mm,
  months,
  focus,
  notes,
)

// Nomad monthly: 7×6 day cells + short Month notes floor. MOS keeps month_weeks.
#let nomad_month_well(calendar, notes, notes-height: 20mm) = grid(
  columns: 1fr,
  rows: (1fr, notes-height),
  calendar,
  notes,
)

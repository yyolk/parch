# Jost 3.7

Vendored static TTF subset (fpdf2 cannot load the variable font):

- `Jost-400-Book.ttf` — `face="sans"` regular (text / UI) — role `chrome`
- `Jost-700-Bold.ttf` — `face="sans"` + `bold=True` (emphasis)
- `Jost-500-Medium.ttf` — `face="serif"` titles — roles `cover_brow` / `page_title`
- `Jost-800-Heavy.ttf` — cover year — role `cover_year`

Cover and header painters take an explicit `TypeRamp` (`ramp.ink(role) → TypeInk`)
and no longer hardcode `weight="heavy"` / face policy. `PlannerLayout` builds a
`JostRamp` and passes it in. Plotter still accepts `weight=`. Cover specs stay
literal until a dedicated role exists.

Upstream: https://github.com/indestructible-type/Jost  
Specimen: https://indestructibletype.com/Jost.html

SIL Open Font License 1.1 — see `LICENSE` and `AUTHORS`.
Reserved Font Name: Jost.

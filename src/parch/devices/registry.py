"""Registered MVP devices — SuperNote Nomad and Kindle Scribe (1st gen)."""

from dataclasses import dataclass
from typing import Literal

from parch import ConfigError
from parch.fonts.ramp import ROOT_BODY, Pt
from parch.geom import Rect

type ToolbarEdge = Literal["top", "none"]

# Keep in lockstep with parch.layouts.planner.painters.NAV_H.
# Registry cannot import painters (cycle). The strip sits on bottom_clearance.
_NAV_H = 8.0


@dataclass(frozen=True, slots=True)
class Device:
    """Physical page. Toolbar slab is reserved; it is not a writing well."""

    id: str
    name: str
    ppi: int
    page_width: float
    page_height: float
    width_px: int
    height_px: int
    toolbar_edge: ToolbarEdge
    toolbar_clearance: float
    writing_clearance: float
    bottom_clearance: float
    root_body: Pt = ROOT_BODY

    @property
    def content_top(self) -> float:
        """First Y chrome/content may occupy."""
        match self.toolbar_edge:
            case "top":
                return self.toolbar_clearance
            case _:
                return 0.0

    def toolbar_slab(self) -> Rect | None:
        match self.toolbar_edge:
            case "top" if self.toolbar_clearance > 0:
                return Rect(0.0, 0.0, self.page_width, self.toolbar_clearance)
            case _:
                return None

    def content_frame(self) -> Rect:
        """Chrome + wells: below toolbar, above nav strip + bottom OS chrome.

        Side inset is writing_clearance. Bottom inset is the nav strip plus
        bottom_clearance — not writing_clearance, which used to overlap the strip.
        """
        top = self.content_top
        margin = self.writing_clearance
        nav_band = _NAV_H + self.bottom_clearance
        return Rect(
            x=margin,
            y=top,
            w=self.page_width - 2 * margin,
            h=self.page_height - top - nav_band,
        )


# 1404×1872 @ 300 PPI → 118.87×158.50 mm. Toolbar top 8 mm.
# Body root 8.5pt: month day nums land on pre-snap 8.5; ratios follow.
NOMAD = Device(
    id="supernote-nomad",
    name="SuperNote Nomad",
    ppi=300,
    page_width=118.87,
    page_height=158.5,
    width_px=1404,
    height_px=1872,
    toolbar_edge="top",
    toolbar_clearance=8.0,
    writing_clearance=4.0,
    bottom_clearance=0.0,
    root_body=ROOT_BODY,
)

# 1860×2480 @ 300 PPI → 157.48×209.97 mm. No toolbar chrome; writing clearance 4 mm.
# Same ROOT_BODY as Nomad — type calibration knob is later, not this PR.
SCRIBE = Device(
    id="kindle-scribe",
    name="Kindle Scribe (1st gen)",
    ppi=300,
    page_width=157.48,
    page_height=209.97,
    width_px=1860,
    height_px=2480,
    toolbar_edge="none",
    toolbar_clearance=0.0,
    writing_clearance=4.0,
    bottom_clearance=10.0,  # measured Send-to-Kindle: hits below 10 mm miss; 10–20 mm solid.
    root_body=ROOT_BODY,
)

_KNOWN = {
    NOMAD.id: NOMAD,
    "nomad": NOMAD,
    SCRIBE.id: SCRIBE,
    "scribe": SCRIBE,
}


def known_device_ids() -> tuple[str, ...]:
    """Canonical device ids (aliases omitted)."""
    return (NOMAD.id, SCRIBE.id)


def get_device(spec: str) -> Device:
    key = spec.strip().lower()
    if key not in _KNOWN:
        known = ", ".join(known_device_ids())
        raise ConfigError(f"unknown device {spec!r}; MVP knows {known}")
    return _KNOWN[key]

"""Registered devices — SuperNote Nomad and Kindle Scribe (1st gen)."""

from dataclasses import dataclass, replace

from parch import ConfigError
from parch.fonts.ramp import ROOT_BODY, Pt
from parch.geom import Rect

NAV_H = 8.0


@dataclass(frozen=True, slots=True)
class Device:
    """Physical page. ``top_clearance`` is reserved; it is not a writing well.

    ``top_clearance == 0`` means no top band. Spec may override this per press
    (``top_clearance = 0``) without forking the registered Device.
    """

    id: str
    name: str
    ppi: int
    page_width: float
    page_height: float
    width_px: int
    height_px: int
    top_clearance: float
    writing_clearance: float
    bottom_clearance: float
    root_body: Pt = ROOT_BODY

    @property
    def content_top(self) -> float:
        """First Y chrome/content may occupy."""
        return self.top_clearance

    def page_rect(self) -> Rect:
        """Full physical page — no writing_clearance, top, or nav inset."""
        return Rect(0.0, 0.0, self.page_width, self.page_height)

    def content_frame(self) -> Rect:
        """Chrome + wells: below top clearance, above nav strip + bottom OS chrome.

        Side inset is writing_clearance. Bottom inset is the nav strip plus
        bottom_clearance — not writing_clearance, which used to overlap the strip.
        """
        top = self.content_top
        margin = self.writing_clearance
        nav_band = NAV_H + self.bottom_clearance
        return Rect(
            x=margin,
            y=top,
            w=self.page_width - 2 * margin,
            h=self.page_height - top - nav_band,
        )


# 1404×1872 @ 300 PPI → 118.87×158.50 mm. Top clearance 8 mm.
# Body root 8.5pt: month day nums land on pre-snap 8.5; ratios follow.
NOMAD = Device(
    id="supernote-nomad",
    name="SuperNote Nomad",
    ppi=300,
    page_width=118.87,
    page_height=158.5,
    width_px=1404,
    height_px=1872,
    top_clearance=8.0,
    writing_clearance=4.0,
    bottom_clearance=0.0,
    root_body=ROOT_BODY,
)

# 1860×2480 @ 300 PPI → 157.48×209.97 mm. Writing clearance 4 mm.
# Top 8 mm is a measured chrome inset (not a physical Kindle toolbar):
# Send-to-Kindle taps are solid from ~8 mm; paint_header chip/meta sit below that floor.
# Header hits are few (chip/meta only). Spec ``top_clearance = 0`` drops the band —
# older presses without it often worked. Bottom 10 mm is separate.
# Same ROOT_BODY as Nomad — type calibration knob is later, not this PR.
SCRIBE = Device(
    id="kindle-scribe",
    name="Kindle Scribe (1st gen)",
    ppi=300,
    page_width=157.48,
    page_height=209.97,
    width_px=1860,
    height_px=2480,
    top_clearance=8.0,
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


def get_device(spec: str, *, top_clearance: float | None = None) -> Device:
    """Registered Device. ``top_clearance`` overrides the reserved top band.

    Omit (or ``None``) keeps the device default. ``0`` means no top band.
    """
    key = spec.strip().lower()
    if key not in _KNOWN:
        known = ", ".join(known_device_ids())
        raise ConfigError(f"unknown device {spec!r}; known devices: {known}")
    device = _KNOWN[key]
    if top_clearance is None:
        return device
    return replace(device, top_clearance=top_clearance)

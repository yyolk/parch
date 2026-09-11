"""SuperNote Nomad — the only MVP device."""

from dataclasses import dataclass, field
from typing import Literal

from parch import ConfigError
from parch.fonts.ramp import TypeOverlay, jost_defaults, require_overlay
from parch.geom import Rect

MM_PER_INCH = 25.4

type ToolbarEdge = Literal["top", "none"]


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
    type_overlay: TypeOverlay = field(default_factory=TypeOverlay)

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
        """Chrome + wells: below the toolbar, inset by writing_clearance."""
        top = self.content_top
        margin = self.writing_clearance
        return Rect(
            x=margin,
            y=top,
            w=self.page_width - 2 * margin,
            h=self.page_height - top - margin,
        )


# Identity overlay — no size/weight patches. Press still builds
# EffectiveRamp = defaults ⊕ this overlay (⊕ toml if present ⊕ proof if on)
# so the device hook is wired without a visual chrome bump vs greenfield tip.
# ProofProfile is a separate press-mode layer; it does not mutate this overlay.
NOMAD_TYPE_OVERLAY = TypeOverlay()

# 1404×1872 @ 300 PPI → 118.87×158.50 mm. Toolbar top 8 mm.
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
    type_overlay=NOMAD_TYPE_OVERLAY,
)

_KNOWN = {
    NOMAD.id: NOMAD,
    "nomad": NOMAD,
}


def get_device(spec: str) -> Device:
    key = spec.strip().lower()
    if key not in _KNOWN:
        raise ConfigError(f"unknown device {spec!r}; MVP knows supernote-nomad")
    device = _KNOWN[key]
    require_overlay(device.type_overlay, jost_defaults())
    return device

"""SuperNote Nomad — the only MVP device."""

from dataclasses import dataclass
from typing import Literal

from parch import ConfigError
from parch.fonts.ramp import ROOT_BODY, Pt
from parch.geom import Rect

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
        """Chrome + wells: below the toolbar, inset by writing_clearance."""
        top = self.content_top
        margin = self.writing_clearance
        return Rect(
            x=margin,
            y=top,
            w=self.page_width - 2 * margin,
            h=self.page_height - top - margin,
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
    root_body=ROOT_BODY,
)

_KNOWN = {
    NOMAD.id: NOMAD,
    "nomad": NOMAD,
}


def known_device_ids() -> tuple[str, ...]:
    """Canonical device ids (aliases omitted)."""
    ids: list[str] = []
    for device in _KNOWN.values():
        if device.id not in ids:
            ids.append(device.id)
    return tuple(ids)


def get_device(spec: str) -> Device:
    key = spec.strip().lower()
    if key not in _KNOWN:
        raise ConfigError(f"unknown device {spec!r}; MVP knows supernote-nomad")
    return _KNOWN[key]

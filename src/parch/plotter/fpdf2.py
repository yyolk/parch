"""Single fpdf2-backed plotter. Catalog-driven families, fake small-caps."""

from pathlib import Path
from typing import override

from fpdf import FPDF

from parch.devices.nomad import Device
from parch.fonts.catalog import FontCatalog, jost_catalog
from parch.fonts.ramp import TypeInk
from parch.geom import Rect
from parch.plotter.protocol import Plotter, TextAlign

SMCP_SCALE = 0.76
SMCP_TRACK_EM = 0.14


def _pt_mm(pt: float) -> float:
    return pt * 25.4 / 72.0


def _level(gray: float) -> int:
    return max(0, min(255, int(round(gray * 255))))


class Fpdf2Plotter(Plotter):
    def __init__(self, device: Device, catalog: FontCatalog | None = None) -> None:
        self.device = device
        self.catalog = jost_catalog() if catalog is None else catalog
        self.pdf = FPDF(unit="mm", format=(device.page_width, device.page_height))
        self.pdf.set_auto_page_break(auto=False, margin=0)
        self.pdf.set_margins(0, 0, 0)
        self.pdf.set_compression(True)
        for (family, weight), path in self.catalog.cuts.items():
            self.pdf.add_font(self.catalog.register_name(family, weight), "", str(path))
        self.pdf.set_font(self.catalog.register_name("jost", "book"), size=10)
        self.pdf.set_text_color(0)
        self.pdf.set_draw_color(0)

    def _register_name(self, ink: TypeInk) -> str:
        return self.catalog.register_name(ink.family, ink.weight)

    def _ink(self, gray: float) -> None:
        level = _level(gray)
        self.pdf.set_text_color(level)

    def _draw(self, gray: float) -> None:
        self.pdf.set_draw_color(_level(gray))

    def _smcp_width(self, text: str, size: float, register_as: str) -> float:
        chars = text.upper()
        if not chars:
            return 0.0
        self.pdf.set_font(register_as, "", size * SMCP_SCALE)
        track = _pt_mm(size * SMCP_SCALE) * SMCP_TRACK_EM
        return sum(self.pdf.get_string_width(ch) for ch in chars) + track * (len(chars) - 1)

    def _draw_smcp(
        self,
        box: Rect,
        content: str,
        *,
        ink: TypeInk,
        align: TextAlign,
        gray: float,
    ) -> None:
        register_as = self._register_name(ink)
        tw = self._smcp_width(content, ink.size, register_as)
        cap = _pt_mm(ink.size * SMCP_SCALE) * 0.72
        baseline = box.y + (box.h + cap) / 2.0 - 0.12
        match align:
            case "center":
                tx = box.x + (box.w - tw) / 2.0
            case "right":
                tx = box.x + box.w - tw
            case _:
                tx = box.x
        self._ink(gray)
        self.pdf.set_font(register_as, "", ink.size * SMCP_SCALE)
        track = _pt_mm(ink.size * SMCP_SCALE) * SMCP_TRACK_EM
        chars = content.upper()
        last = len(chars) - 1
        cx = tx
        for i, ch in enumerate(chars):
            self.pdf.text(cx, baseline, ch)
            cx += self.pdf.get_string_width(ch) + (track if i < last else 0)

    @override
    def begin_page(self) -> None:
        self.pdf.add_page()

    @override
    def reserve_dest(self, name: str) -> None:
        self.pdf.set_link(name=name)

    @override
    def add_dest(self, name: str) -> None:
        self.pdf.add_link(name=name)

    @override
    def rect(
        self,
        box: Rect,
        *,
        stroke: bool = True,
        fill: bool = False,
        stroke_width: float = 0.2,
        fill_gray: float = 0.92,
        stroke_gray: float = 0.0,
    ) -> None:
        match (stroke, fill):
            case (False, False):
                return
            case (True, True):
                style = "DF"
            case (False, True):
                style = "F"
            case (True, False):
                style = "D"
        self.pdf.set_line_width(stroke_width)
        self.pdf.set_fill_color(_level(fill_gray))
        self._draw(stroke_gray)
        self.pdf.rect(box.x, box.y, box.w, box.h, style=style)

    @override
    def line(
        self,
        x1: float,
        y1: float,
        x2: float,
        y2: float,
        *,
        stroke_width: float = 0.2,
        stroke_gray: float = 0.0,
    ) -> None:
        self.pdf.set_line_width(stroke_width)
        self._draw(stroke_gray)
        self.pdf.line(x1, y1, x2, y2)

    @override
    def text(
        self,
        box: Rect,
        content: str,
        *,
        ink: TypeInk,
        align: TextAlign = "left",
        gray: float = 0.0,
        small_caps: bool = False,
    ) -> None:
        if not content:
            return
        if small_caps:
            self._draw_smcp(box, content, ink=ink, align=align, gray=gray)
            return
        register_as = self._register_name(ink)
        self.pdf.set_font(register_as, "", ink.size)
        self._ink(gray)
        cap = _pt_mm(ink.size) * 0.72
        baseline = box.y + (box.h + cap) / 2.0 - 0.12
        tw = self.pdf.get_string_width(content)
        match align:
            case "center":
                tx = box.x + (box.w - tw) / 2.0
            case "right":
                tx = box.x + box.w - tw
            case _:
                tx = box.x
        self.pdf.text(tx, baseline, content)

    @override
    def link(self, box: Rect, dest: str) -> None:
        target = dest if dest.startswith("#") else f"#{dest}"
        self.pdf.link(box.x, box.y, box.w, box.h, target)

    @override
    def finish(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        self.pdf.output(str(path))

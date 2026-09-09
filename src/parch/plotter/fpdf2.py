"""Single fpdf2-backed plotter."""

from pathlib import Path

from fpdf import FPDF

from parch.devices.nomad import Device
from parch.geom import Rect
from parch.plotter.protocol import TextAlign


class Fpdf2Plotter:
    def __init__(self, device: Device) -> None:
        self.device = device
        self.pdf = FPDF(unit="mm", format=(device.page_width, device.page_height))
        self.pdf.set_auto_page_break(auto=False, margin=0)
        self.pdf.set_margins(0, 0, 0)
        self.pdf.set_font("helvetica", size=10)
        self.pdf.set_text_color(0)
        self.pdf.set_draw_color(0)

    def begin_page(self) -> None:
        self.pdf.add_page()

    def reserve_dest(self, name: str) -> None:
        self.pdf.set_link(name=name)

    def add_dest(self, name: str) -> None:
        self.pdf.add_link(name=name)

    def rect(
        self,
        box: Rect,
        *,
        stroke: bool = True,
        fill: bool = False,
        stroke_width: float = 0.2,
        fill_gray: float = 0.92,
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
        level = max(0, min(255, int(round(fill_gray * 255))))
        self.pdf.set_fill_color(level)
        self.pdf.set_draw_color(0)
        self.pdf.rect(box.x, box.y, box.w, box.h, style=style)

    def line(
        self,
        x1: float,
        y1: float,
        x2: float,
        y2: float,
        *,
        stroke_width: float = 0.2,
    ) -> None:
        self.pdf.set_line_width(stroke_width)
        self.pdf.set_draw_color(0)
        self.pdf.line(x1, y1, x2, y2)

    def text(
        self,
        box: Rect,
        content: str,
        *,
        size: float = 10,
        align: TextAlign = "left",
        bold: bool = False,
    ) -> None:
        match align:
            case "center":
                code = "C"
            case "right":
                code = "R"
            case _:
                code = "L"
        style = "B" if bold else ""
        self.pdf.set_font("helvetica", style=style, size=size)
        line_h = size * 0.352778
        y = box.y + max(0.0, (box.h - line_h) / 2)
        self.pdf.set_xy(box.x, y)
        self.pdf.cell(box.w, line_h, content, align=code)

    def link(self, box: Rect, dest: str) -> None:
        target = dest if dest.startswith("#") else f"#{dest}"
        self.pdf.link(box.x, box.y, box.w, box.h, target)

    def finish(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        self.pdf.output(str(path))

from parch.calendar import month_name
from parch.components import CoverTitle
from parch.devices import get_device
from parch.sections.page import NavItem, Page
from parch.spec import Spec


class CoverSection:
    def __init__(self, spec: Spec, *, cta_dest: str | None = None) -> None:
        self.spec = spec
        self.cta_dest = cta_dest or spec.year_dest

    def pages(self) -> list[Page]:
        spec = self.spec
        label = f"{month_name(spec.month)} {spec.year}"
        landing = self.cta_dest
        return [
            Page(
                dest=spec.cover_dest,
                kind="cover",
                title=str(spec.year),
                nav=(NavItem(str(spec.year), landing),),
                components=(
                    CoverTitle(
                        year=spec.year,
                        subtitle=spec.title,
                        device_name=get_device(spec.device).name,
                        cta_label=f"{label}  >",
                        cta_dest=landing,
                    ),
                ),
            )
        ]

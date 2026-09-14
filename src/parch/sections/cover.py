from parch.calendar import month_name
from parch.components import CoverTitle
from parch.devices import get_device
from parch.sections.page import NavItem, Page
from parch.spec import Spec


class CoverSection:
    def __init__(self, spec: Spec, *, cta_dest: str | None = None) -> None:
        self.spec = spec
        self.cta_dest = cta_dest

    def pages(self) -> list[Page]:
        spec = self.spec
        cta_dest = self.cta_dest or spec.cover_cta_dest
        label = (
            spec.title if spec.projects_hub else f"{month_name(spec.month)} {spec.year}"
        )
        return [
            Page(
                dest=spec.cover_dest,
                kind="cover",
                title=str(spec.year),
                nav=(NavItem(str(spec.year), cta_dest),),
                components=(
                    CoverTitle(
                        year=spec.year,
                        subtitle=spec.title,
                        device_name=get_device(spec.device).name,
                        cta_label=f"{label}  >",
                        cta_dest=cta_dest,
                    ),
                ),
            )
        ]

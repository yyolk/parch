from parch.calendar import month_name
from parch.components import CoverTitle
from parch.sections.page import NavItem, Page
from parch.spec import Spec


class CoverSection:
    def __init__(self, spec: Spec) -> None:
        self.spec = spec

    def pages(self) -> list[Page]:
        spec = self.spec
        label = f"{month_name(spec.month)} {spec.year}"
        return [
            Page(
                dest=spec.cover_dest,
                kind="cover",
                title=str(spec.year),
                nav=(NavItem(month_name(spec.month), spec.month_dest),),
                components=(
                    CoverTitle(
                        year=spec.year,
                        subtitle=spec.title,
                        device_name="SuperNote Nomad",
                        cta_label=f"{label}  >",
                        cta_dest=spec.month_dest,
                    ),
                ),
            )
        ]

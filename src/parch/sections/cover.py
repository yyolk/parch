from parch.calendar import month_name
from parch.components import CoverTitle
from parch.sections.page import NavItem, Page
from parch.spec import Spec


class CoverSection:
    def __init__(
        self,
        spec: Spec,
        *,
        landing_dest: str | None = None,
        eyebrow: str = "Year Book",
        specs_lead: str | None = None,
    ) -> None:
        self.spec = spec
        self.landing_dest = landing_dest
        self.eyebrow = eyebrow
        self.specs_lead = specs_lead

    def pages(self) -> list[Page]:
        spec = self.spec
        landing = self.landing_dest or spec.year_dest
        label = f"{month_name(spec.month)} {spec.year}"
        specs_lead = (
            f"{spec.week_start} weeks" if self.specs_lead is None else self.specs_lead
        )
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
                        device_name="SuperNote Nomad",
                        cta_label=f"{label}  >",
                        cta_dest=landing,
                        eyebrow=self.eyebrow,
                        specs_lead=specs_lead,
                    ),
                ),
            )
        ]

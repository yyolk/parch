from parch.calendar import month_name
from parch.components import CoverTitle
from parch.sections.page import NavItem, Page, PageKind
from parch.spec import Spec


class CoverSection:
    """Cover — TOML title is year-planner brow, or sibling display headline when set."""

    def __init__(
        self,
        spec: Spec,
        *,
        landing_dest: str | None = None,
        eyebrow: str = "Year Book",
        specs_lead: str | None = None,
        display_title: str | None = None,
    ) -> None:
        title = spec.title
        self.spec = spec
        self.landing_dest = landing_dest
        self.specs_lead = specs_lead
        if display_title is not None:
            self.display_title = title if title is not None else display_title
            self.eyebrow = eyebrow
        else:
            self.display_title = None
            self.eyebrow = title if title is not None else eyebrow

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
                kind=PageKind.COVER,
                title=str(spec.year),
                nav=(NavItem(str(spec.year), landing),),
                components=(
                    CoverTitle(
                        year=spec.year,
                        cta_label=f"{label}  >",
                        cta_dest=landing,
                        eyebrow=self.eyebrow,
                        specs_lead=specs_lead,
                        display_title=self.display_title,
                    ),
                ),
            )
        ]

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
        landing = (
            spec.projects_index_dest if spec.book == "projects" else spec.year_dest
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
                    ),
                ),
            )
        ]

"""Composite section — cover → projects index/dests only."""

from parch.sections.cover import CoverSection
from parch.sections.page import NavItem, Page
from parch.sections.projects import ProjectsSection
from parch.spec import Spec


class ProjectsNotebookSection:
    """Wrap ``CoverSection`` + ``ProjectsSection`` as one section.

    Cover CTA / year tap lands on the projects index. Projects pages
    get a Proj-only strip so ``strip_items`` does not invent Year/Quar
    dests that this book never reserves.
    """

    def __init__(self, spec: Spec) -> None:
        self.spec = spec

    def pages(self) -> list[Page]:
        spec = self.spec
        landing = spec.projects_index_dest
        nav = (NavItem("Proj", landing),)
        return [
            *CoverSection(spec, landing=landing, eyebrow="Projects").pages(),
            *ProjectsSection(spec, nav=nav).pages(),
        ]

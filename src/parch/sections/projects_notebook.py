"""Projects notebook — composite section: CoverSection then ProjectsSection."""

from parch.sections.cover import CoverSection
from parch.sections.page import Page
from parch.sections.projects import ProjectsSection
from parch.spec import Spec


class ProjectsNotebookSection:
    """One section whose ``pages()`` is only the existing cover + projects sections."""

    def __init__(self, spec: Spec) -> None:
        self.spec = spec

    def pages(self) -> list[Page]:
        spec = self.spec
        return [
            *CoverSection(spec).pages(),
            *ProjectsSection(spec).pages(),
        ]

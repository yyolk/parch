"""Page header slab — title / meta / chip plus the ink contract.

Layout builds this from ``Page`` fields. It is not seated in ``page.components``.
"""

from dataclasses import dataclass

from parch.fonts.ramp import TypeInk, TypeRamp, TypeRole


@dataclass(frozen=True, slots=True)
class HeaderTypoNeeds:
    title: TypeRole = "page_title"
    chrome: TypeRole = "chrome"

    def roles(self) -> tuple[TypeRole, ...]:
        return (self.title, self.chrome)

    def resolve(self, ramp: TypeRamp) -> "HeaderInk":
        return HeaderInk(title=ramp.ink(self.title), chrome=ramp.ink(self.chrome))


@dataclass(frozen=True, slots=True)
class HeaderInk:
    title: TypeInk
    chrome: TypeInk


@dataclass(frozen=True, slots=True)
class HeaderChrome:
    title: str
    meta: str
    chip: str = ""

    def typography(self) -> HeaderTypoNeeds:
        return HeaderTypoNeeds()

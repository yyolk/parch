"""One page per day in the configured range."""

from typing import Any

from parch.calendar import walk
from parch.i18n import I18n
from parch.mos.configurator import Configurator
from parch.mos.manifest import Manifest
from parch.compose.page_data import HeadingMark, PageData
from parch.mos.pages.daily import Daily as DailyPage
from parch.mos.nomad_nav import nomad_topband
from parch.mos.scribe_nav import scribe_hyperpaper_nav
from parch.sections._shared import _side_menu_position, heading_and_well


class Daily:
    ID = "daily"

    def __init__(self, section_name: str, i18n: I18n, configurator: Configurator, **params: Any) -> None:
        self.section_name = section_name
        self.i18n = i18n
        self.configurator = configurator
        self.params = params

    def register(self, manifest: Manifest) -> None:
        for day in self._range():
            manifest.register_source(day.id)

    def pages(self, manifest: Manifest) -> list[PageData]:
        out = []
        side = _side_menu_position(self.configurator)
        for day in self._range():
            page = DailyPage(
                i18n=self.i18n,
                manifest=manifest,
                day=day,
                debug=self.configurator.debug(),
                side=side,
                **self.params,
            )
            heading = page.title()
            if nomad_topband(self.configurator):
                weekday = self.i18n.t(f"weekday.full.{day.weekday_name}")
                month = self.i18n.t(f"months.full.{day.month().name}")
                title = (
                    f"text(size: h1)[{weekday} · {month} {day.month_day} <{day.id}>]"
                )
                content = page.nomad_content()
            elif scribe_hyperpaper_nav(self.configurator):
                title = page.nav_title()
                content = heading_and_well(heading, page.content())
            else:
                title = heading
                content = page.content()
            out.append(
                PageData(
                    title=title,
                    content=content,
                    page_id=day.id,
                    highlight_months=[day.month()],
                    highlight_quarters=[],
                    heading_mark=HeadingMark.TRAIL,
                )
            )
        return out

    def _range(self):
        return walk(self.configurator.start_date(), self.configurator.end_date())

from enum import StrEnum
from typing import TYPE_CHECKING

from textual import on
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import Button, ContentSwitcher

from chezmoi_mousse import AppType, AreaName, TabBtn, Tcss, ViewName

from .shared.button_groups import TabBtnHorizontal
from .shared.loggers import AppLog, DebugLog, OutputLog
from .shared.tabs_base import TabsBase

if TYPE_CHECKING:
    from chezmoi_mousse import CanvasIds

__all__ = ["LogsTab"]


class BorderTitle(StrEnum):
    app_log = " App Log "
    output_log = " Commands StdOut "
    debug_log = " Debug Log "


class LogsTabSwitcher(ContentSwitcher, AppType):

    def __init__(self, ids: "CanvasIds", dev_mode: bool):
        self.ids = ids
        self.dev_mode = dev_mode
        super().__init__(
            id=self.ids.content_switcher_id(area=AreaName.top),
            initial=self.ids.view_id(view=ViewName.app_log_view),
            classes=Tcss.border_title_top.name,
        )

    def compose(self) -> ComposeResult:
        yield AppLog(ids=self.ids)
        yield OutputLog(ids=self.ids)
        if self.dev_mode is True:
            yield DebugLog(ids=self.ids)

    def on_mount(self) -> None:
        self.border_title = BorderTitle.app_log


class LogsTab(TabsBase, AppType):

    def __init__(self, ids: "CanvasIds") -> None:
        self.ids = ids
        self.tab_buttons = (TabBtn.app_log, TabBtn.output_log)
        super().__init__(ids=self.ids)

    def compose(self) -> ComposeResult:
        with Vertical():
            tab_buttons = (TabBtn.app_log, TabBtn.output_log)
            if self.app.dev_mode is True:
                tab_buttons += (TabBtn.debug_log,)

            yield TabBtnHorizontal(
                ids=self.ids, buttons=tab_buttons, area=AreaName.top
            )
            yield LogsTabSwitcher(ids=self.ids, dev_mode=self.app.dev_mode)

    @on(Button.Pressed, Tcss.tab_button.value)
    def switch_content(self, event: Button.Pressed) -> None:
        event.stop()
        switcher = self.query_exactly_one(LogsTabSwitcher)

        if event.button.id == self.ids.button_id(btn=TabBtn.app_log):
            switcher.current = self.ids.view_id(view=ViewName.app_log_view)
            switcher.border_title = BorderTitle.app_log
        elif event.button.id == self.ids.button_id(btn=TabBtn.output_log):
            switcher.current = self.ids.view_id(view=ViewName.output_log_view)
            switcher.border_title = BorderTitle.output_log
        elif (
            self.app.dev_mode is True
            and event.button.id == self.ids.button_id(btn=TabBtn.debug_log)
        ):
            switcher.current = self.ids.view_id(view=ViewName.debug_log_view)
            switcher.border_title = BorderTitle.debug_log

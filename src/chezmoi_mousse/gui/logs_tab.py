from enum import StrEnum
from typing import TYPE_CHECKING

from textual import on
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import Button, ContentSwitcher

from chezmoi_mousse import AppType, SwitcherName, TabBtn, Tcss, ViewName

from .shared.button_groups import TabBtnHorizontal
from .shared.git_log_view import GitLogView
from .shared.loggers import AppLog, DebugLog, OutputLog
from .shared.tabs_base import TabsBase

if TYPE_CHECKING:
    from .shared.canvas_ids import CanvasIds

__all__ = ["LogsTab"]


class BorderTitle(StrEnum):
    app_log = " App Log "
    debug_log = " Debug Log "
    git_log_global = " Global Git Log "
    read_output_log = " Read Output Log "
    write_output_log = " Write Output Log "


class LogsTabSwitcher(ContentSwitcher, AppType):

    def __init__(self, ids: "CanvasIds"):
        self.ids = ids
        super().__init__(
            id=self.ids.content_switcher_id(
                switcher_name=SwitcherName.logs_switcher
            ),
            initial=self.ids.view_id(view=ViewName.app_log_view),
            classes=Tcss.border_title_top.name,
        )

    def compose(self) -> ComposeResult:
        yield AppLog(ids=self.ids)
        yield OutputLog(ids=self.ids, view_name=ViewName.read_output_log_view)
        yield OutputLog(ids=self.ids, view_name=ViewName.write_output_log_view)
        yield GitLogView(ids=self.ids)
        if self.app.dev_mode is True:
            yield DebugLog(ids=self.ids)

    def on_mount(self) -> None:
        self.border_title = BorderTitle.app_log


class LogsTab(TabsBase, AppType):

    def __init__(self, ids: "CanvasIds") -> None:
        self.ids = ids
        super().__init__(ids=self.ids)

    def compose(self) -> ComposeResult:
        with Vertical():
            tab_buttons = (
                TabBtn.app_log,
                TabBtn.read_output_log,
                TabBtn.write_output_log,
                TabBtn.git_log_global,
            )
            if self.app.dev_mode is True:
                tab_buttons += (TabBtn.debug_log,)

            yield TabBtnHorizontal(ids=self.ids, buttons=tab_buttons)
            yield LogsTabSwitcher(ids=self.ids)

    @on(Button.Pressed, Tcss.tab_button.value)
    def switch_content(self, event: Button.Pressed) -> None:
        event.stop()
        switcher = self.query_exactly_one(LogsTabSwitcher)

        if event.button.id == self.ids.button_id(btn=TabBtn.app_log):
            switcher.current = self.ids.view_id(view=ViewName.app_log_view)
            switcher.border_title = BorderTitle.app_log
        elif event.button.id == self.ids.button_id(btn=TabBtn.read_output_log):
            switcher.current = self.ids.view_id(
                view=ViewName.read_output_log_view
            )
            switcher.border_title = BorderTitle.read_output_log
        elif event.button.id == self.ids.button_id(
            btn=TabBtn.write_output_log
        ):
            switcher.current = self.ids.view_id(
                view=ViewName.write_output_log_view
            )
            switcher.border_title = BorderTitle.write_output_log
        elif event.button.id == self.ids.button_id(btn=TabBtn.git_log_global):
            switcher.border_title = BorderTitle.git_log_global
            switcher.current = self.ids.view_id(view=ViewName.git_log_view)
        elif (
            self.app.dev_mode is True
            and event.button.id == self.ids.button_id(btn=TabBtn.debug_log)
        ):
            switcher.current = self.ids.view_id(view=ViewName.debug_log_view)
            switcher.border_title = BorderTitle.debug_log

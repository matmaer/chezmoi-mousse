from textual import on
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import Button, ContentSwitcher

from chezmoi_mousse import AreaName, Id, TabBtn, Tcss, ViewName
from chezmoi_mousse._id_classes import CanvasIds
from chezmoi_mousse.gui import AppType
from chezmoi_mousse.gui.button_groups import TabBtnHorizontal
from chezmoi_mousse.gui.rich_logs import AppLog, DebugLog, OutputLog

__all__ = ["LogsTab"]


class LogsTabSwitcher(ContentSwitcher, AppType):

    def __init__(self, canvas_ids: CanvasIds, dev_mode: bool):
        self.canvas_ids = canvas_ids
        self.dev_mode = dev_mode
        super().__init__(
            id=self.canvas_ids.content_switcher_id(area=AreaName.top),
            initial=self.canvas_ids.view_id(view=ViewName.app_log_view),
            classes=Tcss.border_title_top.name,
        )

    def compose(self) -> ComposeResult:
        yield AppLog(canvas_ids=self.canvas_ids)
        yield OutputLog(canvas_ids=self.canvas_ids)
        if self.dev_mode is True:
            yield DebugLog(canvas_ids=self.canvas_ids)

    def on_mount(self) -> None:
        self.border_title = " App Log "


class LogsTab(Vertical, AppType):

    def __init__(self) -> None:
        self.ids = Id.logs_tab
        self.tab_buttons = (TabBtn.app_log, TabBtn.output_log)
        super().__init__(id=self.ids.tab_container_id)

    def compose(self) -> ComposeResult:
        tab_buttons = (TabBtn.app_log, TabBtn.output_log)
        if self.app.dev_mode is True:
            tab_buttons += (TabBtn.debug_log,)

        yield TabBtnHorizontal(
            canvas_ids=self.ids, buttons=tab_buttons, area=AreaName.top
        )
        yield LogsTabSwitcher(canvas_ids=self.ids, dev_mode=self.app.dev_mode)

    @on(Button.Pressed, Tcss.tab_button.value)
    def switch_content(self, event: Button.Pressed) -> None:
        event.stop()
        switcher = self.query_exactly_one(LogsTabSwitcher)

        if event.button.id == self.ids.button_id(btn=TabBtn.app_log):
            switcher.current = self.ids.view_id(view=ViewName.app_log_view)
            switcher.border_title = " App Log "
        elif event.button.id == self.ids.button_id(btn=TabBtn.output_log):
            switcher.current = self.ids.view_id(view=ViewName.output_log_view)
            switcher.border_title = " Commands StdOut "
        elif (
            self.app.dev_mode is True
            and event.button.id == self.ids.button_id(btn=TabBtn.debug_log)
        ):
            switcher.current = self.ids.view_id(view=ViewName.debug_log_view)
            switcher.border_title = " Debug Log "

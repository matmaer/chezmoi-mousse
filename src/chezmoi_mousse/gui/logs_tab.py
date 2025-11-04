from enum import StrEnum
from typing import TYPE_CHECKING

from textual import on
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import Button, ContentSwitcher

from chezmoi_mousse import AppType, ContainerName, TabBtn, Tcss, ViewName

from .shared.button_groups import TabBtnHorizontal
from .shared.git_log_view import GitLogView
from .shared.loggers import AppLog, DebugLog, OutputLog

if TYPE_CHECKING:
    from .shared.canvas_ids import CanvasIds

__all__ = ["LogsTab"]


class BorderTitle(StrEnum):
    app_log = " App Log "
    debug_log = " Debug Log "
    git_log_global = " Global Git Log "
    read_output_log = " Read Output Log "
    write_output_log = " Write Output Log "


class LogsTab(Vertical, AppType):

    def __init__(self, ids: "CanvasIds") -> None:
        super().__init__()

        self.ids = ids
        self.tab_buttons = (
            TabBtn.app_log,
            TabBtn.read_output_log,
            TabBtn.write_output_log,
            TabBtn.git_log_global,
        )
        if self.app.dev_mode is True:
            self.tab_buttons = (TabBtn.debug_log,) + self.tab_buttons
            self.initial_view = ViewName.debug_log_view
        else:
            self.initial_view = ViewName.app_log_view
        self.content_switcher_id = ids.content_switcher_id(
            name=ContainerName.logs_switcher
        )
        self.content_switcher_qid = ids.content_switcher_id(
            "#", name=ContainerName.logs_switcher
        )
        self.app_log_btn_id = ids.button_id(btn=TabBtn.app_log)
        self.read_output_log_btn_id = self.ids.button_id(
            btn=TabBtn.read_output_log
        )
        self.write_output_log_btn_id = ids.button_id(
            btn=TabBtn.write_output_log
        )
        self.git_log_global_btn_id = ids.button_id(btn=TabBtn.git_log_global)
        self.debug_log_btn_id = ids.button_id(btn=TabBtn.debug_log)

        self.app_log_view_id = ids.view_id(view=ViewName.app_log_view)
        self.read_output_log_view_id = ids.view_id(
            view=ViewName.read_output_log_view
        )
        self.write_output_log_view_id = ids.view_id(
            view=ViewName.write_output_log_view
        )
        self.git_log_global_view_id = ids.view_id(view=ViewName.git_log_view)
        self.debug_log_view_id = self.ids.view_id(view=ViewName.debug_log_view)

    def compose(self) -> ComposeResult:
        yield TabBtnHorizontal(ids=self.ids, buttons=self.tab_buttons)
        with ContentSwitcher(
            id=self.ids.content_switcher_id(name=ContainerName.logs_switcher),
            initial=self.ids.view_id(view=self.initial_view),
            classes=Tcss.border_title_top.name,
        ):
            yield AppLog(ids=self.ids)
            yield OutputLog(
                ids=self.ids, view_name=ViewName.read_output_log_view
            )
            yield OutputLog(
                ids=self.ids, view_name=ViewName.write_output_log_view
            )
            yield GitLogView(ids=self.ids)
            if self.app.dev_mode is True:
                yield DebugLog(ids=self.ids)

    def on_mount(self) -> None:
        switcher = self.query_one(self.content_switcher_qid, ContentSwitcher)
        if self.initial_view == ViewName.debug_log_view:
            switcher.border_title = BorderTitle.debug_log
        else:
            switcher.border_title = BorderTitle.app_log

    @on(Button.Pressed, Tcss.tab_button.value)
    def switch_content(self, event: Button.Pressed) -> None:
        event.stop()
        switcher = self.query_one(self.content_switcher_qid, ContentSwitcher)
        if event.button.id == self.app_log_btn_id:
            switcher.current = self.app_log_view_id
            switcher.border_title = BorderTitle.app_log
        elif event.button.id == self.read_output_log_btn_id:
            switcher.current = self.read_output_log_view_id
            switcher.border_title = BorderTitle.read_output_log
        elif event.button.id == self.write_output_log_btn_id:
            switcher.current = self.write_output_log_view_id
            switcher.border_title = BorderTitle.write_output_log
        elif event.button.id == self.git_log_global_btn_id:
            switcher.border_title = BorderTitle.git_log_global
            switcher.current = self.git_log_global_view_id
        elif (
            self.app.dev_mode is True
            and event.button.id == self.debug_log_btn_id
        ):
            switcher.current = self.debug_log_view_id
            switcher.border_title = BorderTitle.debug_log

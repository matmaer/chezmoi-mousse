from __future__ import annotations

from typing import TYPE_CHECKING

from textual import work
from textual.containers import ScrollableContainer
from textual.reactive import reactive
from textual.widgets import TabPane

from chezmoi_mousse.gui.common import widget_factory
from chezmoi_mousse.str_enums import ColorVar, LogStr

if TYPE_CHECKING:
    from textual import getters
    from textual.app import ComposeResult

    from chezmoi_mousse.data_types import CommandResult
    from chezmoi_mousse.gui.textual_app import ChezmoiGui


__all__ = ["LogsTab"]


class LogsTab(TabPane):
    if TYPE_CHECKING:
        app = getters.app(ChezmoiGui)

    cmd_result: reactive[CommandResult | None] = reactive(None, init=False)

    def compose(self) -> ComposeResult:
        yield ScrollableContainer()

    def on_mount(self) -> None:
        self.scroll = self.query_exactly_one(ScrollableContainer)
        self.mount_line(LogStr.app_log_initialized, ColorVar.foreground_darken_3)

        if "debug" in self.app.features:
            msg = f"Running textual --dev: {LogStr.debug_tab_enabled}"
            self.mount_line(f"{msg}", ColorVar.text_warning)

    def mount_line(self, msg: str, color: ColorVar) -> None:
        self.scroll.mount(widget_factory.log_static(msg, color))

    # NOTE: description to avoid the whole dataclass repr ending up in the description
    @work(description="Log stdout and stderr in a collapsible")
    async def _log_cmd_result(self, cmd_result: CommandResult) -> None:
        self.scroll.mount(widget_factory.cmd_result_collapsible(cmd_result=cmd_result))
        if "doctor" in cmd_result.full_cmd:
            self.scroll.mount_all(widget_factory.doctor_log_lines(cmd_result))

    def watch_cmd_result(self, cmd_result: CommandResult | None) -> None:
        if cmd_result is None:
            return
        self._log_cmd_result(cmd_result)

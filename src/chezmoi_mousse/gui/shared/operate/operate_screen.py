from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import RichLog

from chezmoi_mousse import Canvas, OperateData, Tcss

from .operate_msg import OperateDismissMsg


class OperateScreen(Screen[OperateDismissMsg]):
    def __init__(self, operate_data: OperateData) -> None:
        super().__init__(id=Canvas.operate.name, classes=Tcss.operate_screen)
        self.operate_data = operate_data

    def compose(self) -> ComposeResult:
        yield RichLog(id="operate-screen-log")

    def on_mount(self) -> None:
        log_widget = self.query_one(RichLog)
        log_widget.write("placeholder for operate screen")

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widget import Widget
from textual.widgets import RichLog


class LogSlidebar(Widget):

    def __init__(self, highlight: bool = False):
        super().__init__()
        self.animate = True
        self.auto_scroll = True
        self.highlight = highlight
        self.markup = True
        self.max_lines = 160  # (80×3÷2)×((16−4)÷9)
        self.wrap = True

    def compose(self) -> ComposeResult:
        with Vertical():
            yield RichLog(id="richlog-slidebar")

from collections import deque

from rich.segment import Segment
from rich.style import Style
from textual.app import ComposeResult
from textual.containers import Center
from textual.strip import Strip
from textual.widget import Widget
from textual.screen import Screen
from textual.widgets import Footer


SPLASH = """\
 ██████╗██╗  ██╗███████╗███████╗███╗   ███╗ ██████╗ ██╗
██╔════╝██║  ██║██╔════╝╚══███╔╝████╗ ████║██╔═══██╗██║
██║     ███████║█████╗    ███╔╝ ██╔████╔██║██║   ██║██║
██║     ██╔══██║██╔══╝   ███╔╝  ██║╚██╔╝██║██║   ██║██║
╚██████╗██║  ██║███████╗███████╗██║ ╚═╝ ██║╚██████╔╝██║
 ╚═════╝╚═╝  ╚═╝╚══════╝╚══════╝╚═╝     ╚═╝ ╚═════╝ ╚═╝

 ███╗   ███╗ ██████╗ ██╗   ██╗███████╗███████╗███████╗
 ████╗ ████║██╔═══██╗██║   ██║██╔════╝██╔════╝██╔════╝
 ██╔████╔██║██║   ██║██║   ██║███████╗███████╗█████╗
 ██║╚██╔╝██║██║   ██║██║   ██║╚════██║╚════██║██╔══╝
 ██║ ╚═╝ ██║╚██████╔╝╚██████╔╝███████║███████║███████╗
 ╚═╝     ╚═╝ ╚═════╝  ╚═════╝ ╚══════╝╚══════╝╚══════╝
""".splitlines()

FADE = (
    "#439CFB",
    "#439CFB",
    "#439CFB",
    "#439CFB",
    "#6698FB",
    "#8994FB",
    "#AB8FFB",
    "#CE8BFB",
    "#F187FB",
    "#CE8BFB",
    "#AB8FFB",
    "#8994FB",
    "#6698FB",
    "#439CFB",
    "#439CFB",
    "#439CFB",
    "#439CFB",
)


class GreeterBackground(Widget):
    # size of SPLASH is 55 * 13
    # pad with spaces to make each line the same length
    text = [line.ljust(len(max(SPLASH, key=len))) for line in SPLASH]
    # deque to use the .rotate() method
    colors = deque([Style(color=color) for color in FADE])

    def __init__(self) -> None:
        super().__init__()
        # set_interval is a method from the Textual message pump
        self.set_interval(interval=0.1, callback=self.refresh)

    def render_lines(self, crop) -> list[Strip]:
        self.colors.rotate()
        return super().render_lines(crop)

    def render_line(self, y: int) -> Strip:
        return Strip([Segment(self.text[y], style=self.colors[y])])


class GreeterScreen(Screen):
    def compose(self) -> ComposeResult:
        with Center():
            yield GreeterBackground()
        yield Footer()

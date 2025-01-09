from collections import deque

from rich.segment import Segment
from rich.style import Style
from textual.app import ComposeResult
from textual.containers import Center
from textual.geometry import Region
from textual.strip import Strip
from textual.widget import Widget
from textual.screen import Screen
from textual.widgets import Footer
from textual.reactive import reactive


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
"""

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


class GreeterWidget(Widget):
    colors: deque[Style] = deque()
    text: reactive[list[str]] = reactive(list, init=False)

    def __init__(self) -> None:
        super().__init__()
        self.text = self.create_text_with_style()
        self.clock = self.set_interval(0.1, self.refresh)
        # self.colors = deque([Style])

    def create_text_with_style(self) -> list[str]:
        splash_list = SPLASH.splitlines()
        # pad each line in the list with spaces to the right
        width = len(max(splash_list, key=len))
        splash_list = [line.ljust(width) for line in splash_list]
        return splash_list

    def on_mount(self) -> None:
        for color in FADE:
            self.colors.append(Style(color=color))
        return self.colors

    def render_lines(self, crop: Region) -> list[Strip]:
        self.colors.rotate()
        return super().render_lines(crop)

    def render_line(self, y: int) -> Strip:
        return Strip([Segment(self.text[y], style=self.colors[y])])


class GreeterSplash(Screen):
    def compose(self) -> ComposeResult:
        with Center():
            yield GreeterWidget()
        yield Footer()

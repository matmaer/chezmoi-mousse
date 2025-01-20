from collections import deque

from rich.segment import Segment
from rich.style import Style
from textual.app import ComposeResult
from textual.containers import Center
from textual.geometry import Region
from textual.screen import Screen
from textual.strip import Strip
from textual.widgets import Footer
from textual.widget import Widget

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
    "rgb(67, 156, 251)",
    "rgb(67, 156, 251)",
    "rgb(67, 156, 251)",
    "rgb(67, 156, 251)",
    "rgb(67, 156, 251)",
    "rgb(67, 156, 251)",
    "rgb(67, 156, 251)",
    "rgb(67, 156, 251)",
    "rgb(67, 156, 251)",
    "rgb(67, 156, 251)",
    "rgb(102, 152, 251)",
    "rgb(137, 148, 251)",
    "rgb(171, 143, 251)",
    "rgb(206, 139, 251)",
    "rgb(241, 135, 251)",
    "rgb(241, 135, 251)",
    "rgb(206, 139, 251)",
    "rgb(171, 143, 251)",
    "rgb(137, 148, 251)",
    "rgb(102, 152, 251)",
)


class LoadingBackground(Widget):
    text = [line.ljust(len(max(SPLASH, key=len))) for line in SPLASH]
    colors = deque([Style(color=color) for color in FADE])

    def __init__(self) -> None:
        super().__init__()
        self.set_interval(interval=0.06, callback=self.refresh, repeat=46)

    def render_lines(self, crop: Region) -> list[Strip]:
        self.colors.rotate()
        return super().render_lines(crop)

    def render_line(self, y: int) -> Strip:
        return Strip([Segment(self.text[y], style=self.colors[y])])


class LoadingScreen(Screen):
    def compose(self) -> ComposeResult:
        with Center():
            yield LoadingBackground()
        yield Footer()

from collections import deque


from rich.color import Color
from rich.segment import Segment
from rich.style import Style
from textual.app import ComposeResult
from textual.containers import Center
from textual.geometry import Region
from textual.strip import Strip
from textual.widget import Widget
from textual.screen import Screen
from textual.widgets import Footer


SPLASH = """
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


def create_text() -> list[str]:
    splash_list = SPLASH.splitlines()[1:]
    # pad each line in the list with spaces to the right
    width = len(max(splash_list, key=len))
    splash_list = [line.ljust(width) for line in splash_list]
    return splash_list


class GreeterWidget(Widget):
    def __init__(self) -> None:
        super().__init__()
        self.text = create_text()
        self.clock = self.set_interval(0.1, self.refresh)

    colors: deque[Style] = deque()

    def on_mount(self) -> None:
        for color in (
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
        ):
            self.colors.append(Style(color=Color.parse(color)))

    def render_lines(self, crop: Region) -> list[Strip]:
        self.colors.rotate()
        return super().render_lines(crop)

    def render_line(self, y: int) -> Strip:
        return Strip([Segment(self.text[y], style=self.colors[y % 17])])

    def get_content_height(self, *_) -> int:
        return len(self.text)

    def get_content_width(self, *_) -> int:
        return len(self.text[1])


class GreeterScreen(Screen):
    def compose(self) -> ComposeResult:
        with Center():
            yield GreeterWidget()
            yield Footer()

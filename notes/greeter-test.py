from collections import deque

from rich.color import Color
from rich.segment import Segment
from rich.style import Style
from textual.app import App, ComposeResult
from textual.containers import Container
from textual.strip import Strip
from textual.widget import Widget


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


class GreeterWidget(Widget):
    def __init__(self) -> None:
        super().__init__()
        self.text = self.create_text()
        self.width = len(self.text[1])
        self.height = len(self.text)

    def create_text(self) -> list[str]:
        splash_list = SPLASH.splitlines()[1:]
        # pad each line in the list with spaces to the right
        width = len(max(splash_list, key=len))
        splash_list = [line.ljust(width) for line in splash_list]
        return splash_list

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
        self.clock = self.set_interval(interval=0.1, callback=self.refresh)

    def render_lines(self, crop) -> list[Strip]:
        self.colors.rotate()
        return super().render_lines(crop)

    def render_line(self, y: int) -> Strip:
        return Strip([Segment(self.text[y], style=self.colors[y])])

    def get_content_height(self, *_) -> int:
        return len(self.text)

    def get_content_width(self, *_) -> int:
        return len(self.text[1])


class GreeterApp(App):
    CSS = """
    GreeterWidget {
        width: auto;
        height: auto;
    }
    Container {
        align: center middle;
        background: black;
    }
    """

    def compose(self) -> ComposeResult:
        with Container():
            yield GreeterWidget()


if __name__ == "__main__":
    GreeterApp().run()

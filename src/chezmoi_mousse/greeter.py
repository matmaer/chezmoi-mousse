from collections import deque

from time import sleep
from rich.segment import Segment
from rich.style import Style

from textual import work
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container
from textual.screen import Screen
from textual.strip import Strip
from textual.widgets import Footer, ProgressBar, Static, RichLog

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


class AnimatedFade(Static):
    """A widget to show a custom loading screen."""

    text = [line.ljust(len(max(SPLASH, key=len))) for line in SPLASH]
    line_styles = deque([Style(color=color) for color in FADE])

    def render_lines(self, crop) -> list[Strip]:
        self.line_styles.rotate()
        return super().render_lines(crop)

    def render_line(self, y: int) -> Strip:
        return Strip([Segment(self.text[y], style=self.line_styles[y])])

    def on_mount(self) -> None:
        self.set_interval(interval=0.04, callback=self.refresh, repeat=47)


class CustomLoader(Static):
    def compose(self):
        yield ProgressBar()


class ItemLoader(Static):
    def compose(self):
        yield RichLog()

    @work(thread=True)
    def on_mount(self) -> None:
        for i in range(1, 6):
            sleep(0.5)
            # self.query_one(ProgressBar).advance(20)
            self.query_one(RichLog).write(f"Loading items {i}")


class LoadingScreen(Screen):

    BINDINGS = [
        Binding(
            key="escape",
            action="app.push_screen('inspect')",
            description="Skip to the inspect screen",
        ),
    ]

    def compose(self) -> ComposeResult:
        with Container(id="loadingscreen"):
            yield AnimatedFade()
            yield ProgressBar()
            yield ItemLoader()
        yield Footer()

    @work(thread=True)
    def on_mount(self) -> None:
        for i in range(1, 6):
            sleep(0.5)
            self.query_one(ProgressBar).advance(20)

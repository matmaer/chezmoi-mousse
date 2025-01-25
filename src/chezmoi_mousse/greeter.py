from collections import deque

from rich.segment import Segment
from rich.style import Style
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Center, Container, Middle
from textual.screen import Screen
from textual.strip import Strip
from textual.widgets import Footer, Label, ProgressBar, Static

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
    colors = deque([Style(color=color) for color in FADE])

    def render_lines(self, crop) -> list[Strip]:
        self.colors.rotate()
        return super().render_lines(crop)

    def render_line(self, y: int) -> Strip:
        return Strip([Segment(self.text[y], style=self.colors[y])])

    def on_mount(self) -> None:
        self.set_interval(interval=0.04, callback=self.refresh, repeat=47)


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
            yield Middle(
                Center(AnimatedFade()),
                Center(
                    ProgressBar(
                        total=100,
                        gradient=FADE,
                        show_eta=False,
                        show_percentage=False,
                    )
                ),
                Center(Label("Loading")),
            )
            # yield ItemLoader()
            # yield Label("aoeu")
        yield Footer()

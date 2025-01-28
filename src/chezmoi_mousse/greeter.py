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

from chezmoi_mousse.graphic import FADE, SPLASH


class AnimatedFade(Static):
    """A widget to show a custom loading screen."""

    text = [line.ljust(len(max(SPLASH, key=len))) for line in SPLASH.splitlines()]
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
            yield ProgressBar(
                id="progress",
                show_eta=False,
                total=100,
                )
            yield ItemLoader()
        yield Footer()

    @work(thread=True)
    def on_mount(self) -> None:
        for i in range(1, 6):
            sleep(0.5)
            self.query_one("#progress").advance(20)
            self.query_one(RichLog).write(f"Loading items {i}")

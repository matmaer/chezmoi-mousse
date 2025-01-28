from collections import deque

from time import sleep
from rich.segment import Segment
from rich.style import Style

from textual import work
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Center, Middle
from textual.screen import Screen
from textual.strip import Strip
from textual.widgets import Footer, RichLog
from textual.widget import Widget

from chezmoi_mousse.graphic import FADE, SPLASH


class AnimatedFade(Widget):

    def __init__(self) -> None:
        super().__init__()
        self.id = "animatedfade"
        # classes = "loader"

    def construct_splash_lines():
        splash_lines = SPLASH.splitlines()
        max_width = len(max(splash_lines, key=len))
        return [line.ljust(max_width) for line in splash_lines]

    padded_splash = construct_splash_lines()
    line_styles = deque([Style(color=color) for color in FADE])

    def render_lines(self, crop) -> list[Strip]:
        self.line_styles.rotate()
        return super().render_lines(crop)

    def render_line(self, y: int) -> Strip:
        return Strip([Segment(self.padded_splash[y], style=self.line_styles[y])])

    def on_mount(self) -> None:
        self.set_interval(interval=0.10, callback=self.refresh)

    # def compose(self):
    #     self.query_one("#animatedfade")

class ItemLoader(Widget):
    def __init__(self):
        super().__init__()
        self.id = "itemloader"
    def compose(self):
        yield RichLog(
            id="loaderlog",
            max_lines=1,
            markup=True,
            classes="loader"
        )

    @work(thread=True)
    def on_mount(self) -> None:
        # item_loader = self.query_one("#itemloader")
        # data_table.loading = True
        for i in range(1, 6):
            sleep(0.7)

class LoadingScreen(Screen):

    BINDINGS = [
        Binding(
            key="escape",
            action="app.push_screen('inspect')",
            description="skip animation",
            tooltip="file an issue on Github if you can see this tooltip",
        ),
    ]

    def __init__(self):
        super().__init__()
        self.id = "loadingscreen"

    def compose(self) -> ComposeResult:
        with Center():
            with Middle():
                yield AnimatedFade()
                yield ItemLoader()
        yield Footer()


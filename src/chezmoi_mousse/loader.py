from collections import deque

from rich.segment import Segment
from rich.style import Style
from textual import work
from textual.app import ComposeResult
from textual.containers import Center, Middle
from textual.screen import Screen
from textual.strip import Strip
from textual.widget import Widget
from textual.widgets import Footer, Header, RichLog

from chezmoi_mousse import CHEZMOI
from chezmoi_mousse.commands import ChezmoiCommand as chezmoi
from chezmoi_mousse.graphics import FADE, SPLASH


class AnimatedFade(Widget):

    def __init__(self) -> None:
        super().__init__()
        self.id = "animated-fade"
        self.styles.height = 10
        self.styles.width = 55
        print(self.__class__.__mro__)

    @staticmethod
    def construct_splash_lines() -> list:
        splash_lines = SPLASH.splitlines()
        max_width = len(max(splash_lines, key=len))
        return [line.ljust(max_width) for line in splash_lines]

    padded_splash = construct_splash_lines()
    line_styles = deque([Style(color=color, bold=True) for color in FADE])

    def render_lines(self, crop) -> list[Strip]:
        self.line_styles.rotate()
        return super().render_lines(crop)

    def render_line(self, y: int) -> Strip:
        return Strip(
            [Segment(self.padded_splash[y], style=self.line_styles[y])]
        )

    def on_mount(self) -> None:
        self.set_interval(interval=0.10, callback=self.refresh)


class ItemLoader(Widget):

    def __init__(self) -> None:
        super().__init__()
        self.id = "item-loader"
        print(self.__class__.__mro__)

    def compose(self) -> ComposeResult:
        yield RichLog(
            id="loader-log",
            markup=True,
            max_lines=11,
        )


class LoadingScreen(Screen):

    BINDINGS = [
        ("i", "app.push_screen('inspect')", "inspect"),
        ("o", "app.push_screen('operate')", "operate"),
    ]

    def __init__(self):
        super().__init__()
        self.id = "loader-screen"
        print(self.__class__.__mro__)

    def compose(self) -> ComposeResult:
        yield Header(id="loader-header")
        with Middle():
            with Center():
                yield AnimatedFade()
                yield ItemLoader()
        yield Footer(id="loader-footer")


    def create_log_line(self, command: str) -> None:
        pad_chars = 33
        verb = command.split()[0]
        verb_only_command = f"chezmoi {verb} ".ljust(pad_chars, ".")
        color = self.app.theme_variables["success"]
        logline = f"[{color}]{verb_only_command} loaded[/]"
        return logline

    @work(thread=True)
    def load_command_output(self, command: str) -> None:
        logline = self.create_log_line(command)
        chezmoi.run(command)
        self.query_one("#loader-log").write(logline)

    def on_mount(self) -> None:
        self.title = "-  c h e z m o i  m o u s s e  -"

        for verb, items in CHEZMOI.__dict__.items():
            command = items.command
            self.load_command_output(command)

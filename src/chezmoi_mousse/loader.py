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

from chezmoi_mousse import CHEZMOI, SPLASH, CommandData
from chezmoi_mousse.commands import ChezmoiCommand as chezmoi
from chezmoi_mousse.graphics import FADE


class AnimatedFade(Widget):

    def __init__(self) -> None:
        super().__init__()
        self.id = "animated-fade"
        self.styles.height = 10
        self.styles.width = 55

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


class LoadingScreen(Screen):

    BINDINGS = [
        ("i", "app.push_screen('inspect')", "inspect"),
        ("o", "app.push_screen('operate')", "operate"),
    ]

    def __init__(self):
        super().__init__()
        self.id = "loader-screen"

    def compose(self) -> ComposeResult:
        yield Header(id="loader-header")
        with Middle():
            yield Center(AnimatedFade())
            yield Center(
                RichLog(
                    id="loader-log",
                    markup=True,
                    max_lines=11,
                )
            )
        yield Footer(id="loader-footer")

    @work(thread=True)
    def first_run(self, command: CommandData) -> CommandData:
        short_cmd = f"chezmoi {command.verb_cmd[0]}".ljust(33, ".")
        color = self.app.theme_variables["success"]
        logline = f"[{color}]{short_cmd} loaded[/]"
        chezmoi.run(command)

        self.query_one("#loader-log").write(logline)

    def on_mount(self) -> None:
        self.title = "-  c h e z m o i  m o u s s e  -"
        for _, command in CHEZMOI.__dict__.items():
            self.first_run(command)

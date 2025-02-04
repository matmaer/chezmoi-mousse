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

from chezmoi_mousse import VERBS
from chezmoi_mousse.commands import ChezmoiCommands
from chezmoi_mousse.graphics import FADE, SPLASH


class AnimatedFade(Widget):

    def __init__(self) -> None:
        super().__init__()
        self.styles.height = 10
        self.styles.width = 55

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


class ItemLoader(Widget):
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
        self.commands = ChezmoiCommands()

    def compose(self) -> ComposeResult:
        yield Header(id="loader-header")
        with Center():
            with Middle():
                yield AnimatedFade()
                yield ItemLoader(id="loader-items")
        yield Footer(id="loader-footer")

    @work(thread=True)
    def load_command_output(self, verb: str) -> None:
        if verb == "managed":
            command = "managed --path-style=absolute"
        else:
            command = verb
        self.commands.run(command, refresh=True)

        pad_chars = 30
        command = f"chezmoi {verb}".ljust(pad_chars, '.')
        success_color = self.app.theme_variables['success']
        message = f"[{success_color}]{command} loaded"
        self.query_one("#loader-log").write(message)

    def on_mount(self) -> None:
        self.title = "- c h e z m o i  m o u s s e -"
        for verb in VERBS:
            self.load_command_output(verb)

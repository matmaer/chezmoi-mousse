from collections import deque

from textual import work
from textual.app import ComposeResult
from textual.containers import Center, Middle
from textual.screen import Screen
from textual.widget import Segment, Strip, Style, Widget
from textual.widgets import Footer, Header, RichLog

from chezmoi_mousse.graphics import FADE
from chezmoi_mousse.commands import Components, run


SPLASH = """\
 _______ _______ _______ _______ ____ ____ _______ _o_
|       |   |   |    ___|___    |    `    |       |   |
|    ===|       |     __|     __|         |   |   |   |
|       |   |   |       |       |   |`|   |       |   |
`-------^---^---^-------^-------^---' '---^-------^---'
   ____ ____ _______ ___ ___ _______ _______ _______
  |    `    |       |   |   |    ___|    ___|    ___|
  |         |   |   |   |   |__     |__     |     __|
  |   |`|   |       |       |       |       |       |
  '---' '---^-------^-------^-------^-------^-------'
""".splitlines()


class AnimatedFade(Widget):

    line_styles = deque([Style(color=color, bold=True) for color in FADE])

    def __init__(self) -> None:
        super().__init__()
        self.id = "animated-fade"
        self.styles.height = 10
        self.styles.width = len(max(SPLASH, key=len))

    def render_lines(self, crop) -> list[Strip]:
        self.line_styles.rotate()
        return super().render_lines(crop)

    def render_line(self, y: int) -> Strip:
        return Strip([Segment(SPLASH[y], style=self.line_styles[y])])

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
    def store_command_output(self, command: str, verb: str) -> None:
        rlog = self.query_one("#loader-log")
        run(command, verb, refresh=True)
        pad_chars = 33
        padded_command = f"{command} {verb} ".ljust(pad_chars, ".")
        rlog.write(f"{padded_command} loaded")

    def on_mount(self) -> None:
        self.title = "-  c h e z m o i  m o u s s e  -"
        for c, v in Components().empty_cmd_dict.items():
            for verb in v.keys():
                self.store_command_output(c, verb)

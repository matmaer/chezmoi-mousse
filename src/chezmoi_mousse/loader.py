from collections import deque

from textual import work
from textual.app import ComposeResult
from textual.color import Color, Gradient
from textual.containers import Center, Middle
from textual.screen import Screen
from textual.widget import Segment, Strip, Style, Widget
from textual.widgets import Footer, Header, Log, RichLog

from chezmoi_mousse.commands import Components, run

__all__ = ["LoadingScreen"]

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


def create_fade():
    start_color = "rgb(67, 156, 251)"
    end_color = "rgb(241, 135, 251)"
    fade = [Color.parse(start_color)] * 4
    gradient = Gradient.from_colors(
        start_color,
        end_color,
        quality=5,
    )
    fade.extend(gradient.colors)
    gradient.colors.reverse()
    fade.extend(gradient.colors)
    return fade


FADE = create_fade()


class AnimatedFade(Widget):

    line_styles = deque([Style(color=color.hex, bold=True) for color in FADE])

    def __init__(self) -> None:
        super().__init__()
        self.id = "animated-fade"
        self.styles.height = len(SPLASH)
        self.styles.width = len(max(SPLASH, key=len))

    def render_lines(self, crop) -> list[Strip]:
        self.line_styles.rotate()
        return super().render_lines(crop)

    def render_line(self, y: int) -> Strip:
        return Strip([Segment(SPLASH[y], style=self.line_styles[y])])

    def on_mount(self) -> None:
        self.set_interval(interval=0.10, callback=self.refresh)


class AnimatedLog(Widget):

    line_cols: int = 34  # total width of the padded text in characters
    pad_char: str = "."
    status_text: dict = ("loaded", "loading")

    def __init__(self) -> None:
        super().__init__()
        self.id = "animated-log"
        # self.log = Log(id="loader-log", max_lines=11)

    def get_log_line(self, sub_cmd_name, nr: int) -> str:
        # nr of padding chars needed to get to line_cols minus 2 spaces
        pad_char_count = self.line_cols - len(self.status_text[nr]) - 2
        prefix = f"chezmoi {Components().pretty_cmd(sub_cmd_name)}"
        pad_chars = f"{self.pad_char * pad_char_count}"
        return f"{prefix} {pad_chars} {self.status_text[nr]}"  # includes two spaces

    def compose(self) -> ComposeResult:
        with Center():
            yield Log(id="loader-log", max_lines=11)

    @work(thread=True)
    def store_command_output(self, sub_cmd_name: str) -> None:
        run(sub_cmd_name, refresh=True)

    def on_mount(self) -> None:
        rlog = self.query_one("#loader-log")

        for sub_cmd_name in Components().subs:
            self.store_command_output(sub_cmd_name)
            line_text = self.get_log_line(sub_cmd_name, 0)
            rlog.log(line_text)


class LoadingScreen(Screen):

    line_cols: int = 40  # total width of the padded text in characters
    pad_char: str = "."
    status: dict = ("loaded", "loading")

    BINDINGS = [
        ("i, I", "app.push_screen('inspect')", "inspect"),
        ("o, O", "app.push_screen('operate')", "operate"),
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
    def store_command_output(self, sub: str) -> None:
        nr = 0
        rlog = self.query_one("#loader-log")
        run(sub, refresh=True)
        status_length = len(self.status[nr])
        pretty_cmd = Components().pretty_cmd(sub)
        # nr of padding chars needed to get to line_cols minus 2 spaces
        pad_length = self.line_cols - len(pretty_cmd) - status_length - 2
        pad_chars = f"{self.pad_char * pad_length}"
        log_line_text = f"{pretty_cmd} {pad_chars} {self.status[nr]}"
        rlog.write(f"{log_line_text}")

    def on_mount(self) -> None:
        self.title = "-  c h e z m o i  m o u s s e  -"
        for sub in Components().subs:
            self.store_command_output(sub)

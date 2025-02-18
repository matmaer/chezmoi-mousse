from collections import deque

from textual import work
from textual.app import ComposeResult
from textual.color import Color, Gradient
from textual.containers import Center, Middle
from textual.screen import Screen
from textual.widget import Segment, Strip, Style, Widget
from textual.widgets import Footer, Header, RichLog

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


class LoadingScreen(Screen):

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
    def store_command_output(self, sub_cmd: str) -> None:
        rlog = self.query_one("#loader-log")
        run(sub_cmd, refresh=True)
        pad_chars = 33
        padded_command = f"chezmoi {sub_cmd} ".ljust(pad_chars, ".")
        rlog.write(f"{padded_command} loaded")

    def on_mount(self) -> None:
        self.title = "-  c h e z m o i  m o u s s e  -"
        for sub_cmd in Components().sub_commands:
            self.store_command_output(sub_cmd)

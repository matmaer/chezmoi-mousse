from collections import deque

from textual import work
from textual.app import ComposeResult
from textual.color import Color, Gradient
from textual.containers import Center, Middle
from textual.screen import Screen
from textual.widget import Segment, Strip, Style, Widget
from textual.widgets import Footer, Header, RichLog

from chezmoi_mousse.commands import InputOutput, Utils, chezmoi
from chezmoi_mousse.splash import SPLASH


class AnimatedFade(Widget):

    line_styles: deque[Style]

    def __init__(self) -> None:
        super().__init__(id="animated-fade")
        self.styles.height = len(SPLASH)
        self.styles.width = len(max(SPLASH, key=len))
        self.line_styles: deque[Style] = self.create_fade()

    def create_fade(self) -> deque[Style]:
        start_color = self.app.current_theme.primary
        end_color = self.app.current_theme.accent
        fade = [Color.parse(start_color)] * 5
        gradient = Gradient.from_colors(start_color, end_color, quality=5)
        fade.extend(gradient.colors)
        gradient.colors.reverse()
        fade.extend(gradient.colors)
        return deque([Style(color=color.hex, bold=True) for color in fade])

    def render_lines(self, crop) -> list[Strip]:
        self.line_styles.rotate()
        return super().render_lines(crop)

    def render_line(self, y: int) -> Strip:
        return Strip([Segment(SPLASH[y], style=self.line_styles[y])])

    def on_mount(self) -> None:
        self.set_interval(interval=0.11, callback=self.refresh)


class LoadingScreen(Screen):

    def __init__(self):
        super().__init__(id="loader-screen")

    def compose(self) -> ComposeResult:
        yield Header(id="loader-header")
        with Middle():
            yield Center(AnimatedFade())
            yield Center(RichLog(id="loader-log", max_lines=11))
        yield Footer(id="loader-footer")

    @work(thread=True)
    def _run(self, arg_id: str, line: str) -> None:
        chezmoi_command = getattr(chezmoi, arg_id)
        chezmoi_command.update()
        self.query_one("#loader-log").write(line)

    def on_mount(self) -> None:
        self.title = "-  c h e z m o i  m o u s s e  -"
        for long_cmd in chezmoi.long_commands:
            arg_id = Utils.get_arg_id(long_cmd)
            setattr(chezmoi, arg_id, InputOutput(long_cmd, arg_id))
            label = getattr(chezmoi, arg_id).label
            padding = 32 - len(label)
            line = f"{label} {'.' * padding} loaded"
            self._run(arg_id, line)

    # Any key will dismiss the screen
    def on_key(self) -> None:
        self.screen.dismiss()

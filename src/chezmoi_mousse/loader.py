from collections import deque

from textual import work
from textual.app import ComposeResult
from textual.color import Color, Gradient
from textual.containers import Center, Middle
from textual.screen import Screen
from textual.widget import Segment, Strip, Style, Widget
from textual.widgets import Footer, Header, RichLog

from chezmoi_mousse.commands import chezmoi, Utils
from chezmoi_mousse.splash import SPLASH


class AnimatedFade(Widget):

    def __init__(self) -> None:
        super().__init__()
        self.id = "animated-fade"
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
        self.set_interval(interval=0.10, callback=self.refresh)


class LoadingScreen(Screen):

    def __init__(self):
        super().__init__()
        self.id = "loader-screen"

    def compose(self) -> ComposeResult:
        yield Header(id="loader-header")
        with Middle():
            yield Center(AnimatedFade())
            yield Center(RichLog(id="loader-log", max_lines=11))
        yield Footer(id="loader-footer")

    @work(thread=True)
    def _run(self, args_id) -> None:
        label = getattr(chezmoi, args_id).label
        padding = 32 - len(label)
        line = f"{label} {'.' * padding} loaded"
        getattr(chezmoi, args_id).update()
        self.query_one("#loader-log").write(line)

    def on_mount(self) -> None:
        self.title = "-  c h e z m o i  m o u s s e  -"
        for long_cmd in chezmoi.long_commands:
            self._run(Utils.get_args_id(long_cmd))

    def on_key(self) -> None:
        self.dismiss(chezmoi)
        # self.query_one(RichLog).write(event)

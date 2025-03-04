from collections import deque

from textual import work
from textual.app import ComposeResult
from textual.color import Color, Gradient
from textual.containers import Center, Middle
from textual.screen import Screen
from textual.widget import Segment, Strip, Style, Widget
from textual.widgets import (
    Button,
    RichLog,  # Pretty, Static, TabbedContent,
)


from chezmoi_mousse.common import SPLASH, chezmoi


class AnimatedFade(Widget):

    def __init__(self, fade_colors: deque[Style]) -> None:
        super().__init__(id="animated-fade")
        self.styles.height = len(SPLASH)
        self.styles.width = len(max(SPLASH, key=len))
        self.line_styles = fade_colors

    def render_lines(self, crop) -> list[Strip]:
        self.line_styles.rotate()
        return super().render_lines(crop)

    def render_line(self, y: int) -> Strip:
        return Strip([Segment(SPLASH[y], style=self.line_styles[y])])

    def on_mount(self) -> None:
        self.set_interval(interval=0.11, callback=self.refresh)


class LoadingScreen(Screen):

    def __init__(self) -> None:
        super().__init__()
        self.id = "loading"
        self.theme_fade: deque[Style] = self.create_fade()

    def create_fade(self) -> deque[Style]:
        start_color = self.app.current_theme.primary
        end_color = self.app.current_theme.accent
        fade = [Color.parse(start_color)] * 5
        gradient = Gradient.from_colors(start_color, end_color, quality=5)
        fade.extend(gradient.colors)
        gradient.colors.reverse()
        fade.extend(gradient.colors)
        return deque([Style(color=color.hex, bold=True) for color in fade])

    def compose(self) -> ComposeResult:
        with Middle():
            yield Center(AnimatedFade(fade_colors=self.theme_fade))
            yield Center(RichLog(name="loader log", id="loader-log", max_lines=11))
            yield Center(
                Button(
                    id="continue",
                    label="press any key to continue",
                    disabled=True,
                )
            )

    @work(thread=True)
    def run(self, arg_id) -> None:
        io = getattr(chezmoi, arg_id)
        io.update()
        padding = 32 - len(io.label)
        log_text = f"{io.label} {'.' * padding} loaded"
        self.query_one("#loader-log").write(log_text)

    def check_workers(self) -> None:
        if all(worker.state == "finished" for worker in self.workers):
            self.query_one("#continue").disabled = False

    def on_mount(self) -> None:
        for arg_id in chezmoi.arg_ids:
            self.run(arg_id)
        # set a timer for 0.1 seconds to check if all workers are finished
        self.set_interval(interval=0.1, callback=self.check_workers)

    def on_key(self) -> None:
        if all(worker.state == "finished" for worker in self.workers):
            self.app.pop_screen()

    def on_click(self) -> None:
        if all(worker.state == "finished" for worker in self.workers):
            self.app.pop_screen()

from collections import deque

from textual import work
from textual.app import ComposeResult
from textual.color import Color, Gradient
from textual.containers import Center, Middle
from textual.screen import Screen
from textual.widget import Segment, Strip, Style, Widget
from textual.widgets import Button, RichLog

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
        self.io_data = {}

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
            yield Center(
                RichLog(name="loader log", id="loader-log", max_lines=11)
            )
            yield Center(
                Button(
                    id="continue",
                    label="press any key or click to continue",
                    disabled=True,
                )
            )

    @work(thread=True, group="loaders")
    def run(self, arg_id) -> None:
        io_class = getattr(chezmoi, arg_id)
        io_class.update()
        padding = 32 - len(io_class.label)
        log_text = f"{io_class.label} {'.' * padding} loaded"
        self.query_one("#loader-log").write(log_text)

    def workers_finished(self) -> bool:
        finished = all(
            worker.state == "finished"
            for worker in self.app.workers
            if worker.group == "loaders"
        )
        if finished:
            self.query_one("#continue").disabled = False
        return finished

    def on_mount(self) -> None:
        to_load = [
            arg_id
            for arg_id in chezmoi.long_commands
            if arg_id not in ["dump_config", "managed"]
        ]
        for arg_id in to_load:
            self.run(arg_id)
        self.set_interval(interval=0.1, callback=self.workers_finished)

    def on_key(self) -> None:
        if self.workers_finished():
            self.screen.dismiss()

    def on_click(self) -> None:
        if self.workers_finished():
            self.screen.dismiss()

from collections import deque
import json
from pathlib import Path

from rich.segment import Segment
from rich.style import Style
from textual import work
from textual.app import ComposeResult
from textual.color import Color, Gradient
from textual.containers import Center, Middle
from textual.screen import Screen
from textual.strip import Strip
from textual.widget import Widget
from textual.widgets import Button, RichLog

from chezmoi_mousse.ascii_art import SPLASH
from chezmoi_mousse.common import chezmoi


class AnimatedFade(Widget):

    def __init__(self, fade_colors: deque[Style]) -> None:
        super().__init__()
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
        self.theme_fade: deque[Style] = self.create_fade()
        super().__init__()

    def create_fade(self) -> deque[Style]:
        start_color = Color.parse(self.app.current_theme.primary)
        end_color = Color.parse(self.app.current_theme.accent)
        fade = [start_color] * 5
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
        if arg_id == "dump_config":
            config_dict = json.loads(io_class.std_out)
            setattr(chezmoi, "config", config_dict)
            setattr(
                chezmoi,
                "dest_dir_paths",
                Path(config_dict["destDir"]).rglob("*"),
            )
        padding = 32 - len(io_class.label)
        log_text = f"{io_class.label} {'.' * padding} loaded"
        self.query_one(RichLog).write(log_text)

    def workers_finished(self) -> None:
        finished = all(
            worker.state == "finished"
            for worker in self.app.workers
            if worker.group == "loaders"
        )
        if finished:
            self.query_one("#continue").disabled = False

    def on_mount(self) -> None:
        for arg_id in chezmoi.long_commands:
            self.run(arg_id)
        self.set_interval(interval=0.1, callback=self.workers_finished)

    def on_key(self) -> None:
        if not self.query_one("#continue").disabled:
            self.dismiss()

    def on_click(self) -> None:
        if not self.query_one("#continue").disabled:
            self.dismiss()

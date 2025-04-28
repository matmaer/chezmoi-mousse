from collections import deque
from pathlib import Path

from rich.segment import Segment
from rich.style import Style
from textual import work
from textual.app import ComposeResult
from textual.color import Color, Gradient
from textual.containers import Center, Middle
from textual.screen import Screen
from textual.strip import Strip
from textual.widgets import Button, RichLog, Static

from chezmoi_mousse import SPLASH
from chezmoi_mousse.chezmoi import chezmoi


class LoadingScreen(Screen):

    class AnimatedFade(Static):

        def __init__(self, line_styles: deque[Style]) -> None:
            self.line_styles = line_styles
            super().__init__()
            self.styles.height = len(SPLASH)
            self.styles.width = len(max(SPLASH, key=len))

        def render_lines(self, crop) -> list[Strip]:
            self.line_styles.rotate()
            return super().render_lines(crop)

        def render_line(self, y: int) -> Strip:
            return Strip([Segment(SPLASH[y], style=self.line_styles[y])])

        def on_mount(self) -> None:
            self.set_interval(interval=0.11, callback=self.refresh)

    def __init__(self) -> None:
        self.animated_fade = self.AnimatedFade(line_styles=self.create_fade())
        super().__init__()

    def compose(self) -> ComposeResult:
        with Middle():
            yield Center(self.animated_fade)
            yield Center(RichLog(name="loader log", max_lines=11))
            yield Center(
                Button(
                    id="continue",
                    label="press any key or click to continue",
                    disabled=True,
                )
            )

    def log_text(self, log_label: str) -> None:
        padding = 32 - len(log_label)
        log_text = f"{log_label} {'.' * padding} loaded"

        def update_log():
            self.screen.query_one(RichLog).write(log_text)

        self.app.call_from_thread(update_log)

    @work(thread=True, group="io_workers")
    def run_io_worker(self, arg_id) -> None:
        io_class = getattr(chezmoi, arg_id)
        io_class.update()
        self.log_text(io_class.label)
        if arg_id == "dump_config":
            global dest_dir
            dest_dir = Path(io_class.dict_out["destDir"])
            self.log_text(f"destDir={str(dest_dir)}")

    def all_workers_finished(self) -> None:
        if all(
            worker.state == "finished"
            for worker in self.app.workers
            if worker.group == "io_workers"
        ):
            self.query_one("#continue").disabled = False

    def create_fade(self) -> deque[Style]:
        start_color = Color.parse(self.app.current_theme.primary)
        end_color = Color.parse(self.app.current_theme.accent)
        fade = [start_color] * 5
        gradient = Gradient.from_colors(start_color, end_color, quality=5)
        fade.extend(gradient.colors)
        gradient.colors.reverse()
        fade.extend(gradient.colors)
        return deque([Style(color=color.hex, bold=True) for color in fade])

    def on_mount(self) -> None:
        self.set_interval(interval=0.1, callback=self.all_workers_finished)
        to_process = chezmoi.long_commands.copy()
        self.run_io_worker("dump_config")
        to_process.pop("dump_config")

        for arg_id in to_process:
            self.run_io_worker(arg_id)

    def on_key(self) -> None:
        if not self.query_one("#continue").disabled:
            self.dismiss()

    def on_click(self) -> None:
        if not self.query_one("#continue").disabled:
            self.dismiss()

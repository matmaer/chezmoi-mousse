from collections import deque
from pathlib import Path

from rich.segment import Segment
from rich.style import Style
from textual import work
from textual.app import ComposeResult
from textual.color import Gradient
from textual.containers import Center, Middle
from textual.screen import Screen
from textual.strip import Strip
from textual.widgets import RichLog, Static

from chezmoi_mousse import SPLASH
from chezmoi_mousse.chezmoi import chezmoi

start_color = "#0178D4"
end_color = "#F187FB"
fade = [start_color] * 5
gradient = Gradient.from_colors(start_color, end_color, quality=5)
fade.extend([color.hex for color in gradient.colors])
gradient.colors.reverse()
fade.extend([color.hex for color in gradient.colors])
line_styles = deque([Style(color=color, bold=True) for color in fade])
fade_height = len(SPLASH)
fade_width = len(max(SPLASH, key=len))
log_height = len(chezmoi.long_commands)
log_width = 32


class AnimatedFade(Static):

    def __init__(self) -> None:
        super().__init__()
        self.styles.height = fade_height
        self.styles.width = fade_width

    def render_lines(self, crop) -> list[Strip]:
        line_styles.rotate()
        return super().render_lines(crop)

    def render_line(self, y: int) -> Strip:
        return Strip([Segment(SPLASH[y], style=line_styles[y])])

    def on_mount(self) -> None:
        self.set_interval(interval=0.05, callback=self.refresh)


ANIMATED_FADE = AnimatedFade()
RICH_LOG = RichLog(id="loading_screen_log")
LOG_PADDING_WIDTH = 32
RICH_LOG.styles.height = len(chezmoi.long_commands) + 1
RICH_LOG.styles.width = LOG_PADDING_WIDTH + 14


class LoadingScreen(Screen):

    def __init__(self) -> None:
        self.animated_fade = ANIMATED_FADE
        self.rich_log = RICH_LOG
        self.dest_dir: Path
        super().__init__(id="loading_screen")
        self.timer = self.set_interval(
            interval=0.5, callback=self.all_workers_finished
        )

    def compose(self) -> ComposeResult:
        with Middle():
            yield Center(self.animated_fade)
            yield Center(self.rich_log)

    def log_text(self, log_label: str) -> None:
        padding = LOG_PADDING_WIDTH - len(log_label)

        def update_log():
            log_text = f"{log_label} {'.' * padding} loaded"
            RICH_LOG.write(log_text)

        self.app.call_from_thread(update_log)

    @work(thread=True, group="io_workers")
    def run_io_worker(self, arg_id) -> None:
        io_class = getattr(chezmoi, arg_id)
        io_class.update()
        self.log_text(io_class.label)

    def all_workers_finished(self) -> None:
        if all(
            worker.state == "finished"
            for worker in self.app.workers
            if worker.group == "io_workers"
        ):
            self.timer.stop()
            dest_dir = Path(chezmoi.dump_config.dict_out["destDir"])
            chezmoi.dest_dir = dest_dir
            log_label = f"destDir {dest_dir}"
            padding = LOG_PADDING_WIDTH - len(log_label)
            log_text = f"{log_label} {'.' * padding} loaded"
            RICH_LOG.write(log_text)
            # self.dismiss()

    def on_mount(self) -> None:

        for arg_id in chezmoi.long_commands:
            self.run_io_worker(arg_id)

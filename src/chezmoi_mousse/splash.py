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
fade_width = len(max(SPLASH, key=len)) - 2

LOG_HEIGHT = len(chezmoi.long_commands)
DEST_DIR: Path
LOG_PADDING_WIDTH = 36
LONG_COMMANDS = chezmoi.long_commands


class AnimatedFade(Static):

    def __init__(self) -> None:
        super().__init__()
        self.styles.height = fade_height
        self.styles.width = fade_width
        self.styles.margin = 2

    def render_lines(self, crop) -> list[Strip]:
        line_styles.rotate()
        return super().render_lines(crop)

    def render_line(self, y: int) -> Strip:
        return Strip([Segment(SPLASH[y], style=line_styles[y])])

    def on_mount(self) -> None:
        self.set_interval(interval=0.06, callback=self.refresh)


ANIMATED_FADE = AnimatedFade()

RICH_LOG = RichLog(id="loading_screen_log")
RICH_LOG.styles.height = LOG_HEIGHT + 1
RICH_LOG.styles.width = LOG_PADDING_WIDTH + 9
RICH_LOG.styles.color = "#0053AA"


class LoadingScreen(Screen):

    def __init__(self) -> None:
        self.animated_fade = ANIMATED_FADE
        self.rich_log = RICH_LOG
        super().__init__()
        self.timer = self.set_interval(
            interval=0.7, callback=self.all_workers_finished
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
            DEST_DIR = Path(chezmoi.dump_config.dict_out["destDir"])
            chezmoi.dest_dir = DEST_DIR
            log_label = f"destDir {DEST_DIR}"
            padding = LOG_PADDING_WIDTH - len(log_label)
            log_text = f"{log_label} {'.' * padding} loaded"
            RICH_LOG.write(log_text)
            self.dismiss()

    def on_mount(self) -> None:

        for arg_id in LONG_COMMANDS:
            self.run_io_worker(arg_id)

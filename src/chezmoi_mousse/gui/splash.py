import json
from collections import deque
from pathlib import Path
from subprocess import CompletedProcess, run
from typing import TYPE_CHECKING

from rich.segment import Segment
from rich.style import Style
from textual import work
from textual.app import ComposeResult
from textual.color import Gradient
from textual.containers import Center, Middle
from textual.geometry import Region
from textual.screen import Screen
from textual.strip import Strip
from textual.widgets import RichLog, Static
from textual.worker import WorkerState

from chezmoi_mousse import (
    IDS,
    AppType,
    Chezmoi,
    CommandResult,
    ParsedConfig,
    ReadCmd,
    SplashData,
    VerbArgs,
)

if TYPE_CHECKING:
    from textual.timer import Timer

__all__ = ["SplashScreen"]

SPLASH_COMMANDS: list[ReadCmd] = [
    ReadCmd.cat_config,
    ReadCmd.doctor,
    ReadCmd.dump_config,
    ReadCmd.git_log,
    ReadCmd.ignored,
    ReadCmd.managed_dirs,
    ReadCmd.managed_files,
    ReadCmd.status_dirs,
    ReadCmd.status_files,
    ReadCmd.template_data,
    ReadCmd.verify,
]

SPLASH = """\
 _______________________________ ___________________._
|       |   |   |    ___|___    |    '    |       |   |
|    ===|       |     __|     __|         |   |   |   |
|       |   |   |       |       |   |ˇ|   |       |   |
`-------^---^---^-------^-------^---' '---^-------^---'
   ____ ____ _______ ___ ___ _______ _______ _______
  |    ˇ    |       |   |   |    ___|    ___|    ___|
  |         |   |   |   |   |__     |__     |     __|
  |   |ˇ|   |       |       |       |       |       |
  '---' '---^-------^-------^-------^-------^-------'
""".replace(
    "===", "=\u200b=\u200b="
).splitlines()

FADE_HEIGHT = len(SPLASH)
FADE_WIDTH = len(max(SPLASH, key=len))
LOG_PADDING_WIDTH = 37
LOADED_SUFFIX = "loaded"


def _subprocess_run_cmd(cmd: ReadCmd) -> CommandResult:
    time_out = 1
    result: CompletedProcess[str] = run(
        cmd.value,
        capture_output=True,
        shell=False,
        text=True,
        timeout=time_out,
    )
    return CommandResult(completed_process=result, path_arg=None)


def create_deque() -> deque[Style]:
    start_color = "#0178D4"
    end_color = "#F187FB"

    fade = [start_color] * 12
    gradient = Gradient.from_colors(start_color, end_color, quality=6)
    fade.extend([color.hex for color in gradient.colors])
    gradient.colors.reverse()
    fade.extend([color.hex for color in gradient.colors])

    line_styles = deque(
        [Style(color=color, bgcolor="#000000", bold=True) for color in fade]
    )
    return line_styles


FADE_LINE_STYLES = create_deque()
cat_config: "CommandResult | None" = None
doctor: "CommandResult | None" = None
dump_config: "CommandResult | None" = None
git_log: "CommandResult | None" = None
ignored: "CommandResult | None" = None
managed_dirs: "CommandResult | None" = None
managed_files: "CommandResult | None" = None
parsed_config: "ParsedConfig | None" = None
status_dirs: "CommandResult | None" = None
status_files: "CommandResult | None" = None
template_data: "CommandResult | None" = None
verify: "CommandResult | None" = None


class AnimatedFade(Static):

    def render_lines(self, crop: Region) -> list[Strip]:
        FADE_LINE_STYLES.rotate()
        return super().render_lines(crop)

    def render_line(self, y: int) -> Strip:
        return Strip([Segment(SPLASH[y], style=FADE_LINE_STYLES[y])])

    def on_mount(self) -> None:
        self.styles.height = FADE_HEIGHT
        self.styles.width = FADE_WIDTH
        self.fade_timer: "Timer" = self.set_interval(
            interval=0.05, callback=self.refresh
        )


class SplashLog(RichLog):
    def __init__(self) -> None:
        super().__init__(id=IDS.splash.logger.splash, markup=True)

    def on_mount(self) -> None:
        self.styles.height = len(SPLASH_COMMANDS)
        self.styles.width = "auto"
        self.styles.margin = 2


class SplashScreen(Screen[SplashData | None], AppType):

    def __init__(self) -> None:
        super().__init__(id=IDS.splash.canvas_name)
        self.splash_log: SplashLog  # set in on_mount
        self.splash_data: SplashData | None = None
        self.splash_log_q = IDS.splash.logger.splash_q
        self.post_io_started: bool = False

    def compose(self) -> ComposeResult:
        with Center():
            with Middle():
                yield Center(AnimatedFade())
                yield Center(SplashLog())

    def on_mount(self) -> None:
        self.splash_log = self.query_one(self.splash_log_q, SplashLog)
        self.io_workers_timer: "Timer" = self.set_interval(
            interval=1, callback=self.all_workers_finished
        )
        if self.app.chezmoi_found is False:
            self.splash_log.styles.height = 1
            cmd_text = "chezmoi command"
            padding = LOG_PADDING_WIDTH - len(cmd_text)
            log_text = f"{cmd_text} {'.' * padding} not found"
            self.splash_log.write(log_text)
            return
        self.run_command_workers()

    @work(group="io_workers")
    async def run_command_workers(self) -> None:
        status_worker = self.run_io_worker(ReadCmd.status_files)
        await status_worker.wait()
        assert type(globals()["status_files"].exit_code) is int

        if (
            globals()["status_files"].exit_code != 0
            and self.app.init_cmd_issued is False
        ):
            # Run io workers for data used in the InitScreen
            self.run_io_worker(ReadCmd.doctor)
            self.run_io_worker(ReadCmd.template_data)
            return
        elif (
            globals()["status_files"].exit_code != 0
            and self.app.init_cmd_issued is True
        ):
            raise RuntimeError("Chezmoi cannot be initialized.")
        else:
            for splash_cmd in SPLASH_COMMANDS:
                if splash_cmd == ReadCmd.status_files:
                    continue
                self.run_io_worker(splash_cmd)

    @work(thread=True, group="io_workers")
    def run_io_worker(self, splash_cmd: ReadCmd) -> None:
        cmd_result: "CommandResult" = _subprocess_run_cmd(splash_cmd)
        cmd_text = cmd_result.pretty_cmd
        globals()[splash_cmd.name] = cmd_result
        if splash_cmd == ReadCmd.dump_config:
            parsed_config = json.loads(cmd_result.std_out)
            globals()["parsed_config"] = ParsedConfig(
                dest_dir=Path(parsed_config["destDir"]),
                git_autoadd=parsed_config["git"]["autoadd"],
                source_dir=Path(parsed_config["sourceDir"]),
                git_autocommit=parsed_config["git"]["autocommit"],
                git_autopush=parsed_config["git"]["autopush"],
            )
        elif splash_cmd in (
            ReadCmd.managed_dirs,
            ReadCmd.managed_files,
            ReadCmd.status_dirs,
            ReadCmd.status_files,
        ):
            cmd_text = cmd_result.pretty_cmd.replace(
                VerbArgs.include_dirs.value, "dirs"
            ).replace(VerbArgs.include_files.value, "files")
        padding = LOG_PADDING_WIDTH - len(cmd_text)
        log_text = f"{cmd_text} {'.' * padding} {LOADED_SUFFIX}"
        if cmd_result.exit_code == 0:
            color = self.app.theme_variables["text-primary"]
        elif cmd_result.exit_code == 1:
            if splash_cmd == ReadCmd.verify:
                color = self.app.theme_variables["text-primary"]
            else:
                color = self.app.theme_variables["text-warning"]
        else:
            color = self.app.theme_variables["text-error"]
        self.app.call_from_thread(
            self.splash_log.write, f"[{color}]{log_text}[/{color}]"
        )

    @work(thread=True, group="post_io_workers")
    def populate_chezmoi_class(self) -> None:
        self.app.chezmoi = Chezmoi(
            dev_mode=self.app.dev_mode,
            managed_dirs=globals()["managed_dirs"],
            managed_files=globals()["managed_files"],
            status_dirs=globals()["status_dirs"],
            status_files=globals()["status_files"],
        )

    @work(thread=True, group="post_io_workers")
    def construct_return_data(self):
        self.splash_data = SplashData(
            cat_config=globals()["cat_config"],
            doctor=globals()["doctor"],
            git_log=globals()["git_log"],
            ignored=globals()["ignored"],
            parsed_config=globals()["parsed_config"],
            template_data=globals()["template_data"],
            verify=globals()["verify"],
        )

    def all_workers_finished(self) -> None:
        if self.app.chezmoi_found is False:
            self.dismiss(None)
            return
        if not all(
            worker.state == WorkerState.SUCCESS
            for worker in self.screen.workers
            if worker.group == "io_workers"
        ):
            return
        if self.post_io_started is False:
            self.populate_chezmoi_class()
            self.construct_return_data()
            self.post_io_started = True
            return
        if all(
            worker.state == WorkerState.SUCCESS
            for worker in self.screen.workers
            if worker.group == "post_io_workers"
        ):
            self.post_io_started = False
            self.dismiss(self.splash_data)

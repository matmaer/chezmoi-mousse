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
from textual.timer import Timer
from textual.widgets import RichLog, Static
from textual.worker import WorkerState

from chezmoi_mousse import (
    AppType,
    Chezmoi,
    CommandResult,
    ParsedConfig,
    ReadCmd,
    SplashData,
    VerbArgs,
    WriteCmd,
)

if TYPE_CHECKING:
    from chezmoi_mousse import AppIds

__all__ = ["LoadingScreen"]

SPLASH_COMMANDS: list[ReadCmd | WriteCmd] = [
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
    WriteCmd.init,
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


def _subprocess_run_cmd(
    cmd: ReadCmd | WriteCmd, init_arg: str | None = None
) -> CommandResult:
    if cmd == WriteCmd.init and init_arg is not None:
        cmd.value.append(init_arg)
    if init_arg is not None:
        time_out = 5
    else:
        time_out = 1
    result: CompletedProcess[str] = run(
        cmd.value,
        capture_output=True,
        shell=False,
        text=True,
        timeout=time_out,
    )
    return CommandResult(completed_process_data=result, path_arg=None)


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
init: "CommandResult | None" = None
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


class LoadingScreen(Screen[SplashData | None], AppType):

    def __init__(
        self, ids: "AppIds", run_init: bool, init_arg: str | None = None
    ) -> None:
        self.ids = ids
        self.run_init = run_init
        self.fade_timer: Timer
        self.all_workers_timer: Timer
        if init_arg is not None:
            self.init_arg = init_arg
        super().__init__()

    def compose(self) -> ComposeResult:
        with Center():
            with Middle():
                yield Center(AnimatedFade())
                yield Center(RichLog(id=self.ids.logger.splash))

    @work(thread=True, group="io_workers")
    def run_threaded_cmd(self, splash_cmd: ReadCmd) -> None:
        splash_log = self.query_exactly_one(RichLog)
        cmd_result: "CommandResult" = _subprocess_run_cmd(splash_cmd)
        globals()[splash_cmd.name] = cmd_result
        padding = LOG_PADDING_WIDTH - len(cmd_result.pretty_cmd)
        log_text = f"{cmd_result.pretty_cmd} {'.' * padding} {LOADED_SUFFIX}"
        splash_log.write(log_text)

    @work(group="io_workers")
    async def run_non_threaded_cmd(
        self, splash_cmd: ReadCmd | WriteCmd
    ) -> None:
        cmd_result = _subprocess_run_cmd(splash_cmd)
        splash_log = self.query_exactly_one(RichLog)
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
        splash_log.write(log_text)

    def all_workers_finished(self) -> None:
        if all(
            worker.state == WorkerState.SUCCESS
            for worker in self.screen.workers
            if worker.group == "io_workers"
        ):
            if self.app.chezmoi_found is False:
                self.dismiss(None)
                return

            self.dismiss(
                SplashData(
                    cat_config=globals()["cat_config"],
                    doctor=globals()["doctor"],
                    executed_commands=[
                        globals()[cmd.name]
                        for cmd in SPLASH_COMMANDS
                        if globals()[cmd.name] is not None
                    ],  # used for logging in subsequent screens
                    git_log=globals()["git_log"],
                    ignored=globals()["ignored"],
                    init=globals()["init"],
                    parsed_config=globals()["parsed_config"],
                    template_data=globals()["template_data"],
                    verify=globals()["verify"],
                )
            )

    async def on_mount(self) -> None:
        middle_container = self.query_one(Middle)
        middle_container.styles.width = FADE_WIDTH
        animated_fade = self.query_exactly_one(AnimatedFade)
        animated_fade.styles.height = FADE_HEIGHT
        rich_log = self.query_exactly_one(RichLog)
        rich_log.styles.width = "auto"
        rich_log.styles.color = "#6DB2FF"
        rich_log.styles.margin = 2
        self.all_workers_timer = self.set_interval(
            interval=1, callback=self.all_workers_finished
        )
        self.fade_timer = self.set_interval(
            interval=0.05, callback=animated_fade.refresh
        )
        if self.app.chezmoi_found is True:
            rich_log.styles.height = len(SPLASH_COMMANDS)
        else:
            rich_log.styles.height = 1
            splash_log = self.query_exactly_one(RichLog)
            cmd_text = "chezmoi command"
            padding = LOG_PADDING_WIDTH - len(cmd_text)
            log_text = f"{cmd_text} {'.' * padding} not found"
            splash_log.write(log_text)
            return

        if self.run_init is True:
            run_init_worker = self.run_non_threaded_cmd(WriteCmd.init)
            await run_init_worker.wait()

        # Now run commands which output could be used on all screens
        for command in (
            ReadCmd.doctor,
            ReadCmd.ignored,
            ReadCmd.template_data,
        ):
            self.run_threaded_cmd(command)

        cat_config_worker = self.run_non_threaded_cmd(ReadCmd.cat_config)
        await cat_config_worker.wait()

        verify_worker = self.run_non_threaded_cmd(ReadCmd.verify)
        await verify_worker.wait()  # TODO: skip some commands if exit zero

        # These all need to be awaited so the Chezmoi instance can be created.
        for command in (
            ReadCmd.dump_config,
            ReadCmd.git_log,
            ReadCmd.managed_dirs,
            ReadCmd.managed_files,
            ReadCmd.status_dirs,
            ReadCmd.status_files,
        ):
            worker = self.run_non_threaded_cmd(command)
            await worker.wait()

        self.app.chezmoi = Chezmoi(
            dev_mode=self.app.dev_mode,
            managed_dirs=globals()["managed_dirs"],
            managed_files=globals()["managed_files"],
            status_dirs=globals()["status_dirs"],
            status_files=globals()["status_files"],
        )

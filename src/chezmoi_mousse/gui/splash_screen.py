import json
import urllib.request
from collections import deque
from enum import StrEnum
from pathlib import Path
from typing import TypedDict

from rich.segment import Segment
from rich.style import Style
from textual import events, work
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
    ChezmoiCommand,
    CmdResults,
    CommandResult,
    ParsedConfig,
    PathDict,
    ReadCmd,
    VerbArgs,
)

__all__ = ["SplashScreen"]

type Value = str | dict[str, "Value"]


class Node(TypedDict):
    text: str
    indent: int
    children: list["Node"]


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
""".replace("===", "=\u200b=\u200b=").splitlines()

FADE_HEIGHT = len(SPLASH)
FADE_WIDTH = len(max(SPLASH, key=len))
LOG_PADDING_WIDTH = 37
LOADED_SUFFIX = "loaded"


cat_config: "CommandResult | None" = None
doctor: "CommandResult | None" = None
dump_config: "CommandResult | None" = None
git_log: "CommandResult | None" = None
ignored: "CommandResult | None" = None
parsed_config: "ParsedConfig | None" = None
template_data: "CommandResult | None" = None
verify: "CommandResult | None" = None


class TemplateStr(StrEnum):
    """Strings to process the install help and latest chezmoi release."""

    cross_platform = "chezmoi is available in many cross-platform package managers"
    chezmoi_install_doc_url = "https://raw.githubusercontent.com/twpayne/chezmoi/refs/heads/master/assets/chezmoi.io/docs/install.md.tmpl"
    chezmoi_latest_release_url = (
        "https://api.github.com/repos/twpayne/chezmoi/releases/latest"
    )
    more_packages = "For more packages, see"
    os_install = "Install chezmoi with your package manager with a single command"
    version_tag = "{{ $version }}"


class AnimatedFade(Static):

    def __init__(self) -> None:
        super().__init__()

    def on_mount(self) -> None:
        self.styles.height = FADE_HEIGHT
        self.styles.width = FADE_WIDTH
        start_color = "#0178D4"
        end_color = "#F187FB"
        fade = [start_color] * 8
        gradient = Gradient.from_colors(start_color, end_color, quality=6)
        fade.extend([color.hex for color in gradient.colors])
        gradient.colors.reverse()
        fade.extend([color.hex for color in gradient.colors])
        self.fade_line_styles = deque(
            [Style(color=color, bgcolor="#000000", bold=True) for color in fade]
        )
        self.fade_line_styles.rotate(-2)
        self.set_interval(name="refresh_self", interval=0.1, callback=self.refresh)

    def render_lines(self, crop: Region) -> list[Strip]:
        self.fade_line_styles.rotate()
        return super().render_lines(crop)

    def render_line(self, y: int) -> Strip:
        return Strip([Segment(SPLASH[y], style=self.fade_line_styles[y])])


class SplashLog(RichLog):
    def __init__(self) -> None:
        super().__init__(id=IDS.splash.logger.splash, markup=True)

    def on_mount(self) -> None:
        self.styles.height = len(SPLASH_COMMANDS)
        self.styles.width = "auto"
        self.styles.margin = 2


class SplashScreen(Screen[None], AppType):

    def __init__(self) -> None:
        super().__init__()
        self.splash_log: SplashLog  # set in on_mount

    def _forward_event(self, event: events.Event) -> None:
        # Override textual Screen method
        # Skip all mouse events to prevent interference with animation
        if isinstance(event, events.MouseEvent):
            return
        # Allow all other events (keyboard, etc.)
        super()._forward_event(event)

    def compose(self) -> ComposeResult:
        with Middle():
            yield Center(AnimatedFade())
            yield Center(SplashLog())

    async def on_mount(self) -> None:
        self.check_workers_timer = self.set_interval(
            interval=2, callback=self.all_workers_finished
        )
        self.splash_log = self.query_one(IDS.splash.logger.splash_q, SplashLog)
        if self.app.chezmoi_found is False:
            install_help_worker = self.get_install_screen_data()
            await install_help_worker.wait()
            self.app.cmd_results = CmdResults(
                install_help_data=install_help_worker.result
            )
            self.splash_log.styles.height = 1
            cmd_text = "chezmoi command"
            padding = LOG_PADDING_WIDTH - len(cmd_text)
            self.splash_log.write(f"{cmd_text} {'.' * padding} not found")
            return

        status_worker = self.run_io_worker(ReadCmd.status_files)
        await status_worker.wait()
        if status_worker.state == WorkerState.SUCCESS:
            if (
                globals()["status_files"].exit_code != 0
                or self.app.force_init_needed is True
            ):
                self.app.init_needed = True
                self.app.force_init_needed = False
                # Run io workers for OperateScreen init commands
                self.run_io_worker(ReadCmd.doctor)
                self.run_io_worker(ReadCmd.template_data)
            else:
                for splash_cmd in SPLASH_COMMANDS:
                    if splash_cmd == ReadCmd.status_files:
                        continue
                    self.run_io_worker(splash_cmd)

    @work(thread=True, group="io_workers")
    def run_io_worker(self, splash_cmd: ReadCmd) -> None:
        chezmoi_cmd = ChezmoiCommand()
        cmd_result = chezmoi_cmd.read(splash_cmd)
        cmd_text = cmd_result.filtered_cmd
        globals()[splash_cmd.name] = cmd_result
        if splash_cmd == ReadCmd.dump_config:
            parsed_config = json.loads(cmd_result.completed_process.stdout)
            globals()["parsed_config"] = ParsedConfig(
                dest_dir=Path(parsed_config["destDir"]),
                git_auto_add=parsed_config["git"]["autoadd"],
                git_auto_commit=parsed_config["git"]["autocommit"],
                git_auto_push=parsed_config["git"]["autopush"],
                source_dir=Path(parsed_config["sourceDir"]),
            )
        elif splash_cmd in (
            ReadCmd.managed_dirs,
            ReadCmd.managed_files,
            ReadCmd.status_dirs,
            ReadCmd.status_files,
        ):
            cmd_text = cmd_result.filtered_cmd.replace(
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

    @work
    async def get_install_screen_data(self) -> dict[str, Value]:
        with urllib.request.urlopen(TemplateStr.chezmoi_latest_release_url) as response:
            data = json.load(response)
            latest_version = data.get("tag_name")

        req = urllib.request.Request(
            TemplateStr.chezmoi_install_doc_url, headers={"User-Agent": "python-urllib"}
        )
        with urllib.request.urlopen(req, timeout=2) as response:
            # After decoding the response
            content = response.read().decode("utf-8")
            # Split into lines first
            content_list = content.splitlines()
            # Then filter
            content_list = [
                line
                for line in content_list
                if line.strip() and not line.strip().startswith("```")
            ]
        # Replace template strings
        replacements: list[tuple[str, str]] = [
            (TemplateStr.version_tag, latest_version),
            ('"', ""),
            ("=== ", ""),
        ]
        for old, new in replacements:
            content_list = [line.replace(old, new) for line in content_list]
        # Strip head and tail
        first_idx = next(
            (
                i
                for i, line in enumerate(content_list)
                if line.startswith(TemplateStr.os_install)
            )
        )
        last_idx = next(
            (
                i
                for i, line in enumerate(content_list)
                if line.startswith(TemplateStr.more_packages)
            )
        )
        content_list = content_list[first_idx:last_idx]
        # Split OS-specific and cross-platform commands
        split_idx = next(
            (
                i
                for i, line in enumerate(content_list)
                if line.startswith(TemplateStr.cross_platform)
            )
        )
        # Generate result
        result = content_list[1:split_idx]  # OS-specific commands
        result.append("Cross-Platform")  # Add a header and indent cross-platform
        result.extend(f"    {line}" for line in content_list[split_idx + 1 :])
        freebsd_idx = next(
            (i for i, line in enumerate(result) if line.startswith("FreeBSD"))
        )
        # insert a list item before FreeBSD
        result.insert(freebsd_idx, "Unix-like systems")
        # increase indent for the next four lines (FreeBSD and OpenIndiana commands)
        for i in range(freebsd_idx + 1, freebsd_idx + 5):
            result[i] = f"    {result[i]}"

        root_node: Node = {"text": "", "indent": -1, "children": []}
        stack: list[Node] = [root_node]

        # construct tree data structure
        for line in result:
            indent = len(line) - len(line.lstrip(" "))
            # Pop nodes with greater or equal indentation
            while stack and indent <= stack[-1]["indent"]:
                stack.pop()
            # Add new node
            node: Node = {"text": line.strip(), "indent": indent, "children": []}
            stack[-1]["children"].append(node)  # will modify the root_node variable
            stack.append(node)

        # collapse tree into nested dictionary
        def collapse(node: Node) -> Value:
            # a node without children is the text of the command
            if not node["children"]:
                return node["text"]
            # Single child becomes its value for a nested structure
            if len(node["children"]) == 1:
                return collapse(node["children"][0])
            # Multiple children become a dictionary
            return {child["text"]: collapse(child) for child in node["children"]}

        # return final nested dict
        return {child["text"]: collapse(child) for child in root_node["children"]}

    @work(name="update_app")
    async def update_app(self) -> None:
        if self.app.init_needed is True:
            self.app.cmd_results = CmdResults(
                doctor=globals()["doctor"], template_data=globals()["template_data"]
            )
            return
        self.app.dest_dir = globals()["parsed_config"].dest_dir
        cmd_results = CmdResults(
            cat_config=globals()["cat_config"],
            doctor=globals()["doctor"],
            dump_config=globals()["dump_config"],
            git_log=globals()["git_log"],
            ignored=globals()["ignored"],
            managed_dirs=globals()["managed_dirs"],
            managed_files=globals()["managed_files"],
            status_files=globals()["status_files"],
            template_data=globals()["template_data"],
            verify=globals()["verify"],
        )
        self.app.cmd_results = cmd_results
        self.app.dest_dir = globals()["parsed_config"].dest_dir
        self.app.parsed_config = globals()["parsed_config"]
        self.app.parsed_template_data = json.loads(
            globals()["template_data"].completed_process.stdout
        )
        self.app.cmd_results.verify = globals()["verify"]

    @work
    async def update_dir_node_dict(self) -> None:
        path_dict_instance = PathDict(
            dest_dir=globals()["parsed_config"].dest_dir,
            managed_dirs_result=globals()["managed_dirs"],
            managed_files_result=globals()["managed_files"],
            status_dirs_result=globals()["status_dirs"],
            status_files_result=globals()["status_files"],
            cmd=self.app.cmd,
            theme_variables=self.app.theme_variables,
        )
        self.app.path_dict = path_dict_instance
        self.app.dir_node_dict = path_dict_instance.dir_node_dict

    def all_workers_finished(self) -> None:
        if self.app.chezmoi_found is False:
            self.dismiss(None)
            return
        if all(
            worker.state == WorkerState.SUCCESS
            for worker in self.workers
            if worker.group == "io_workers"
        ):
            update_dir_node_worker = self.update_dir_node_dict()
            if update_dir_node_worker.state != WorkerState.SUCCESS:
                return
            update_app_worker = self.update_app()
            if update_app_worker.state == WorkerState.SUCCESS:
                if all(w for w in self.workers if w.is_finished):
                    self.dismiss()
            else:
                raise RuntimeError("update_app worker did not complete successfully")

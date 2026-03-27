import json
import urllib.request
from collections import deque
from enum import StrEnum
from pathlib import Path
from typing import TYPE_CHECKING, TypedDict

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

from chezmoi_mousse import CMD, AppType, ReadCmd

from .install_help import InstallHelpScreen

if TYPE_CHECKING:
    from chezmoi_mousse import ParsedJson

__all__ = ["SplashScreen"]


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

SPLASH_LOGO = """\
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
"""

SPLASH = SPLASH_LOGO.replace("===", "=\u200b=\u200b=").splitlines()

FADE_HEIGHT = len(SPLASH)
FADE_WIDTH = len(max(SPLASH, key=len))
LOG_MSG_WIDTH = 44


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
        super().__init__(markup=True)

    def on_mount(self) -> None:
        self.styles.height = len(SPLASH_COMMANDS) + 1  # +1 for parse dump-config log
        self.styles.width = "auto"
        self.styles.margin = 2


class SplashScreen(Screen[None], AppType):

    def __init__(self) -> None:
        super().__init__()
        self.splash_log: SplashLog  # set in on_mount
        self.set_interval(interval=2, callback=self._all_workers_finished)

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

    def on_mount(self) -> None:
        self.splash_log = self.query_exactly_one(SplashLog)
        if CMD.run_cmd.chezmoi_bin is None:
            self._install_help_workers()
        else:
            self._chezmoi_found_workers()

    @work(group="io_worker")
    async def _install_help_workers(self) -> None:
        self.splash_log.styles.height = 1
        cmd_text = "chezmoi command"
        suffix = "not found"
        padding = LOG_MSG_WIDTH - (len(cmd_text) + len(suffix))
        self.splash_log.write(f"{cmd_text} {'.' * padding} {suffix}")
        install_help_worker = self._get_install_screen_data()
        await install_help_worker.wait()
        InstallHelpScreen.install_help_data = install_help_worker.result

    @work
    async def _chezmoi_found_workers(self) -> None:
        for splash_cmd in SPLASH_COMMANDS:
            self._run_io_worker(splash_cmd)

    @work(thread=True, group="io_workers")
    def _run_io_worker(self, splash_cmd: ReadCmd) -> None:
        color = self.app.theme_variables["text-primary"]
        if splash_cmd == ReadCmd.git_log and self.app.git_found is False:
            suffix = "skipped"
            short_cmd = ReadCmd.git_log.short_cmd
            padding = LOG_MSG_WIDTH - (len(short_cmd) + len(suffix))
            log_text = f"[{color}]{short_cmd} {'.' * padding} {suffix}[/{color}]"
            self.app.call_from_thread(self.splash_log.write, log_text)
            return
        result = CMD.run_cmd.read(splash_cmd)
        setattr(CMD.cache.cmd_results, f"{splash_cmd.name}", result)
        suffix = "unknown"
        if result.exit_code == 0:
            suffix = "success" if splash_cmd != ReadCmd.verify else "matches"
        else:
            suffix = "checked"
            color = self.app.theme_variables["text-warning"]
        padding = LOG_MSG_WIDTH - (len(result.short_cmd_no_path) + len(suffix))
        log_text = (
            f"[{color}]{result.short_cmd_no_path} {'.' * padding} {suffix}[/{color}]"
        )
        self.app.call_from_thread(self.splash_log.write, log_text)
        if splash_cmd == ReadCmd.dump_config:
            try:
                parsed_cfg = json.loads(result.std_out)
                CMD.cache.dest_dir = Path(parsed_cfg["destDir"])
                CMD.cache.git_auto_commit = parsed_cfg["git"]["autocommit"]
                CMD.cache.git_auto_push = parsed_cfg["git"]["autopush"]
                color = self.app.theme_variables["text-success"]
                suffix = "success"
            except (json.JSONDecodeError, KeyError, TypeError):
                color = self.app.theme_variables["text-error"]
                suffix = "not parsed"
            command = "json loads dump_config"
            padding = LOG_MSG_WIDTH - (len(command) + len(suffix))
            log_text = f"[{color}]{command} {'.' * padding} {suffix}[/{color}]"
            self.app.call_from_thread(self.splash_log.write, log_text)

    @work(thread=True, group="io_workers")
    def _get_install_screen_data(self) -> "ParsedJson":
        def get_index(seq: list[str], prefix: str) -> int:
            return next(i for i, line in enumerate(seq) if line.startswith(prefix))

        with urllib.request.urlopen(TemplateStr.chezmoi_latest_release_url) as response:
            latest_version = json.load(response).get("tag_name")

        req = urllib.request.Request(
            TemplateStr.chezmoi_install_doc_url, headers={"User-Agent": "python-urllib"}
        )
        with urllib.request.urlopen(req, timeout=2) as response:
            content_list = [
                line
                for line in response.read().decode("utf-8").splitlines()
                if line.strip() and not line.strip().startswith("```")
            ]

        replacements: list[tuple[str, str]] = [
            (TemplateStr.version_tag, latest_version),
            ('"', ""),
            ("=== ", ""),
        ]
        for old, new in replacements:
            content_list = [line.replace(old, new) for line in content_list]

        first_idx = get_index(content_list, TemplateStr.os_install)
        last_idx = get_index(content_list, TemplateStr.more_packages)
        content_list = content_list[first_idx:last_idx]

        split_idx = get_index(content_list, TemplateStr.cross_platform)

        result = content_list[1:split_idx]
        result.append("Cross-Platform")
        result.extend(f"    {line}" for line in content_list[split_idx + 1 :])

        freebsd_idx = next(
            i for i, line in enumerate(result) if line.startswith("FreeBSD")
        )
        result.insert(freebsd_idx, "Unix-like systems")
        end = min(freebsd_idx + 5, len(result))
        for i in range(freebsd_idx + 1, end):
            result[i] = f"    {result[i]}"

        root_node: Node = {"text": "", "indent": -1, "children": []}
        stack: list[Node] = [root_node]

        for line in result:
            indent = len(line) - len(line.lstrip(" "))
            while stack and indent <= stack[-1]["indent"]:
                stack.pop()
            node: Node = {"text": line.strip(), "indent": indent, "children": []}
            stack[-1]["children"].append(node)
            stack.append(node)

        def collapse(node: Node) -> "ParsedJson | str":
            if not node["children"]:
                return node["text"]
            if len(node["children"]) == 1:
                return collapse(node["children"][0])
            return {child["text"]: collapse(child) for child in node["children"]}

        return {child["text"]: collapse(child) for child in root_node["children"]}

    def _all_workers_finished(self) -> None:
        if all(
            worker.state == WorkerState.SUCCESS
            for worker in self.workers
            if worker.group == "io_workers"
        ):
            if CMD.run_cmd.chezmoi_bin is None:
                self.dismiss(None)
                return
            CMD.cache.update_path_sets()
            if all(w for w in self.workers if w.is_finished):
                self.dismiss()

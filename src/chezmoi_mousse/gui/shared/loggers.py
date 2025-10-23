import os
from datetime import datetime
from enum import StrEnum
from subprocess import CompletedProcess
from typing import TYPE_CHECKING

from rich.markup import escape
from textual.app import ComposeResult
from textual.widgets import ContentSwitcher, RichLog

from chezmoi_mousse import AppType, AreaName, Chars, LogUtils, Tcss, ViewName

if TYPE_CHECKING:
    from chezmoi_mousse import CanvasIds

__all__ = ["AppLog", "DebugLog", "OutputLog"]


class CommandLogBase(RichLog, AppType):

    def _log_time(self) -> str:
        return f"[[green]{datetime.now().strftime('%H:%M:%S')}[/]]"

    def _log_command(self, command: list[str]) -> None:
        trimmed_cmd = LogUtils.pretty_cmd_str(command)
        time = self._log_time()
        color = self.app.theme_variables["primary-lighten-3"]
        log_line = f"{time} [{color}]{trimmed_cmd}[/]"
        self.write(log_line)

    def ready_to_run(self, message: str) -> None:
        color = self.app.theme_variables["accent-darken-3"]
        self.write(f"{self._log_time()} [{color}]{message}[/]")

    def info(self, message: str) -> None:
        color = self.app.theme_variables["text-secondary"]
        self.write(f"{self._log_time()} [{color}]{message}[/]")

    def success(self, message: str) -> None:
        color = self.app.theme_variables["text-success"]
        self.write(f"{self._log_time()} [{color}]{message}[/]")

    def warning(self, message: str) -> None:
        lines = message.splitlines()
        color = self.app.theme_variables["text-warning"]
        for line in [line for line in lines if line.strip() != ""]:
            escaped_line = escape(line)
            self.write(f"{self._log_time()} [{color}]{escaped_line}[/]")

    def error(self, message: str) -> None:
        color = self.app.theme_variables["text-error"]
        time = self._log_time()
        self.write(f"{time} [{color}]{message}[/]")

    def dimmed(self, message: str) -> None:
        if message.strip() == "":
            return
        lines: list[str] = message.splitlines()
        color = self.app.theme_variables["text-disabled"]
        for line in lines:
            if line.strip() != "":
                escaped_line = escape(line)
                self.write(f"    [{color}]{escaped_line}[/]")


class AppLog(CommandLogBase, AppType):

    def __init__(self, ids: "CanvasIds") -> None:
        self.ids = ids
        super().__init__(
            id=self.ids.view_id(view=ViewName.app_log_view),
            markup=True,
            max_lines=10000,
            classes=Tcss.log_views.name,
        )
        self.succes_no_output = f"{Chars.check_mark} Success, no output"
        self.success_with_output = (
            f"{Chars.check_mark} success, output processed in UI"
        )

    def completed_process(
        self, completed_process: CompletedProcess[str]
    ) -> None:
        self._log_command(completed_process.args)
        if completed_process.returncode == 0:
            if completed_process.stdout == "":
                self.success(self.succes_no_output)
            else:
                self.success(self.success_with_output)
        else:
            self.error(
                f"{Chars.x_mark} Command failed with exit code {completed_process.returncode}, stderr logged to Output log"
            )


class DebugLog(CommandLogBase, AppType):

    type Mro = tuple[type, ...]

    def __init__(self, ids: "CanvasIds") -> None:
        self.ids = ids
        super().__init__(
            id=self.ids.view_id(view=ViewName.debug_log_view),
            markup=True,
            max_lines=10000,
            wrap=True,
            classes=Tcss.log_views.name,
        )

    def completed_process(
        self, completed_process: CompletedProcess[str]
    ) -> None:
        self._log_command(completed_process.args)
        self.dimmed(f"{dir(completed_process)}")

    def mro(self, mro: Mro) -> None:
        color = self.app.theme_variables["accent-darken-2"]
        self.write(f"{self._log_time()} [{color}]Method Resolution Order:[/]")

        exclude = {
            "typing.Generic",
            "builtins.object",
            "textual.dom.DOMNode",
            "textual.message_pump.MessagePump",
            "chezmoi_mousse.id_typing.AppType",
        }

        pretty_mro = " -> ".join(
            f"{qname}\n"
            for cls in mro
            if not any(
                e in (qname := f"{cls.__module__}.{cls.__qualname__}")
                for e in exclude
            )
        )
        self.dimmed(pretty_mro)

    def list_attr(self, obj: object) -> None:
        members = [attr for attr in dir(obj) if not attr.startswith("_")]
        self.ready_to_run(f"{obj.__class__.__name__} attributes:")
        self.dimmed(", ".join(members))

    def print_env_vars(self) -> None:
        for key, value in os.environ.items():
            self.write(f"{key}: {value}")


class OutputLog(CommandLogBase, AppType):

    def __init__(self, ids: "CanvasIds") -> None:
        self.ids = ids
        super().__init__(
            id=self.ids.view_id(view=ViewName.output_log_view),
            markup=True,
            max_lines=10000,
            classes=Tcss.log_views.name,
        )

    def _trim_stdout(self, stdout: str):
        # remove trailing and leading new lines but NOT leading whitespace
        stripped = stdout.lstrip("\n").rstrip()
        # remove intermediate empty lines
        return "\n".join(
            [line for line in stripped.splitlines() if line.strip() != ""]
        )

    def completed_process(
        self, completed_process: CompletedProcess[str], trimmed: bool = True
    ) -> None:
        if trimmed:
            completed_process.stdout = self._trim_stdout(
                completed_process.stdout
            )
            completed_process.stderr = self._trim_stdout(
                completed_process.stderr
            )
        self._log_command(completed_process.args)
        if completed_process.returncode == 0:
            self.success("success, stdout:")
            if completed_process.stdout == "":
                self.dimmed("No output on stdout")
            else:
                self.dimmed(completed_process.stdout)
        else:
            self.error("failed, stderr:")
            self.dimmed(f"{completed_process.stderr}")


class BorderTitle(StrEnum):
    app_log = " App Log "
    output_log = " Commands StdOut "
    debug_log = " Debug Log "


class LogsTabSwitcher(ContentSwitcher, AppType):

    def __init__(self, ids: "CanvasIds", dev_mode: bool):
        self.ids = ids
        self.dev_mode = dev_mode
        super().__init__(
            id=self.ids.content_switcher_id(area=AreaName.top),
            initial=self.ids.view_id(view=ViewName.app_log_view),
            classes=Tcss.border_title_top.name,
        )

    def compose(self) -> ComposeResult:
        yield AppLog(ids=self.ids)
        yield OutputLog(ids=self.ids)
        if self.dev_mode is True:
            yield DebugLog(ids=self.ids)

    def on_mount(self) -> None:
        self.border_title = BorderTitle.app_log

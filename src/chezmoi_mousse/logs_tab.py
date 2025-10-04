from datetime import datetime
from subprocess import CompletedProcess

from rich.markup import escape
from textual.widgets import RichLog

import chezmoi_mousse.custom_theme as theme
from chezmoi_mousse.id_typing import AppType
from chezmoi_mousse.id_typing.enums import (
    Chars,
    GlobalCmd,
    LogName,
    Tcss,
    VerbArgs,
)


class CommandLogBase(RichLog):

    def _log_time(self) -> str:
        return f"[[green]{datetime.now().strftime('%H:%M:%S')}[/]]"

    @staticmethod
    def pretty_cmd_str(command: list[str]) -> str:
        filter_git_log_args = VerbArgs.git_log.value[3:]
        return "chezmoi " + " ".join(
            [
                _
                for _ in command[1:]
                if _
                not in GlobalCmd.default_args.value
                + filter_git_log_args
                + [
                    VerbArgs.format_json.value,
                    VerbArgs.path_style_absolute.value,
                ]
            ]
        )

    def _log_command(self, command: list[str]) -> None:
        trimmed_cmd = self.pretty_cmd_str(command)
        time = self._log_time()
        color = theme.vars["primary-lighten-3"]
        log_line = f"{time} [{color}]{trimmed_cmd}[/]"
        self.write(log_line)

    def error(self, message: str) -> None:
        color = theme.vars["text-error"]
        time = self._log_time()
        self.write(f"{time} [{color}]{message}[/]")

    def warning(self, message: str) -> None:
        lines = message.splitlines()
        color = theme.vars["text-warning"]
        for line in [line for line in lines if line.strip()]:
            escaped_line = escape(line)
            self.write(f"{self._log_time()} [{color}]{escaped_line}[/]")

    def success(self, message: str) -> None:
        color = theme.vars["text-success"]
        self.write(f"{self._log_time()} [{color}]{message}[/]")

    def ready_to_run(self, message: str) -> None:
        color = theme.vars["accent-darken-3"]
        self.write(f"{self._log_time()} [{color}]{message}[/]")

    def dimmed(self, message: str) -> None:
        if message.strip() == "":
            return
        lines: list[str] = message.splitlines()
        color = theme.vars["text-disabled"]
        for line in lines:
            if line.strip():
                escaped_line = escape(line)
                self.write(f"[{color}]{escaped_line}[/]")


class AppLog(CommandLogBase, AppType):

    def __init__(self) -> None:
        super().__init__(
            id=LogName.app_log.name,
            markup=True,
            max_lines=10000,
            classes=Tcss.log_views,
        )
        success = f"{Chars.check_mark} Success"
        self.succes_no_output = f"{success}, no output"
        self.success_with_output = f"{success}, output processed in UI"

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

    def on_mount(self) -> None:
        self.app.chezmoi.app_log = self.completed_process


class DebugLog(CommandLogBase, AppType):

    type Mro = tuple[type, ...]

    def __init__(self) -> None:
        super().__init__(
            id=LogName.debug_log.name,
            markup=True,
            max_lines=10000,
            wrap=True,
            classes=Tcss.log_views,
        )

    def update_debug_log(self, log_message: str) -> None:
        self.write(log_message)

    def on_mount(self) -> None:
        self.app.chezmoi.debug_log = self.update_debug_log
        self.write("in debug log view")
        self.add_class(Tcss.log_views)
        self.ready_to_run("Debug log ready to capture logs.")

    def mro(self, mro: Mro) -> None:
        color = theme.vars["accent-darken-2"]
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


class OutputLog(CommandLogBase, AppType):

    def __init__(self) -> None:
        super().__init__(
            id=LogName.output_log.name,
            markup=True,
            max_lines=10000,
            classes=Tcss.log_views,
        )

    def completed_process(
        self, completed_process: CompletedProcess[str]
    ) -> None:
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
        self.refresh()

    def on_mount(self) -> None:
        self.app.chezmoi.output_log = self.completed_process

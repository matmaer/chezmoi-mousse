import inspect
import os
from datetime import datetime
from enum import StrEnum
from typing import TYPE_CHECKING

from rich.markup import escape
from textual.containers import ScrollableContainer
from textual.reactive import reactive
from textual.widgets import RichLog

from chezmoi_mousse import CMD, IDS, AppType, Chars, LogString, ReadVerb

if TYPE_CHECKING:
    from collections.abc import Callable
    from typing import Any

    from chezmoi_mousse import CommandResult

__all__ = ["AppLog", "CmdLog", "DebugLog"]


class LogColor(StrEnum):
    dimmed = "text-muted"
    error = "text-error"
    info = "text-primary"
    ready = "accent-darken-2"
    success = "text-success"
    warning = "text-warning"


class Loggers(AppType):

    @property
    def _log_time(self) -> str:
        return f"[[green]{datetime.now().strftime('%H:%M:%S')}[/]]"

    def get_log_line(self, msg: str, color: LogColor) -> str:
        msg_color = self.app.theme_variables[color.value]
        return f"{self._log_time} [{msg_color}]{msg}[/]"

    def get_dimmed_lines(self, message: str) -> str:
        if message.strip() == "":
            return ""
        lines: list[str] = message.splitlines()
        color = self.app.theme_variables[LogColor.dimmed]
        for line in lines:
            if line.strip() != "":
                escaped_line = escape(line)
                lines.append(f"[{color}]{escaped_line}[/]")
        return "  \n".join(lines)


class RichLoggers(Loggers, RichLog):

    def write_cmd(self, message: str, color: LogColor) -> None:
        self.write(self.get_log_line(message, color))

    def write_dimmed(self, message: str) -> None:
        if message.strip() == "":
            return
        self.write(self.get_dimmed_lines(message))

    def write_error(self, message: str) -> None:
        self.write(self.get_log_line(message, LogColor.error))

    def write_info(self, message: str) -> None:
        self.write(self.get_log_line(message, LogColor.info))

    def write_ready(self, message: str) -> None:
        self.write(self.get_log_line(f"--- {message} ---", LogColor.ready))

    def write_warning(self, message: str) -> None:
        self.write(self.get_log_line(message, LogColor.warning))


class AppLog(RichLoggers):

    cmd_result: reactive["CommandResult | None"] = reactive(None)

    def __init__(self) -> None:
        super().__init__(id=IDS.logs.logger.app, markup=True, max_lines=10000)

    def on_mount(self) -> None:
        self.write_ready(LogString.app_log_initialized)
        if CMD.run_cmd.chezmoi_bin is not None:
            self.write_info(LogString.using_chezmoi_bin + f" {CMD.run_cmd.chezmoi_bin}")
        if CMD.dev_mode is True:
            self.write_warning(
                f"{Chars.warning_sign} {LogString.dev_mode_enabled} "
                f"{Chars.warning_sign} "
            )

    def log_cmd_result(self, cmd_result: "CommandResult") -> None:
        cmd_color = LogColor.success if cmd_result.exit_code == 0 else LogColor.warning
        log_text: list[str] = [f"{cmd_result.short_cmd_no_path}"]

        if ReadVerb.verify.value in cmd_result.completed_process.args:
            if cmd_result.exit_code == 0:
                log_text.append(LogString.verify_exit_zero)
                cmd_color = LogColor.info
            else:
                log_text.append(LogString.verify_non_zero)
                cmd_color = LogColor.info
        elif ReadVerb.doctor.value in cmd_result.completed_process.args:
            output_lower = cmd_result.std_out.lower()
            if "error" in output_lower:
                cmd_color = LogColor.error
                log_text.append(LogString.doctor_errors_found)
            elif "failed" in output_lower:
                log_text.append(LogString.doctor_fails_found)
            elif "warning" in output_lower:
                log_text.append(LogString.doctor_warnings_found)
                cmd_color = LogColor.info
            else:
                log_text.append(LogString.doctor_no_issue_found)
                cmd_color = LogColor.success
        else:
            return
        self.write_cmd(" ".join(log_text), cmd_color)

    def watch_cmd_result(self, cmd_result: "CommandResult | None") -> None:
        if cmd_result is None:
            return
        self.log_cmd_result(cmd_result)


class CmdLog(ScrollableContainer):

    def __init__(self) -> None:
        super().__init__(id=IDS.logs.logger.cmd)

    cmd_result: reactive["CommandResult | None"] = reactive(None)

    def watch_cmd_result(self, cmd_result: "CommandResult | None") -> None:
        if cmd_result is None:
            return
        self.log_cmd_result(cmd_result)

    def log_cmd_result(self, cmd_result: "CommandResult") -> None:
        self.mount(cmd_result.pretty_collapsible)


class DebugLog(RichLoggers):

    def __init__(self) -> None:
        super().__init__(
            id=IDS.logs.logger.debug, markup=True, max_lines=10000, wrap=True
        )

    def on_mount(self) -> None:
        self.write_ready(LogString.debug_log_initialized)

    def mro(self, mro: tuple[type, ...]) -> None:
        """Parameter mro accepts self.__class__.__mro__ or SomeClass.__mro__"""
        self.write_info("Method Resolution Order:")

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
                e in (qname := f"{cls.__module__}.{cls.__qualname__}") for e in exclude
            )
        )
        self.write_dimmed(pretty_mro)

    def list_attr(
        self,
        obj: object,
        *,
        filter_text: str | None = None,
        show_method_sources: bool = False,
    ) -> None:
        members = [attr for attr in dir(obj) if not attr.startswith("_")]
        if filter_text is not None:
            members = [m for m in members if filter_text in m]

        if show_method_sources is True:
            for member_name in members:
                member = getattr(obj, member_name)
                if inspect.isroutine(member):
                    self.write_info(f"Source for method {member_name}:")
                    try:
                        source = inspect.getsource(member)
                        self.write_dimmed(source)
                    except OSError as e:
                        self.write_error("Could not retrieve source")
                        self.write_dimmed(f"{e}")

        def _type_for(name: str) -> str:
            try:
                val = getattr(obj, name)
                if inspect.isclass(val):
                    return "class"
                if inspect.ismodule(val):
                    return "module"
                if inspect.isroutine(val):
                    if show_method_sources is True:
                        self.callable_source(val)
                    return str(type(val).__name__)
                return str(type(val).__name__)
            except Exception:
                return "unknown"

        members_with_types = [f"{m}: {_type_for(m)}" for m in members]
        self.write_info(f"{obj.__class__.__name__} attributes:")
        self.write_dimmed("\n".join(members_with_types))

    def callable_source(self, callable: "Callable[..., Any]") -> None:
        self.write_info(f"Function source for {callable.__name__}:")
        try:
            source = inspect.getsource(callable)
            self.write_dimmed(source)
        except OSError as e:
            self.write_error("Could not retrieve source")
            self.write_dimmed(f"{e}")

    def print_env_vars(self) -> None:
        for key, value in os.environ.items():
            self.write(f"{key}: {value}")

import inspect
import os
from datetime import datetime
from enum import StrEnum
from typing import TYPE_CHECKING

from rich.markup import escape
from textual import work
from textual.containers import ScrollableContainer, VerticalGroup
from textual.widgets import RichLog

from chezmoi_mousse import AppType, Chars, LogString, ReadVerb, Tcss

if TYPE_CHECKING:
    from collections.abc import Callable
    from typing import Any

    from chezmoi_mousse import AppIds, CommandResult

__all__ = ["AppLog", "DebugLog", "OperateLog", "OutputCollapsible", "ReadCmdLog"]


class BorderTitle(StrEnum):
    app_log = " App Log "
    git_log_global = " Global Git Log "
    read_cmd_log = " Read Log "
    operate_log = " Operate Log "


class LoggersBase(RichLog, AppType):

    def log_time(self) -> str:
        return f"[[green]{datetime.now().strftime('%H:%M:%S')}[/]]"

    def ready_to_run(self, message: str) -> None:
        color = self.app.theme_variables["accent-darken-3"]
        self.write(f"{self.log_time()} [{color}]--- {message} ---[/]")

    def info(self, message: str) -> None:
        color = self.app.theme_variables["text-secondary"]
        self.write(f"{self.log_time()} [{color}]{message}[/]")

    def error(self, message: str, with_time: bool = True) -> None:
        color = self.app.theme_variables["text-error"]
        time = f"{self.log_time()} " if with_time else ""
        self.write(f"{time}[{color}]{message}[/]")

    def dimmed(self, message: str) -> None:
        if message.strip() == "":
            return
        lines: list[str] = message.splitlines()
        color = self.app.theme_variables["foreground-darken-2"]
        for line in lines:
            if line.strip() != "":
                escaped_line = escape(line)
                self.write(f"[{color}]{escaped_line}[/]")


class AppLog(LoggersBase, AppType):

    def __init__(self, ids: "AppIds") -> None:
        super().__init__(
            id=ids.logger.app,
            markup=True,
            max_lines=10000,
            classes=Tcss.border_title_top,
        )

    def on_mount(self) -> None:
        self.ready_to_run(LogString.app_log_initialized)
        self.border_title = BorderTitle.app_log
        if self.app.chezmoi_found:
            self.success(LogString.chezmoi_found, with_time=False)
        else:
            self.error(LogString.chezmoi_not_found, with_time=False)
        if self.app.dev_mode is True:
            self.warning(
                f"{Chars.warning_sign} {LogString.dev_mode_enabled}", with_time=False
            )

    def log_command(self, command_result: "CommandResult") -> str:
        time = self.log_time()
        color = self.app.theme_variables["primary-lighten-3"]
        return f"{time} [{color}]{command_result.pretty_cmd}[/]"

    def success(self, message: str, with_time: bool = False) -> None:
        color = self.app.theme_variables["text-success"]
        time = f"{self.log_time()} " if with_time else ""
        self.write(f"{time}[{color}]{Chars.check_mark} {message}[/]")

    def warning(self, message: str, with_time: bool = True) -> None:
        lines = message.splitlines()
        color = self.app.theme_variables["text-warning"]
        for line in [line for line in lines if line.strip() != ""]:
            time = f"{self.log_time()} " if with_time else ""
            self.write(f"{time}[{color}]{line}[/]")

    def log_cmd_results(self, command_result: "CommandResult") -> None:
        self.write(self.log_command(command_result))
        if ReadVerb.verify.value in command_result.cmd_args:
            if command_result.exit_code == 0:
                self.success(LogString.verify_exit_zero, with_time=False)
            else:
                self.success(LogString.verify_non_zero, with_time=False)
            return
        elif ReadVerb.doctor.value in command_result.cmd_args:
            output_lower = command_result.std_out.lower()
            if "error" in output_lower:
                self.error(LogString.doctor_errors_found, with_time=False)
            elif "failed" in output_lower:
                self.error(LogString.doctor_fails_found, with_time=False)
            elif "warning" in output_lower:
                self.warning(LogString.doctor_warnings_found, with_time=False)
            else:
                self.success(LogString.doctor_no_issue_found, with_time=False)
            self.dimmed(LogString.see_config_tab)
        elif command_result.exit_code == 0:
            if command_result.std_out == "":
                self.success(LogString.succes_no_output)
            else:
                self.success(LogString.success_with_output)
        if command_result.std_err != "":
            self.error(
                f"{LogString.std_err_logged}, exit code: {command_result.exit_code}"
            )


class DebugLog(LoggersBase, AppType):

    type Mro = tuple[type, ...]

    def __init__(self, ids: "AppIds") -> None:
        super().__init__(
            id=ids.logger.debug,
            markup=True,
            max_lines=10000,
            wrap=True,
            classes=Tcss.border_title_top,
        )

    def on_mount(self) -> None:
        self.ready_to_run(LogString.debug_log_initialized)

    def mro(self, mro: Mro) -> None:
        color = self.app.theme_variables["accent-darken-2"]
        self.write(f"{self.log_time()} [{color}]Method Resolution Order:[/]")

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
        self.dimmed(pretty_mro)

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
                    self.info(f"Source for method {member_name}:")
                    try:
                        source = inspect.getsource(member)
                        self.dimmed(source)
                    except OSError as e:
                        self.error("Could not retrieve source")
                        self.dimmed(f"{e}")

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
        self.info(f"{obj.__class__.__name__} attributes:")
        self.dimmed("\n".join(members_with_types))

    def callable_source(self, callable: "Callable[..., Any]") -> None:
        self.info(f"Function source for {callable.__name__}:")
        try:
            source = inspect.getsource(callable)
            self.dimmed(source)
        except OSError as e:
            self.error("Could not retrieve source")
            self.dimmed(f"{e}")

    def print_env_vars(self) -> None:
        for key, value in os.environ.items():
            self.write(f"{key}: {value}")


class OutputCollapsible(VerticalGroup, AppType):

    def __init__(self, command_result: "CommandResult") -> None:
        super().__init__(classes=Tcss.cmd_output)
        self.cmd_result = command_result

    def on_mount(self) -> None:
        self.mount(self.cmd_result.pretty_collapsible)


class OperateLog(ScrollableContainer, AppType):

    def __init__(self, ids: "AppIds") -> None:
        super().__init__(id=ids.logger.operate)

    def on_mount(self) -> None:
        self.add_class(Tcss.border_title_top)
        self.border_title = BorderTitle.operate_log

    @work
    async def log_cmd_results(self, command_result: "CommandResult") -> None:
        collapsible = OutputCollapsible(command_result)
        self.mount(collapsible)


class ReadCmdLog(ScrollableContainer, AppType):

    def __init__(self, ids: "AppIds") -> None:
        super().__init__(id=ids.logger.read)
        self.ids = ids

    def on_mount(self) -> None:
        self.add_class(Tcss.border_title_top)
        self.border_title = BorderTitle.read_cmd_log

    @work
    async def log_cmd_results(self, command_result: "CommandResult") -> None:
        self.mount(command_result.pretty_collapsible)

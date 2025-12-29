import inspect
import os
from datetime import datetime
from typing import TYPE_CHECKING

from rich.markup import escape
from textual.containers import ScrollableContainer
from textual.widgets import RichLog, Static

from chezmoi_mousse import AppType, Chars, LogStrings, ReadVerb, Tcss

from ._custom_collapsible import CustomCollapsible

if TYPE_CHECKING:
    from collections.abc import Callable
    from typing import Any

    from chezmoi_mousse import AppIds, CommandResult

__all__ = ["AppLog", "DebugLog", "OperateLog", "ReadCmdLog"]


class LoggersBase(RichLog, AppType):

    def _log_time(self) -> str:
        return f"[[green]{datetime.now().strftime('%H:%M:%S')}[/]]"

    def log_command(self, command_result: "CommandResult") -> str:
        time = self._log_time()
        color = self.app.theme_variables["primary-lighten-3"]
        return f"{time} [{color}]{command_result.pretty_cmd}[/]"

    def ready_to_run(self, message: str) -> None:
        color = self.app.theme_variables["accent-darken-3"]
        self.write(f"{self._log_time()} [{color}]--- {message} ---[/]")

    def info(self, message: str) -> None:
        color = self.app.theme_variables["text-secondary"]
        self.write(f"{self._log_time()} [{color}]{message}[/]")

    def success(self, message: str) -> None:
        color = self.app.theme_variables["text-success"]
        self.write(
            f"{self._log_time()} [{color}]{Chars.check_mark} {message}[/]"
        )

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


class AppLog(LoggersBase, AppType):

    def __init__(self, ids: "AppIds") -> None:
        super().__init__(id=ids.logger.app, markup=True, max_lines=10000)
        self.succes_no_output = "Success, no output"
        self.success_with_output = "Success, output will be processed"
        self.std_err_logged = "Command stderr available in an Output log view"
        self.verify_exit_zero = "All targets match their target state"
        self.verify_non_zero = (
            "Targets not matching their target state will be processed"
        )

    def on_mount(self) -> None:
        self.ready_to_run(LogStrings.app_log_initialized)
        if self.app.chezmoi_found:
            self.success(LogStrings.chezmoi_found)
        else:
            self.error(LogStrings.chezmoi_not_found)
        if self.app.dev_mode:
            self.warning(LogStrings.dev_mode_enabled)

    def log_doctor_exit_zero_msg(
        self, command_result: "CommandResult"
    ) -> None:
        if "error" in command_result.std_out.lower():
            self.error(
                f"{Chars.x_mark} One or more errors found, check the Config tab for details"
            )
            return
        elif "failed" in command_result.std_out.lower():
            self.warning(
                f"{Chars.warning_sign} One or more tests failed, check the Config tab for details"
            )
            return
        elif "warning" in command_result.std_out.lower():
            self.success("Only warnings found, see the Config tab")
            return
        else:
            self.success("No warnings, failed or error entries found")

    def log_cmd_results(self, command_result: "CommandResult") -> None:
        self.write(self.log_command(command_result))
        if ReadVerb.verify.value in command_result.cmd_args:
            if command_result.exit_code == 0:
                self.success(self.verify_exit_zero)
            else:
                self.success(self.verify_non_zero)
            return
        elif ReadVerb.doctor.value in command_result.cmd_args:
            if command_result.exit_code == 0:
                self.log_doctor_exit_zero_msg(command_result)
            return
        elif command_result.exit_code == 0:
            if command_result.std_out == "":
                self.success(self.succes_no_output)
            elif command_result.std_out != "":
                self.success(self.success_with_output)
        elif command_result.exit_code != 0:
            if command_result.std_err != "":
                self.error(
                    f"{self.std_err_logged}, exit code: {command_result.exit_code}"
                )
                return
            else:
                self.error(
                    f"Exit code: {command_result.exit_code}, no stderr output"
                )


class DebugLog(LoggersBase, AppType):

    type Mro = tuple[type, ...]

    def __init__(self, ids: "AppIds") -> None:
        super().__init__(
            id=ids.logger.debug, markup=True, max_lines=10000, wrap=True
        )

    def on_mount(self) -> None:
        self.ready_to_run(LogStrings.debug_log_initialized)

    def completed_process(self, command_result: "CommandResult") -> None:
        self.write(self.log_command(command_result))
        self.dimmed(f"{dir(command_result)}")

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
                        self.error(f"Could not retrieve source: {e}")

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
            self.error(f"Could not retrieve source: {e}")

    def print_env_vars(self) -> None:
        for key, value in os.environ.items():
            self.write(f"{key}: {value}")


class OperateLog(LoggersBase, AppType):

    def __init__(self, ids: "AppIds") -> None:
        super().__init__(id=ids.logger.operate, markup=True, max_lines=10000)

    def on_mount(self) -> None:
        self.ready_to_run(LogStrings.operate_log_initialized)

    def log_cmd_results(self, command_result: "CommandResult") -> None:
        self.write(self.log_command(command_result))
        if command_result.exit_code == 0:
            self.success("Success, stdout:")
            if command_result.std_out == "":
                self.dimmed("No output on stdout")
            else:
                self.dimmed(command_result.std_out)
        elif command_result.exit_code != 0:
            if command_result.std_err != "":
                self.error("Failed, stderr:")
                self.dimmed(f"{command_result.std_err}")
            else:
                self.warning("Non zero exit but no stderr output.")


class ReadOutputCollapsible(CustomCollapsible, AppType):

    def __init__(
        self, command_result: "CommandResult", output: str, counter: int
    ) -> None:
        self.command_result = command_result
        self.pretty_cmd = command_result.pretty_cmd
        self.pretty_time = command_result.pretty_time
        self.static_id = f"read_cmd_static_number_{counter}"

        super().__init__(
            Static(
                output,
                id=self.static_id,
                markup=False,
                classes=Tcss.read_cmd_static,
            ),
            title=f"{self.pretty_time} {self.pretty_cmd}",
        )

    def on_mount(self) -> None:
        collapsible_title = self.query_exactly_one("CollapsibleTitle")
        if self.command_result.exit_code == 0:
            collapsible_title.styles.color = self.app.theme_variables[
                "text-success"
            ]
        else:
            collapsible_title.styles.color = self.app.theme_variables[
                "text-warning"
            ]


class ReadCmdLog(ScrollableContainer, AppType):

    collapsible_counter: int = 0

    def __init__(self, ids: "AppIds") -> None:
        super().__init__(id=ids.logger.read)

    def log_cmd_results(self, command_result: "CommandResult") -> None:
        # Don't log verify read-verb outputs as in produces no output.
        if ReadVerb.verify.value in command_result.cmd_args:
            return

        self.collapsible_counter += 1

        output = (
            command_result.std_out
            if command_result.exit_code == 0
            else command_result.std_err
        )

        collapsible = ReadOutputCollapsible(
            command_result=command_result,
            output=output,
            counter=self.collapsible_counter,
        )
        self.mount(collapsible)

import inspect
import os
from datetime import datetime
from typing import TYPE_CHECKING

from rich.markup import escape
from textual.widgets import RichLog

from chezmoi_mousse import AppType, Chars, ReadVerbs, Tcss, ViewName

if TYPE_CHECKING:

    from collections.abc import Callable
    from typing import Any

    from chezmoi_mousse import CommandResult

    from .canvas_ids import CanvasIds

__all__ = ["AppLog", "DebugLog", "OutputLog"]


class CommandLogBase(RichLog, AppType):

    def _log_time(self) -> str:
        return f"[[green]{datetime.now().strftime('%H:%M:%S')}[/]]"

    def _log_command(self, command_result: "CommandResult") -> None:
        time = self._log_time()
        color = self.app.theme_variables["primary-lighten-3"]
        log_line = f"{time} [{color}]{command_result.pretty_cmd}[/]"
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
            f"{Chars.check_mark} Success, output will be processed"
        )
        self.std_err_logged = (
            f"{Chars.x_mark} Command stderr available in an Output log view"
        )
        self.doctor_exit_zero = f'{Chars.check_mark} No errors found by "chezmoi doctor", check the Config tab for possible warnings or failed tests'
        self.verify_exit_zero = (
            f"{Chars.check_mark} All targets match their target state"
        )
        self.verify_non_zero = f"{Chars.check_mark} Targets not matching their target state will be processed"

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
            self.success(
                f"{Chars.check_mark} Only warnings found, see the Config tab"
            )
            return
        else:
            self.success(
                f"{Chars.check_mark} No warnings, failed or error entries found"
            )

    def log_cmd_results(self, command_result: "CommandResult") -> None:
        self._log_command(command_result)
        if ReadVerbs.verify.value in command_result.cmd_args:
            if command_result.returncode == 0:
                self.success(self.verify_exit_zero)
            else:
                self.success(self.verify_non_zero)
            return
        elif ReadVerbs.doctor.value in command_result.cmd_args:
            if command_result.returncode == 0:
                self.log_doctor_exit_zero_msg(command_result)
            return
        elif command_result.returncode == 0:
            if command_result.std_out == "":
                self.success(self.succes_no_output)
            elif command_result.std_out != "":
                self.success(self.success_with_output)
        elif command_result.returncode != 0:
            if command_result.std_err != "":
                self.error(
                    f"{self.std_err_logged}, exit code: {command_result.returncode}"
                )
                return
            else:
                self.error(
                    f"Exit code: {command_result.returncode}, no stderr output"
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

    def completed_process(self, command_result: "CommandResult") -> None:
        self._log_command(command_result)
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
        if filter_text is None:
            self.dimmed(", ".join(members_with_types))
        else:
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


class OutputLog(CommandLogBase, AppType):

    def __init__(self, ids: "CanvasIds", view_name: ViewName) -> None:
        self.ids = ids
        self.view_name = view_name
        super().__init__(
            id=self.ids.view_id(view=self.view_name),
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

    def log_cmd_results(self, command_result: "CommandResult") -> None:
        if ReadVerbs.verify.value in command_result.cmd_args:
            return
        self._log_command(command_result)
        if command_result.returncode == 0:
            self.success("success, stdout:")
            if command_result.std_out == "":
                self.dimmed("No output on stdout")
            else:
                self.dimmed(command_result.std_out)
        elif command_result.returncode != 0:
            if command_result.std_err != "":
                self.error("failed, stderr:")
                self.dimmed(f"{command_result.std_err}")
            else:
                self.warning("Non zero exit but no stderr output.")

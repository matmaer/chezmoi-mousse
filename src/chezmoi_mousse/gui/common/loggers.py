from __future__ import annotations

import inspect
import os
from datetime import datetime
from typing import TYPE_CHECKING

from rich.markup import escape
from textual import getters
from textual.containers import ScrollableContainer
from textual.reactive import reactive
from textual.widgets import Collapsible, Label, RichLog, Static

from chezmoi_mousse.str_enums import Chars, LogColor, LogString, SectionLabel, Tcss

if TYPE_CHECKING:
    from collections.abc import Callable
    from typing import Any

    from chezmoi_mousse.cm_types import AppIds, ChezmoiGui, CommandResult

__all__ = ["AppLog", "CmdLog", "CmdResultCollapsible", "DebugLog"]


class CmdResultCollapsible(Collapsible):

    def __init__(self, *, cmd_result: CommandResult):
        collapsible_contents = self._collapsible_contents(cmd_result)
        super().__init__(
            *collapsible_contents,
            title=cmd_result.colored_cmd,
            collapsed_symbol=Chars.right_triangle,
            expanded_symbol=Chars.down_triangle,
        )

    def _collapsible_contents(self, result: CommandResult) -> list[Label | Static]:
        dry_run_str = "(dry run)" if result.dry_run else ""
        curated_std_out = result.std_out or f"{LogString.no_stdout} {dry_run_str}"
        curated_std_err = result.std_err or f"{LogString.no_stderr} {dry_run_str}"
        contents: list[Label | Static] = [
            Label(SectionLabel.full_cmd, classes=Tcss.sub_section_label)
        ]
        contents.extend([Label(result.full_cmd_str, classes=Tcss.full_cmd)])
        contents.extend(
            [
                Label(SectionLabel.stdout_output, classes=Tcss.sub_section_label),
                Static(f"{curated_std_out}", markup=False),
            ]
        )
        contents.extend(
            [
                Label(SectionLabel.stderr_output, classes=Tcss.sub_section_label),
                Static(f"{curated_std_err}", markup=False),
            ]
        )
        return contents


class CmdLog(ScrollableContainer):

    if TYPE_CHECKING:
        app = getters.app(ChezmoiGui)

    def __init__(self) -> None:
        super().__init__(id=self.app.cm_attr.ids.logs.richlog.cmd)

    cmd_results: reactive[list[CommandResult] | None] = reactive(None, init=False)

    def watch_cmd_results(self, cmd_results: list[CommandResult] | None) -> None:
        if cmd_results is None:
            return
        for result in cmd_results:
            self.mount(CmdResultCollapsible(cmd_result=result))


class RichLoggers(RichLog):

    if TYPE_CHECKING:
        app = getters.app(ChezmoiGui)

    def _get_log_line(self, msg: str, color: LogColor) -> str:
        log_time = f"[[green]{datetime.now().strftime('%H:%M:%S')}[/]]"
        msg_color = self.app.theme_variables[color.value]
        return f"{log_time} [{msg_color}]{msg}[/]"

    def write_color(self, message: str, color: LogColor) -> None:
        self.write(self._get_log_line(message, color))

    def write_cmd(self, message: str, color: LogColor) -> None:
        self.write(self._get_log_line(message, color))

    def write_error(self, message: str) -> None:
        self.write(self._get_log_line(message, LogColor.error))

    def write_info(self, message: str) -> None:
        self.write(self._get_log_line(message, LogColor.info))

    def write_ready(self, message: str) -> None:
        self.write(self._get_log_line(f"--- {message} ---", LogColor.ready))

    def write_warning(self, message: str) -> None:
        self.write(self._get_log_line(message, LogColor.warning))


class AppLog(RichLoggers):

    if TYPE_CHECKING:
        app = getters.app(ChezmoiGui)

    cmd_results: reactive[list[CommandResult] | None] = reactive(None, init=False)

    def __init__(self) -> None:
        super().__init__(
            id=self.app.cm_attr.ids.logs.richlog.app, markup=True, max_lines=10000
        )

    def on_mount(self) -> None:
        self.write_ready(LogString.app_log_initialized)
        if "debug" in self.app.features:
            self.write_warning(f"Running textual --dev: {LogString.debug_tab_enabled}")
            self.log_doctor_info()

    def log_doctor_info(self) -> None:
        self.write_ready("chezmoi doctor output lines")
        for line in self.app.cm_attr.splash_results.doctor.out_lines:
            if "error" in line.lower():
                self.write_error(line)
            elif "failed" in line.lower():
                self.write_warning(line)
            elif "warning" in line.lower():
                self.write_info(line)
            else:
                self.write_info(LogString.doctor_no_issue_found)
        self.write_ready("end of chezmoi doctor output")

    # TODO: implement watch_cmd_results
    def watch_cmd_results(self, cmd_results: list[CommandResult] | None) -> None:

        if cmd_results is None:
            return


class DebugLog(RichLoggers):

    def __init__(self, *, ids: AppIds) -> None:
        super().__init__(id=ids.richlog.debug, markup=True, max_lines=10000, wrap=True)

    def on_mount(self) -> None:
        self.write_ready(LogString.debug_log_initialized)

    def write_dimmed(self, message: str) -> None:
        lines: list[str] = message.splitlines()
        for line in lines:
            if line.strip() != "":
                escaped_line = escape(line)
                lines.append(f"[dim]{escaped_line}[/]")
        message = "  \n".join(lines)
        self.write(message)

    def mro(self, mro: tuple[type, ...]) -> None:
        """Parameter mro accepts self.__class__.__mro__ or SomeClass.__mro__"""
        self.write_info("Method Resolution Order:")

        exclude = {
            "typing.Generic",
            "builtins.object",
            "textual.dom.DOMNode",
            "textual.message_pump.MessagePump",
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

    def callable_source(self, callable: Callable[..., Any]) -> None:
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

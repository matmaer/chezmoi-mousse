import inspect
import os
from datetime import datetime
from enum import StrEnum
from typing import TYPE_CHECKING

from rich.markup import escape
from textual import on
from textual.app import ComposeResult
from textual.containers import ScrollableContainer, Vertical
from textual.widgets import (
    Button,
    Collapsible,
    ContentSwitcher,
    RichLog,
    Static,
)

from chezmoi_mousse import (
    AppType,
    Chars,
    ContainerName,
    ReadVerbs,
    TabBtn,
    Tcss,
    ViewName,
)
from chezmoi_mousse.shared import GitLogView, TabButtons

if TYPE_CHECKING:
    from collections.abc import Callable
    from typing import Any

    from chezmoi_mousse import CanvasIds, CommandResult

__all__ = ["LogsTab", "AppLog", "DebugLog", "OperateLog", "ReadCmdLog"]


class BorderTitle(StrEnum):
    app_log = " App Log "
    debug_log = " Debug Log "
    git_log_global = " Global Git Log "
    read_cmd_log = " Read Commands Output Log "
    operate_log = " Operate Commands Output Log "


class LoggersBase(RichLog, AppType):

    def _log_time(self) -> str:
        return f"[[green]{datetime.now().strftime('%H:%M:%S')}[/]]"

    def log_command(self, command_result: "CommandResult") -> str:
        time = self._log_time()
        color = self.app.theme_variables["primary-lighten-3"]
        return f"{time} [{color}]{command_result.pretty_cmd}[/]"
        # self.write(log_line)

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


class AppLog(LoggersBase, AppType):

    def __init__(self, ids: "CanvasIds") -> None:
        self.ids = ids
        super().__init__(
            id=self.ids.view_id(view=ViewName.app_log_view),
            markup=True,
            max_lines=10000,
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
        self.write(self.log_command(command_result))
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


class DebugLog(LoggersBase, AppType):

    type Mro = tuple[type, ...]

    def __init__(self, ids: "CanvasIds") -> None:
        self.ids = ids
        super().__init__(
            id=self.ids.view_id(view=ViewName.debug_log_view),
            markup=True,
            max_lines=10000,
            wrap=True,
        )

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


class OperateLog(LoggersBase, AppType):

    def __init__(self, ids: "CanvasIds", view_name: ViewName) -> None:
        self.ids = ids
        self.view_name = view_name
        super().__init__(
            id=self.ids.view_id(view=self.view_name),
            markup=True,
            max_lines=10000,
        )

    def log_cmd_results(self, command_result: "CommandResult") -> None:
        self.write(self.log_command(command_result))
        if command_result.returncode == 0:
            self.success("Success, stdout:")
            if command_result.std_out == "":
                self.dimmed("No output on stdout")
            else:
                self.dimmed(command_result.std_out)
        elif command_result.returncode != 0:
            if command_result.std_err != "":
                self.error("Failed, stderr:")
                self.dimmed(f"{command_result.std_err}")
            else:
                self.warning("Non zero exit but no stderr output.")


class ReadOutputCollapsible(Collapsible, AppType):

    def __init__(
        self, ids: "CanvasIds", command: str, output: str, counter: int
    ) -> None:
        self.static_id = f"read_cmd_static_number_{counter}"
        self.static_qid = f"#read_cmd_static_number_{counter}"
        self.collapsible_id = f"read_cmd_collapsible_number_{counter}"
        super().__init__(
            Static(output, id=self.static_id, markup=False),
            title=command,
            collapsed_symbol=Chars.right_triangle,
            expanded_symbol=Chars.down_triangle,
            collapsed=True,
            id=self.collapsible_id,
        )

    def on_mount(self) -> None:
        static_widget = self.query_one(self.static_qid, Static)
        static_widget.add_class("static_output")


class ReadCmdLog(ScrollableContainer, AppType):

    collapsible_counter: int = 0

    def __init__(self, ids: "CanvasIds", view_name: ViewName) -> None:
        self.ids = ids
        self.view_name = view_name
        super().__init__(id=self.ids.view_id(view=self.view_name))

        self.ids = ids
        self.view_name = view_name

    def log_cmd_results(self, command_result: "CommandResult") -> None:
        # Don't log verify read-verb outputs as in produces no output.
        if ReadVerbs.verify.value in command_result.cmd_args:
            return

        self.collapsible_counter += 1

        time_str = datetime.now().strftime("%H:%M:%S")
        command_title = f"{time_str} {command_result.pretty_cmd}"

        collapsible = ReadOutputCollapsible(
            ids=self.ids,
            command=command_title,
            output=command_result.std_out,
            counter=self.collapsible_counter,
        )
        self.mount(collapsible)


class LogsTab(Vertical, AppType):

    def __init__(self, ids: "CanvasIds") -> None:
        super().__init__()

        self.ids = ids
        self.tab_buttons = (
            TabBtn.app_log,
            TabBtn.read_cmd_log,
            TabBtn.operate_log,
            TabBtn.git_log_logs_tab,
        )
        if self.app.dev_mode is True:
            self.tab_buttons = (TabBtn.debug_log,) + self.tab_buttons
            self.initial_view_id = ids.view_id(view=ViewName.debug_log_view)
        else:
            self.initial_view_id = ids.view_id(view=ViewName.app_log_view)
        self.content_switcher_id = ids.content_switcher_id(
            name=ContainerName.logs_switcher
        )
        self.content_switcher_qid = ids.content_switcher_id(
            "#", name=ContainerName.logs_switcher
        )
        self.app_btn_id = ids.button_id(btn=TabBtn.app_log)
        self.read_btn_id = ids.button_id(btn=TabBtn.read_cmd_log)
        self.write_btn_id = ids.button_id(btn=TabBtn.operate_log)
        self.git_log_btn_id = ids.button_id(btn=TabBtn.git_log_logs_tab)
        self.debug_btn_id = ids.button_id(btn=TabBtn.debug_log)

        self.app_log_view_id = ids.view_id(view=ViewName.app_log_view)
        self.read_cmd_log_view_id = ids.view_id(
            view=ViewName.read_cmd_log_view
        )
        self.operate_log_view_id = ids.view_id(view=ViewName.operate_log_view)
        self.git_log_global_view_id = ids.view_id(view=ViewName.git_log_view)
        self.debug_log_view_id = ids.view_id(view=ViewName.debug_log_view)

    def compose(self) -> ComposeResult:
        yield TabButtons(ids=self.ids, buttons=self.tab_buttons)
        with ContentSwitcher(
            id=self.content_switcher_id,
            initial=self.initial_view_id,
            classes=Tcss.border_title_top.name,
        ):
            yield AppLog(ids=self.ids)
            yield ReadCmdLog(
                ids=self.ids, view_name=ViewName.read_cmd_log_view
            )
            yield OperateLog(ids=self.ids, view_name=ViewName.operate_log_view)
            yield GitLogView(ids=self.ids)
            if self.app.dev_mode is True:
                yield DebugLog(ids=self.ids)

    def on_mount(self) -> None:
        switcher = self.query_one(self.content_switcher_qid, ContentSwitcher)
        if self.initial_view_id == self.debug_log_view_id:
            switcher.border_title = BorderTitle.debug_log
        else:
            switcher.border_title = BorderTitle.app_log

    @on(Button.Pressed, Tcss.tab_button.value)
    def switch_content(self, event: Button.Pressed) -> None:
        event.stop()
        switcher = self.query_one(self.content_switcher_qid, ContentSwitcher)
        if event.button.id == self.app_btn_id:
            switcher.current = self.app_log_view_id
            switcher.border_title = BorderTitle.app_log
        elif event.button.id == self.read_btn_id:
            switcher.current = self.read_cmd_log_view_id
            switcher.border_title = BorderTitle.read_cmd_log
        elif event.button.id == self.write_btn_id:
            switcher.current = self.operate_log_view_id
            switcher.border_title = BorderTitle.operate_log
        elif event.button.id == self.git_log_btn_id:
            switcher.border_title = BorderTitle.git_log_global
            switcher.current = self.git_log_global_view_id
        elif (
            self.app.dev_mode is True and event.button.id == self.debug_btn_id
        ):
            switcher.current = self.debug_log_view_id
            switcher.border_title = BorderTitle.debug_log

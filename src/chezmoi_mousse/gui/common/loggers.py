from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from textual.containers import ScrollableContainer
from textual.reactive import reactive
from textual.widgets import Collapsible, Label, RichLog, Static

from chezmoi_mousse import store
from chezmoi_mousse.str_enums import Chars, ColorVar, LabelStr, LogStr, Tcss

if TYPE_CHECKING:
    from textual import getters

    from chezmoi_mousse.gui.textual_app import ChezmoiGui
    from chezmoi_mousse.named_tuples import CommandResult

__all__ = ["AppLog", "CmdLog", "RichLoggers"]


class CmdResultCollapsible(Collapsible):
    def __init__(self, *, cmd_result: CommandResult) -> None:
        collapsible_contents = self._collapsible_contents(cmd_result)
        super().__init__(
            *collapsible_contents,
            title=self._colored_with_timestamp(
                cmd_result.pretty_cmd,
                cmd_result.returncode,
                time_stamp=cmd_result.time_stamp,
            ),
            collapsed_symbol=Chars.right_triangle,
            expanded_symbol=Chars.down_triangle,
        )

    def _colored_with_timestamp(
        self, cmd_str: str, code: int | None, time_stamp: str
    ) -> str:
        if code is None:
            color = f"${ColorVar.text_error}"
        else:
            color = (
                f"${ColorVar.text_success}"
                if code == 0
                else f"${ColorVar.text_warning}"
            )
        return f"[{time_stamp}] [{color}]{cmd_str}[/] (returncode {code})"

    def _collapsible_contents(self, result: CommandResult) -> list[Label | Static]:
        curated_std_out = result.std_out or f"{LogStr.no_stdout}"
        curated_std_err = result.std_err or f"{LogStr.no_stderr}"
        contents: list[Label | Static] = [
            Label(LabelStr.full_cmd, classes=Tcss.sub_section_label)
        ]
        contents.extend([Label(result.full_cmd, classes=Tcss.full_cmd)])
        contents.extend(
            [
                Label(LabelStr.stdout_output, classes=Tcss.sub_section_label),
                Static(f"{curated_std_out}", markup=False),
            ]
        )
        contents.extend(
            [
                Label(LabelStr.stderr_output, classes=Tcss.sub_section_label),
                Static(f"{curated_std_err}", markup=False),
            ]
        )
        return contents


class CmdLog(ScrollableContainer):
    def __init__(self) -> None:
        super().__init__(id=store.logs_ids.container.cmd_log)

    cmd_result: reactive[CommandResult | None] = reactive(None, init=False)

    async def watch_cmd_result(self, cmd_result: CommandResult | None) -> None:
        if cmd_result is not None:
            self.mount(CmdResultCollapsible(cmd_result=cmd_result))


class RichLoggers(RichLog):
    if TYPE_CHECKING:
        app = getters.app(ChezmoiGui)

    def _get_log_line(self, msg: str, color: ColorVar) -> str:
        log_time = f"[[green]{datetime.now().strftime('%H:%M:%S')}[/]]"
        msg_color = self.app.theme_variables[color.value]
        return f"{log_time} [{msg_color}]{msg}[/]"

    def write_cmd(self, pretty_cmd: str, returncode: int) -> None:
        color = ColorVar.text_success if returncode == 0 else ColorVar.text_warning
        self.write(self._get_log_line(f"{pretty_cmd} (returncode {returncode})", color))

    def write_dimmed(self, message: str) -> None:
        self.write(self._get_log_line(message, ColorVar.dimmed))

    def write_error(self, message: str) -> None:
        self.write(self._get_log_line(message, ColorVar.text_error))

    def write_ready(self, message: str) -> None:
        self.write(self._get_log_line(f"--- {message} ---", ColorVar.accent_darken_2))

    def write_success(self, message: str) -> None:
        self.write(self._get_log_line(message, ColorVar.text_success))

    def write_warning(self, message: str) -> None:
        self.write(self._get_log_line(message, ColorVar.text_warning))


class AppLog(RichLoggers):
    if TYPE_CHECKING:
        app = getters.app(ChezmoiGui)

    cmd_result: reactive[CommandResult | None] = reactive(None, init=False)

    def __init__(self) -> None:
        super().__init__(id=store.logs_ids.richlog.app, markup=True, max_lines=10000)

    def on_mount(self) -> None:
        self.write_dimmed(LogStr.app_log_initialized)
        if "debug" in self.app.features:
            self.write_warning(f"Running textual --dev: {LogStr.debug_tab_enabled}")

    async def watch_cmd_result(self, cmd_result: CommandResult) -> None:
        if cmd_result.returncode == 0:
            self.write_cmd(cmd_result.pretty_cmd, cmd_result.returncode)
        if "doctor" in cmd_result.full_cmd:
            first_col: list[str] = [
                line.split()[0]
                for line in cmd_result.std_out.splitlines()
                if line.strip() != ""
            ]
            self.write_ready(LogStr.doctor_section)
            nothing_serious = True
            if "error" in first_col:
                self.write_error(LogStr.doctor_errors_found)
                nothing_serious = False
            if "failed" in first_col:
                self.write_error(LogStr.doctor_failed_found)
                nothing_serious = False
            if "warning" in first_col:
                self.write_warning(LogStr.doctor_warnings_found)
            if "not set" in cmd_result.std_out:
                self.write_warning(LogStr.doctor_not_set_found)
            if nothing_serious:
                self.write_success(LogStr.doctor_no_issue_found)
            else:
                self.write_success(LogStr.doctor_minor_issues_found)
            self.write_ready(LogStr.doctor_section.end)

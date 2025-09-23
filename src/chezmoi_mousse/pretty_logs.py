from datetime import datetime
from enum import StrEnum, auto

from rich.markup import escape
from textual.widgets import RichLog

import chezmoi_mousse.custom_theme as theme
from chezmoi_mousse.chezmoi import INIT_CFG, GlobalCmd, VerbArgs
from chezmoi_mousse.constants import BorderTitle, TcssStr, ViewName
from chezmoi_mousse.id_typing import Id, Mro, OperateHelp, TabIds


class LogIds(StrEnum):
    init_log = auto()
    operate_log = auto()


class CommandLog(RichLog):
    def __init__(
        self, *, tab_ids: TabIds | LogIds, view_name: ViewName | None = None
    ) -> None:
        self.tab_ids = tab_ids
        self.view_name = view_name
        if self.view_name is not None and isinstance(self.tab_ids, TabIds):
            self.rich_log_id = self.tab_ids.view_id(view=self.view_name)
        elif isinstance(self.tab_ids, LogIds):
            self.rich_log_id = self.tab_ids.value
        super().__init__(
            id=self.rich_log_id,
            auto_scroll=True,
            markup=True,
            max_lines=10000,
            wrap=True,
        )

    def on_mount(self) -> None:
        if self.id == LogIds.init_log:
            self.add_class(TcssStr.border_title_top)
            self.border_title = BorderTitle.init_log
            self.add_class(TcssStr.bottom_docked_log)
        elif self.id == LogIds.operate_log:
            self.add_class(TcssStr.border_title_top)
            self.border_title = BorderTitle.operante_log
            self.add_class(TcssStr.bottom_docked_log)
        elif self.tab_ids == Id.logs:
            self.add_class(TcssStr.log_views)
            if self.view_name == ViewName.app_log_view:
                if INIT_CFG.dev_mode:
                    self.ready_to_run("Running in development mode")
                if not INIT_CFG.changes_enabled:
                    self.ready_to_run(OperateHelp.changes_mode_disabled.value)
                else:
                    self.warning(OperateHelp.changes_mode_enabled.value)
            elif self.view_name == ViewName.debug_log_view:
                self.ready_to_run("Debug log ready to capture logs.")

    def _log_time(self) -> str:
        return f"[[green]{datetime.now().strftime('%H:%M:%S')}[/]]"

    def _pretty_cmd_str(self, command: list[str]) -> str:
        filter_git_log_args = VerbArgs.git_log.value[3:]
        return f"{INIT_CFG.chezmoi_cmd} " + " ".join(
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

    def command(self, command: list[str]) -> None:
        trimmed_cmd = self._pretty_cmd_str(command)
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


class DebugLog(CommandLog):

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


app_log = CommandLog(tab_ids=Id.logs, view_name=ViewName.app_log_view)
debug_log = DebugLog(tab_ids=Id.logs, view_name=ViewName.debug_log_view)
# TODO: implement output log as a list of collapsibles
output_log = CommandLog(tab_ids=Id.logs, view_name=ViewName.output_log_view)


# class CommandLogger:

#     def __init__(self, long_command: list[str], cmd_stdout: str) -> None:
#         self.long_command = long_command
#         self.cmd_stdout = cmd_stdout

#     def log_command(self):
#         app_log.command(self.long_command)
#         output_log.command(self.long_command)
#         # log all commands stdout to output_log
#         if self.cmd_stdout.strip() == "":
#             output_log.dimmed("Command returned no output on stdout")
#         else:
#             output_log.dimmed(self.cmd_stdout)
#         # handle operate logging
#         if any(verb in self.long_command for verb in OperateVerbs):
#             if (
#                 OperateVerbs.init in self.long_command
#                 or OperateVerbs.purge in self.long_command
#             ):
#                 init_log.command(self.long_command)
#             else:
#                 op_log.command(self.long_command)
#             if self.cmd_stdout.strip() == "":
#                 msg = f"{Chars.check_mark} Command made changes successfully, no output"
#                 app_log.success(msg)
#                 if (
#                     OperateVerbs.init in self.long_command
#                     or OperateVerbs.purge in self.long_command
#                 ):
#                     init_log.success(msg)
#                 else:
#                     op_log.success(msg)
#             else:
#                 app_log.success(
#                     f"{Chars.check_mark} Exit status 0, stdout logged to output log"
#                 )
#                 msg = f"{Chars.check_mark} Command ran successfully, exit status 0"
#                 if (
#                     OperateVerbs.init in self.long_command
#                     or OperateVerbs.purge in self.long_command
#                 ):
#                     init_log.success(msg)
#                     init_log.dimmed(self.cmd_stdout)
#                 else:
#                     op_log.success(msg)
#                     op_log.dimmed(self.cmd_stdout)

#         # handle IoVerb logging
#         if self.long_command in IoCmd:
#             app_log.warning(
#                 "InputOutput data updated for processing in the app"
#             )
#         elif any(verb in self.long_command for verb in ReadVerbs):
#             app_log.warning("Data available to display in the app")

#         else:
#             app_log.error("No specific logging implemented")

#         if self.cmd_stdout == "to implement dataclass":
#             e = "placeholder"
#             # log to output_log
#             output_log.command(self.long_command)
#             attribs = [
#                 a
#                 for a in dir(e)
#                 if not a.startswith("_")
#                 and a not in ["add_note", "with_traceback"]
#             ]
#             dimmed_msg = ""
#             output_log.error("An error occurred, exception data:")
#             for attr in attribs:
#                 dimmed_msg += f"{attr}:\n{getattr(e, attr)}\n"
#             output_log.dimmed(dimmed_msg)

#             # log to app_log, op_log, init_log
#             cmd_failed_msg = f"{Chars.x_mark} Command failed, exception logged to Output log, see Logs tab"

#             # log to app_log
#             app_log.command(self.long_command)
#             app_log.error(cmd_failed_msg)

#             # log to op_log or init_log
#             if any(verb in self.long_command for verb in OperateVerbs):
#                 if "init" in self.long_command:
#                     init_log.command(self.long_command)
#                     init_log.error(cmd_failed_msg)
#                 op_log.command(self.long_command)
#                 op_log.error(cmd_failed_msg)

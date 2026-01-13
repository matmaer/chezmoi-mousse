from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from subprocess import CompletedProcess, run
from typing import TYPE_CHECKING

from textual.containers import VerticalGroup
from textual.widgets import Collapsible, Label, Static

from ._app_state import AppState
from ._str_enum_names import Tcss
from ._str_enums import Chars, LogString, SectionLabel

if TYPE_CHECKING:
    from .gui.common.loggers import AppLog, OperateLog, ReadCmdLog


__all__ = [
    "ChezmoiCommand",
    "CommandResult",
    "ReadCmd",
    "ReadVerb",
    "VerbArgs",
    "WriteCmd",
    "WriteVerb",
]


class LogUtils:

    @staticmethod
    def formatted_time_str() -> str:
        return f"{datetime.now().strftime("%H:%M:%S")}"

    @staticmethod
    def pretty_time() -> str:
        return f"[$text-success][{datetime.now().strftime("%H:%M:%S")}][/]"

    @staticmethod
    def filtered_args_str(command: list[str]) -> str:
        filter_git_log_args = VerbArgs.git_log.value[3:]
        exclude = set(
            GlobalCmd.default_args.value
            + filter_git_log_args
            + [VerbArgs.format_json.value, VerbArgs.path_style_absolute.value]
        )
        return " ".join([part for part in command if part and part not in exclude])


class GlobalCmd(Enum):
    default_args = [
        "--color=off",
        "--force",
        "--interactive=false",
        "--keep-going=false",
        "--mode=file",
        "--no-pager",
        "--no-tty",
        "--progress=false",
        "--verbose=true",
        "--use-builtin-git=true",
        "--use-builtin-diff=true",
    ]
    live_run = ["chezmoi"] + default_args
    _dry_run = live_run + ["--dry-run"]
    # version = live_run + ["--version"] TODO

    @classmethod
    def base_cmd(cls) -> list[str]:
        if AppState.changes_enabled() is True:
            return cls.live_run.value
        else:
            return cls._dry_run.value


class VerbArgs(Enum):
    # encrypt = "--encrypt"
    # debug = "--debug"
    format_json = "--format=json"
    git_log = [
        "--",
        "log",
        "--date-order",
        "--format=%ar by %cn;%s",
        "--max-count=100",
        "--no-color",
        "--no-decorate",
        "--no-expand-tabs",
    ]
    include_dirs = "--include=dirs"
    include_files = "--include=files"
    init_do_not_guess = "--guess-repo-url=false"
    init_guess_https = "--guess-repo-url=true"
    init_guess_ssh = ["--guess-repo-url=true", "--ssh"]
    path_style_absolute = "--path-style=absolute"
    reverse = "--reverse"


class ReadVerb(Enum):
    cat = "cat"
    cat_config = "cat-config"
    data = "data"
    diff = "diff"
    doctor = "doctor"
    dump_config = "dump-config"
    git = "git"
    ignored = "ignored"
    managed = "managed"
    source_path = "source-path"
    status = "status"
    # unmanaged = "unmanaged"
    verify = "verify"


class ReadCmd(Enum):
    cat = [ReadVerb.cat.value]
    cat_config = [ReadVerb.cat_config.value]
    diff = [ReadVerb.diff.value]
    diff_reverse = [ReadVerb.diff.value, VerbArgs.reverse.value]
    doctor = [ReadVerb.doctor.value]
    dump_config = [VerbArgs.format_json.value, ReadVerb.dump_config.value]
    git_log = [ReadVerb.git.value] + VerbArgs.git_log.value
    ignored = [ReadVerb.ignored.value]
    managed_dirs = [
        ReadVerb.managed.value,
        VerbArgs.path_style_absolute.value,
        VerbArgs.include_dirs.value,
    ]
    managed_files = [
        ReadVerb.managed.value,
        VerbArgs.path_style_absolute.value,
        VerbArgs.include_files.value,
    ]
    source_path = [ReadVerb.source_path.value]
    status_dirs = [
        ReadVerb.status.value,
        VerbArgs.path_style_absolute.value,
        VerbArgs.include_dirs.value,
    ]
    status_files = [
        ReadVerb.status.value,
        VerbArgs.path_style_absolute.value,
        VerbArgs.include_files.value,
    ]
    template_data = [ReadVerb.data.value]
    # unmanaged = [ReadVerb.unmanaged.value, VerbArgs.path_style_absolute.value]
    verify = [ReadVerb.verify.value]

    @property
    def pretty_cmd(self) -> str:
        return f"[$success]chezmoi {LogUtils.filtered_args_str(self.value)}[/]"


class WriteVerb(Enum):
    add = "add"
    apply = "apply"
    destroy = "destroy"
    forget = "forget"
    init = "init"
    re_add = "re-add"


class WriteCmd(Enum):
    add = [WriteVerb.add.value]
    apply = [WriteVerb.apply.value]
    destroy = [WriteVerb.destroy.value]
    forget = [WriteVerb.forget.value]
    init_guess_https = [WriteVerb.init.value, VerbArgs.init_guess_https.value]
    init_guess_ssh = [WriteVerb.init.value] + VerbArgs.init_guess_ssh.value
    init_new = [WriteVerb.init.value]
    init_no_guess = [WriteVerb.init.value, VerbArgs.init_do_not_guess.value]
    re_add = [WriteVerb.re_add.value]

    @property
    def pretty_cmd(self) -> str:
        return (
            f"[$text-success bold]"
            f"{LogUtils.filtered_args_str(GlobalCmd.base_cmd() + self.value)}[/]"
        )

    @property
    def subprocess_arguments(self) -> list[str]:
        return GlobalCmd.base_cmd() + self.value


def _run_chezmoi_cmd(
    command: list[str], read_cmd: ReadCmd | None, write_cmd: WriteCmd | None
) -> CompletedProcess[str]:
    if read_cmd is not None and read_cmd != ReadCmd.doctor:
        time_out = 2
    elif read_cmd == ReadCmd.doctor:
        time_out = 4
    elif write_cmd is not None:
        time_out = 7
    else:
        raise ValueError("Both read_cmd and write_cmd are None")
    return run(command, capture_output=True, shell=False, text=True, timeout=time_out)


@dataclass(slots=True)
class CommandResult:
    completed_process: CompletedProcess[str]
    write_cmd: bool

    def __post_init__(self) -> None:
        self.completed_process.stdout = self.get_text(self.completed_process.stdout)
        self.completed_process.stderr = self.get_text(self.completed_process.stderr)

    def has_text(self, s: str) -> bool:
        return s != "" and not s.isspace()

    def get_text(self, output: str) -> str:
        if not self.has_text(output):
            return ""
        lines = output.splitlines()
        # Remove leading lines with no text
        start = 0
        while start < len(lines) and not self.has_text(lines[start]):
            start += 1
        # Remove trailing lines with no text
        end = len(lines)
        while end > start and not self.has_text(lines[end - 1]):
            end -= 1
        return "\n".join(lines[start:end])

    @property
    def cmd_args(self) -> list[str]:
        return self.completed_process.args

    @property  # merely a shortcut for easy access
    def std_out(self) -> str:
        return self.completed_process.stdout

    @property  # merely a shortcut for easy access
    def std_err(self) -> str:
        return self.completed_process.stderr

    @property
    def pretty_collapsible_title(self) -> str:
        if self.exit_code == 0:
            return f"{LogUtils.pretty_time()} [$text-success]{self.pretty_cmd}[/]"
        else:
            return f"{LogUtils.pretty_time()} [$text-warning]{self.pretty_cmd}[/]"

    @property
    def dry_run(self) -> bool:
        return "--dry-run" in self.cmd_args

    @property
    def exit_code(self) -> int:
        return self.completed_process.returncode

    @property
    def pretty_cmd(self) -> str:
        return f"{LogUtils.filtered_args_str(self.cmd_args)}"

    @property
    def pretty_collapsible(self) -> VerticalGroup:
        collapsible_contents: list[Label | Static] = []
        stdout_empty = (
            LogString.no_stdout_write_cmd_dry
            if self.write_cmd is True and self.dry_run is True
            else LogString.no_stdout
        )
        stderr_empty = (
            LogString.no_stderr_write_cmd_dry
            if self.write_cmd is True and self.dry_run is True
            else LogString.no_stderr
        )
        std_out_text = self.std_out if self.std_out != "" else stdout_empty
        std_err_text = self.std_err if self.std_err != "" else stderr_empty
        collapsible_contents.extend(
            [
                Label(SectionLabel.stdout_output, classes=Tcss.sub_section_label),
                Static(f"{std_out_text}"),
            ]
        )
        collapsible_contents.extend(
            [
                Label(SectionLabel.stderr_output, classes=Tcss.sub_section_label),
                Static(f"{std_err_text}"),
            ]
        )
        return VerticalGroup(
            Collapsible(
                *collapsible_contents,
                title=self.pretty_collapsible_title,
                collapsed_symbol=Chars.right_triangle,
                expanded_symbol=Chars.down_triangle,
                collapsed=True,
            )
        )


class ChezmoiCommand:

    def __init__(self) -> None:
        self.app = AppState.get_app()
        self.app_log: AppLog | None = None
        self.read_cmd_log: ReadCmdLog | None = None
        self.operate_log: OperateLog | None = None

    #################################
    # Command execution and logging #
    #################################

    def _log_read_cmd(self, result: CommandResult):
        if self.app_log is None or self.read_cmd_log is None:
            return
        self.read_cmd_log.log_cmd_results(result)
        self.app_log.log_cmd_results(result)

    def _log_write_cmd(self, result: CommandResult):
        if self.app_log is None or self.operate_log is None:
            return
        self.operate_log.log_cmd_results(result)
        self.app_log.log_cmd_results(result)

    def read(self, read_cmd: ReadCmd, *, path_arg: Path | None = None) -> CommandResult:
        base_cmd = GlobalCmd.live_run.value  # read commands always run live
        command = base_cmd + read_cmd.value
        if path_arg is not None:
            command += [str(path_arg)]
        result: CompletedProcess[str] = _run_chezmoi_cmd(
            command, read_cmd=read_cmd, write_cmd=None
        )
        command_result = CommandResult(completed_process=result, write_cmd=False)
        self._log_read_cmd(command_result)
        return command_result

    def perform(
        self,
        write_cmd: WriteCmd,
        *,
        path_arg: str | None = None,
        init_arg: str | None = None,
    ) -> CommandResult:
        if write_cmd == WriteCmd.init_new:
            command: list[str] = GlobalCmd.base_cmd() + write_cmd.value
            if init_arg is not None:
                command: list[str] = GlobalCmd.base_cmd() + write_cmd.value + [init_arg]
        elif init_arg is None:
            if path_arg is None:
                command: list[str] = GlobalCmd.base_cmd() + write_cmd.value
            else:
                command: list[str] = (
                    GlobalCmd.base_cmd() + write_cmd.value + [str(path_arg)]
                )
        else:
            raise ValueError("Invalid arguments for perform()")

        result: CompletedProcess[str] = _run_chezmoi_cmd(
            command, read_cmd=None, write_cmd=write_cmd
        )
        command_result = CommandResult(completed_process=result, write_cmd=True)
        self._log_write_cmd(command_result)
        if write_cmd in (
            WriteCmd.add,
            WriteCmd.apply,
            WriteCmd.destroy,
            WriteCmd.forget,
            WriteCmd.re_add,
        ):
            if self.app is None:
                raise ValueError("self.app is None")
            if self.app.dest_dir is None:
                raise ValueError("self.app.dest_dir is None")
            self.app.managed.update_path_dict(
                managed_dirs=self.read(ReadCmd.managed_dirs).std_out,
                managed_files=self.read(ReadCmd.managed_files).std_out,
                status_dirs=self.read(ReadCmd.status_dirs).std_out,
                status_files=self.read(ReadCmd.status_files).std_out,
            )
        return command_result

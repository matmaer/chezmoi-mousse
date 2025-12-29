from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from subprocess import CompletedProcess, run
from typing import TYPE_CHECKING

from ._app_state import AppState
from ._chezmoi_paths import ChezmoiPaths

if TYPE_CHECKING:
    from .gui.tabs.logs_tab import AppLog, DebugLog, OperateLog, ReadCmdLog

__all__ = [
    "ChezmoiCommand",
    "CommandResult",
    "GlobalCmd",
    "ReadCmd",
    "ReadVerb",
    "VerbArgs",
    "WriteCmd",
    "WriteVerb",
]


class LogUtils:

    @staticmethod
    def pretty_cmd_str(command: list[str]) -> str:
        filter_git_log_args = VerbArgs.git_log.value[3:]
        exclude = set(
            GlobalCmd.default_args.value
            + filter_git_log_args
            + [VerbArgs.format_json.value, VerbArgs.path_style_absolute.value]
            + VerbArgs.diff.value
        )
        return " ".join(
            [part for part in command if part and part not in exclude]
        )


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
        "--use-builtin-git=true",
    ]
    live_run = ["chezmoi"] + default_args
    dry_run = live_run + ["--dry-run"]
    # version = live_run + ["--version"] TODO


class VerbArgs(Enum):
    # encrypt = "--encrypt"
    # debug = "--debug"
    diff = ["--use-builtin-diff", "--no-pager"]
    format_json = "--format=json"
    git_log = [
        "--",
        "--no-pager",
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
    init_guess_ssh = ["--ssh"]
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
    unmanaged = "unmanaged"
    verify = "verify"


class ReadCmd(Enum):
    cat = [ReadVerb.cat.value]
    cat_config = [ReadVerb.cat_config.value]
    diff = [ReadVerb.diff.value] + VerbArgs.diff.value
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
    unmanaged = [ReadVerb.unmanaged.value, VerbArgs.path_style_absolute.value]
    verify = [ReadVerb.verify.value]

    @property
    def pretty_cmd(self) -> str:
        return f"{GlobalCmd.live_run.value[0]} {LogUtils.pretty_cmd_str(self.value)}"


class WriteVerb(Enum):
    add = "add"
    apply = "apply"
    destroy = "destroy"
    forget = "forget"
    init = "init"
    re_add = "re-add"


# class WriteCmd(Enum):
#     add = GlobalCmd.dry_run.value + [WriteVerb.add.value]
#     add_live = GlobalCmd.live_run.value + [WriteVerb.add.value]
#     apply_dry = GlobalCmd.dry_run.value + [WriteVerb.apply.value]
#     apply_live = GlobalCmd.live_run.value + [WriteVerb.apply.value]
#     destroy_dry = GlobalCmd.dry_run.value + [WriteVerb.destroy.value]
#     destroy_live = GlobalCmd.live_run.value + [WriteVerb.destroy.value]
#     forget_dry = GlobalCmd.dry_run.value + [WriteVerb.forget.value]
#     forget_live = GlobalCmd.live_run.value + [WriteVerb.forget.value]
#     init_guess_https = [WriteVerb.init.value]
#     init_guess_ssh = [WriteVerb.init.value] + VerbArgs.init_guess_ssh.value
#     init_new = [WriteVerb.init.value]
#     init_no_guess = [WriteVerb.init.value, VerbArgs.init_do_not_guess.value]
#     re_add_dry = GlobalCmd.dry_run.value + [WriteVerb.re_add.value]
#     re_add_live = GlobalCmd.live_run.value + [WriteVerb.re_add.value]


class WriteCmd(Enum):
    add_dry = GlobalCmd.dry_run.value + [WriteVerb.add.value]
    add_live = GlobalCmd.live_run.value + [WriteVerb.add.value]
    apply_dry = GlobalCmd.dry_run.value + [WriteVerb.apply.value]
    apply_live = GlobalCmd.live_run.value + [WriteVerb.apply.value]
    destroy_dry = GlobalCmd.dry_run.value + [WriteVerb.destroy.value]
    destroy_live = GlobalCmd.live_run.value + [WriteVerb.destroy.value]
    forget_dry = GlobalCmd.dry_run.value + [WriteVerb.forget.value]
    forget_live = GlobalCmd.live_run.value + [WriteVerb.forget.value]
    init_guess_https = [WriteVerb.init.value]
    init_guess_ssh = [WriteVerb.init.value] + VerbArgs.init_guess_ssh.value
    init_new = [WriteVerb.init.value]
    init_no_guess = [WriteVerb.init.value, VerbArgs.init_do_not_guess.value]
    re_add_dry = GlobalCmd.dry_run.value + [WriteVerb.re_add.value]
    re_add_live = GlobalCmd.live_run.value + [WriteVerb.re_add.value]

    @property
    def pretty_cmd(self) -> str:
        return LogUtils.pretty_cmd_str(self.value)

    # @classmethod
    # def base_cmd(cls) -> list[str]:
    #     if AppState.changes_enabled() is True:
    #         return cls.live_run.value
    #     else:
    #         return cls.dry_run.value


@dataclass(slots=True)
class CommandResult:
    completed_process: CompletedProcess[str]
    stripped_std_out: str
    stripped_std_err: str
    pretty_time: str = f"[{datetime.now().strftime('%H:%M:%S')}]"
    read_cmd: ReadCmd | None = None
    write_cmd: WriteCmd | None = None

    @property
    def cmd_args(self) -> list[str]:
        return self.completed_process.args

    @property
    def dry_run(self) -> bool:
        return "--dry-run" in self.cmd_args

    @property
    def exit_code(self) -> int:
        return self.completed_process.returncode

    @property
    def pretty_cmd(self) -> str:
        return LogUtils.pretty_cmd_str(self.cmd_args)

    @property
    def std_out(self) -> str:
        if self.stripped_std_out == "" and "--dry-run" in self.cmd_args:
            return "No output on stdout, command was executed with --dry-run."
        elif self.stripped_std_out == "":
            return "No output on stdout."
        else:
            return self.stripped_std_out

    @property
    def std_err(self) -> str:
        if self.stripped_std_err == "":
            return "No output on stderr."
        else:
            return self.stripped_std_err


class ChezmoiCommand:

    def __init__(self, *, dev_mode: bool) -> None:
        self._dev_mode = dev_mode

        self.app_log: AppLog | None = None
        self.read_cmd_log: ReadCmdLog | None = None
        self.operate_log: OperateLog | None = None
        if self._dev_mode is True:
            self.debug_log: DebugLog | None = None

    #################################
    # Command execution and logging #
    #################################

    def _log_in_app_and_read_cmd_log(self, result: CommandResult):
        if self.app_log is not None and self.read_cmd_log is not None:
            self.app_log.log_cmd_results(result)
            self.read_cmd_log.log_cmd_results(result)

    def _log_in_app_and_operate_log(self, result: CommandResult):
        if self.app_log is not None and self.operate_log is not None:
            self.app_log.log_cmd_results(result)
            self.operate_log.log_cmd_results(result)

    def update_managed_paths(self) -> None:
        ChezmoiPaths.managed_dirs_result = self.read(ReadCmd.managed_dirs)
        ChezmoiPaths.managed_files_result = self.read(ReadCmd.managed_files)

    def update_status_paths(self) -> None:
        ChezmoiPaths.status_files_result = self.read(ReadCmd.status_files)
        ChezmoiPaths.status_dirs_result = self.read(ReadCmd.status_dirs)

    @staticmethod
    def strip_output(cmd_output: str):
        # remove trailing space and new lines but NOT leading whitespace
        stripped = cmd_output.lstrip("\n").rstrip()
        # remove intermediate empty lines
        return "\n".join(
            [line for line in stripped.splitlines() if line.strip() != ""]
        )

    def read(
        self, read_cmd: ReadCmd, *, path_arg: Path | None = None
    ) -> CommandResult:
        base_cmd = GlobalCmd.live_run.value
        command = base_cmd + read_cmd.value
        if path_arg is not None:
            command += [str(path_arg)]
        if read_cmd == ReadCmd.doctor:
            time_out = 4
        else:
            time_out = 2
        result: CompletedProcess[str] = run(
            command,
            capture_output=True,
            shell=False,
            text=True,
            timeout=time_out,
        )
        stripped_stdout = self.strip_output(result.stdout)
        stripped_stderr = self.strip_output(result.stderr)
        command_result = CommandResult(
            completed_process=result,
            read_cmd=read_cmd,
            stripped_std_err=stripped_stderr,
            stripped_std_out=stripped_stdout,
        )
        self._log_in_app_and_read_cmd_log(command_result)
        return command_result

    def perform(
        self,
        write_cmd: WriteCmd,
        *,
        path_arg: Path | None = None,
        init_arg: str | None = None,
    ) -> CommandResult:
        if AppState.changes_enabled() is True:
            base_cmd = GlobalCmd.live_run.value
        else:
            base_cmd = GlobalCmd.dry_run.value
        if (
            write_cmd
            in (
                WriteCmd.add_dry,
                WriteCmd.add_live,
                WriteCmd.apply_dry,
                WriteCmd.apply_live,
                WriteCmd.destroy_dry,
                WriteCmd.destroy_live,
                WriteCmd.forget_dry,
                WriteCmd.forget_live,
                WriteCmd.re_add_dry,
                WriteCmd.re_add_live,
            )
            and path_arg is not None
        ):
            command: list[str] = write_cmd.value + [str(path_arg)]
        elif write_cmd == WriteCmd.init_new:
            command: list[str] = base_cmd + write_cmd.value
        elif (
            write_cmd
            in (
                WriteCmd.init_guess_https,
                WriteCmd.init_guess_ssh,
                WriteCmd.init_no_guess,
            )
            and init_arg is not None
        ):
            command: list[str] = base_cmd + write_cmd.value + [init_arg]
        else:
            raise ValueError("Invalid arguments for perform()")

        result: CompletedProcess[str] = run(
            command, capture_output=True, shell=False, text=True, timeout=5
        )
        stripped_stdout = self.strip_output(result.stdout)
        stripped_stderr = self.strip_output(result.stderr)
        command_result = CommandResult(
            completed_process=result,
            stripped_std_err=stripped_stderr,
            stripped_std_out=stripped_stdout,
            write_cmd=write_cmd,
        )
        self._log_in_app_and_operate_log(command_result)
        # if write_cmd == WriteCmd.add_live:
        #     self.update_managed_paths()
        # elif (
        #     write_cmd in (WriteCmd.apply_live, WriteCmd.re_add_live)
        #     and path_arg is not None
        # ):
        #     self.update_status_paths()
        # elif (
        #     write_cmd in (WriteCmd.destroy_live, WriteCmd.forget_live)
        #     and path_arg is not None
        # ):
        #     self.update_status_paths()
        #     self.update_managed_paths()
        return command_result

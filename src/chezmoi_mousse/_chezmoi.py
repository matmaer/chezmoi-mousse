from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from subprocess import CompletedProcess, run
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .gui.tabs.logs_tab import AppLog, DebugLog, OperateLog, ReadCmdLog

type PathDict = "dict[Path, str]"
type PathList = "list[Path]"

__all__ = [
    "Chezmoi",
    "CommandResult",
    "GlobalCmd",
    "PathDict",
    "ReadCmd",
    "ReadVerbs",
    "VerbArgs",
    "WriteCmd",
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

    @staticmethod
    def strip_output(stdout: str):
        # remove trailing space and new lines but NOT leading whitespace
        stripped = stdout.lstrip("\n").rstrip()
        # remove intermediate empty lines
        return "\n".join(
            [line for line in stripped.splitlines() if line.strip() != ""]
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


class ReadVerbs(Enum):
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
    verify = "verify"


class ReadCmd(Enum):
    cat = GlobalCmd.live_run.value + [ReadVerbs.cat.value]
    cat_config = GlobalCmd.live_run.value + [ReadVerbs.cat_config.value]
    diff = (
        GlobalCmd.live_run.value + [ReadVerbs.diff.value] + VerbArgs.diff.value
    )
    diff_reverse = GlobalCmd.live_run.value + [
        ReadVerbs.diff.value,
        VerbArgs.reverse.value,
    ]
    doctor = GlobalCmd.live_run.value + [ReadVerbs.doctor.value]
    dump_config = GlobalCmd.live_run.value + [
        VerbArgs.format_json.value,
        ReadVerbs.dump_config.value,
    ]
    git_log = (
        GlobalCmd.live_run.value
        + [ReadVerbs.git.value]
        + VerbArgs.git_log.value
    )
    ignored = GlobalCmd.live_run.value + [ReadVerbs.ignored.value]
    managed_dirs = GlobalCmd.live_run.value + [
        ReadVerbs.managed.value,
        VerbArgs.path_style_absolute.value,
        VerbArgs.include_dirs.value,
    ]
    managed_files = GlobalCmd.live_run.value + [
        ReadVerbs.managed.value,
        VerbArgs.path_style_absolute.value,
        VerbArgs.include_files.value,
    ]
    source_path = GlobalCmd.live_run.value + [ReadVerbs.source_path.value]
    status_dirs = GlobalCmd.live_run.value + [
        ReadVerbs.status.value,
        VerbArgs.path_style_absolute.value,
        VerbArgs.include_dirs.value,
    ]
    status_files = GlobalCmd.live_run.value + [
        ReadVerbs.status.value,
        VerbArgs.path_style_absolute.value,
        VerbArgs.include_files.value,
    ]
    template_data = GlobalCmd.live_run.value + [ReadVerbs.data.value]
    verify = GlobalCmd.live_run.value + [ReadVerbs.verify.value]
    # version = GlobalCmd.version.value TODO

    @property
    def pretty_cmd(self) -> str:
        return LogUtils.pretty_cmd_str(self.value)


class WriteVerbs(Enum):
    add = "add"
    apply = "apply"
    destroy = "destroy"
    forget = "forget"
    init = "init"
    re_add = "re-add"


class WriteCmd(Enum):
    add_dry = GlobalCmd.dry_run.value + [WriteVerbs.add.value]
    add_live = GlobalCmd.live_run.value + [WriteVerbs.add.value]
    apply_dry = GlobalCmd.dry_run.value + [WriteVerbs.apply.value]
    apply_live = GlobalCmd.live_run.value + [WriteVerbs.apply.value]
    destroy_dry = GlobalCmd.dry_run.value + [WriteVerbs.destroy.value]
    destroy_live = GlobalCmd.live_run.value + [WriteVerbs.destroy.value]
    forget_dry = GlobalCmd.dry_run.value + [WriteVerbs.forget.value]
    forget_live = GlobalCmd.live_run.value + [WriteVerbs.forget.value]
    init_guess_https = [WriteVerbs.init.value]
    init_guess_ssh = [WriteVerbs.init.value] + VerbArgs.init_guess_ssh.value
    init_new = [WriteVerbs.init.value]
    init_no_guess = [WriteVerbs.init.value, VerbArgs.init_do_not_guess.value]
    re_add_dry = GlobalCmd.dry_run.value + [WriteVerbs.re_add.value]
    re_add_live = GlobalCmd.live_run.value + [WriteVerbs.re_add.value]

    @property
    def pretty_cmd(self) -> str:
        return LogUtils.pretty_cmd_str(self.value)


@dataclass(slots=True)
class CommandResult:
    completed_process: CompletedProcess[str]
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
        stripped_stdout = LogUtils.strip_output(self.completed_process.stdout)
        if stripped_stdout == "" and "--dry-run" in self.cmd_args:
            return "No output on stdout, command was executed with --dry-run."
        elif stripped_stdout == "":
            return "No output on stdout."
        else:
            return stripped_stdout

    @property
    def std_err(self) -> str:
        stripped_stderr = LogUtils.strip_output(self.completed_process.stderr)
        if stripped_stderr == "" and "--dry-run" in self.cmd_args:
            return "No output on stderr, command was executed with --dry-run."
        elif stripped_stderr == "":
            return ""
        else:
            return stripped_stderr


class Chezmoi:

    def __init__(
        self,
        *,
        dev_mode: bool,
        managed_dirs: CommandResult,
        managed_files: CommandResult,
        status_dirs: CommandResult,
        status_files: CommandResult,
    ) -> None:
        self._dev_mode = dev_mode
        self._managed_dirs_result = managed_dirs
        self._managed_files_result = managed_files
        self._status_dirs_result = status_dirs
        self._status_files_result = status_files

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

    ############################
    # MANAGED AND STATUS PATHS #
    ############################

    @property
    def dirs(self) -> "PathList":
        return [
            Path(line)
            for line in self._managed_dirs_result.std_out.splitlines()
        ]

    @property
    def files(self) -> "PathList":
        return [
            Path(line)
            for line in self._managed_files_result.std_out.splitlines()
        ]

    @property
    def status_dirs(self) -> "PathDict":
        return {
            Path(line[3:]): line[:2]
            for line in self._status_dirs_result.std_out.splitlines()
            if line.strip() != ""
        }

    @property
    def status_files(self) -> "PathDict":
        return {
            Path(line[3:]): line[:2]
            for line in self._status_files_result.std_out.splitlines()
            if line.strip() != ""
        }

    # properties filtering status files into apply and re-add contexts

    @property
    def apply_status_files(self) -> "PathDict":
        return {
            path: status_pair[1]
            for path, status_pair in self.status_files.items()
            if status_pair[1] in "ADM"  # Check second character only
        }

    @property
    def re_add_status_files(self) -> "PathDict":
        # consider these files to have a status as chezmoi re-add can be run
        return {
            path: status_pair[0]
            for path, status_pair in self.status_files.items()
            if (
                status_pair[0] == "M"
                or (status_pair[0] == " " and status_pair[1] in "ADM")
            )
            and path.exists()
        }

    # properties filtering status dirs into apply and re-add contexts

    @property
    def apply_status_dirs(self) -> "PathDict":
        real_status_dirs = {
            path: status_pair[1]
            for path, status_pair in self.status_dirs.items()
            if status_pair[1] in "ADM"  # Check second character only
        }
        dirs_with_status_files = {
            file_path.parent: " "
            for file_path, _ in self.apply_status_files.items()
            if file_path.parent not in real_status_dirs
        }
        return {**real_status_dirs, **dirs_with_status_files}

    @property
    def re_add_status_dirs(self) -> "PathDict":
        # Dir status is not relevant to the re-add command, just return any
        # parent dir that contains re-add status files
        # Return those directories with status " "
        # No need to check for existence, as files within must exist
        return {
            file_path.parent: " "
            for file_path in self.re_add_status_files.keys()
        }

    # properties for files without status
    @property
    def apply_files_without_status(self) -> "PathDict":
        return {
            path: "X"
            for path in self.files
            if path not in self.apply_status_files.keys()
        }

    @property
    def re_add_files_without_status(self) -> "PathDict":
        return {
            path: "X"
            for path in self.files
            if path not in self.re_add_status_files.keys()
        }

    # concat dicts, files override dirs on key collisions, should never happen
    @property
    def apply_status_paths(self) -> "PathDict":
        return {**self.apply_status_dirs, **self.apply_status_files}

    @property
    def re_add_status_paths(self) -> "PathDict":
        return {**self.re_add_status_dirs, **self.re_add_status_files}

    def apply_status_dirs_in(self, dir_path: Path) -> "PathDict":
        return {
            path: status
            for path, status in self.apply_status_dirs.items()
            if path.parent == dir_path
        }

    def apply_status_files_in(self, dir_path: Path) -> "PathDict":
        return {
            path: status
            for path, status in self.apply_status_files.items()
            if path.parent == dir_path
        }

    def re_add_status_files_in(self, dir_path: Path) -> "PathDict":
        return {
            path: status
            for path, status in self.re_add_status_files.items()
            if path.parent == dir_path
        }

    def re_add_status_dirs_in(self, dir_path: Path) -> "PathDict":
        return {
            path: status
            for path, status in self.re_add_status_dirs.items()
            if path.parent == dir_path
        }

    def apply_files_without_status_in(self, dir_path: Path) -> "PathDict":
        return {
            path: status
            for path, status in self.apply_files_without_status.items()
            if path.parent == dir_path
        }

    def re_add_files_without_status_in(self, dir_path: Path) -> "PathDict":
        return {
            path: status
            for path, status in self.re_add_files_without_status.items()
            if path.parent == dir_path
        }

    def has_apply_status_paths_in(self, dir_path: Path) -> bool:
        # Return True if any apply-status path is a descendant of the
        # provided directory.
        return any(
            status_path.is_relative_to(dir_path)
            for status_path in self.apply_status_paths.keys()
        )

    def has_re_add_status_paths_in(self, dir_path: Path) -> bool:
        # Same logic as for apply: return True if any re-add status path
        # is a descendant of dir_path.
        return any(
            status_path.is_relative_to(dir_path)
            for status_path in self.re_add_status_paths.keys()
        )

    def list_apply_status_paths_in(self, dir_path: Path) -> PathDict:
        # Return a dict of apply-status paths that are descendants of the
        # provided directory, mapping path -> status.
        return {
            path: status
            for path, status in self.apply_status_paths.items()
            if path.is_relative_to(dir_path)
        }

    def list_re_add_status_paths_in(self, dir_path: Path) -> PathDict:
        # Return a dict of re-add-status paths that are descendants of dir_path,
        # mapping path -> status.
        return {
            path: status
            for path, status in self.re_add_status_paths.items()
            if path.is_relative_to(dir_path)
        }

    def update_managed_paths(self) -> None:
        self._managed_dirs_result: CommandResult = self.read(
            ReadCmd.managed_dirs
        )
        self._managed_files_result: CommandResult = self.read(
            ReadCmd.managed_files
        )
        self._status_files_result: CommandResult = self.read(
            ReadCmd.status_files
        )
        self._status_dirs_result: CommandResult = self.read(
            ReadCmd.status_dirs
        )

    def read(
        self, read_cmd: ReadCmd, *, path_arg: Path | None = None
    ) -> CommandResult:
        command: list[str] = read_cmd.value
        if path_arg is None:
            command: list[str] = command
        else:
            command: list[str] = command + [str(path_arg)]
        if read_cmd == ReadCmd.doctor:
            time_out = 3
        else:
            time_out = 1
        result: CompletedProcess[str] = run(
            command,
            capture_output=True,
            shell=False,
            text=True,
            timeout=time_out,
        )
        command_result = CommandResult(
            completed_process=result, read_cmd=read_cmd
        )
        self._log_in_app_and_read_cmd_log(command_result)
        return command_result

    def perform(
        self,
        write_cmd: WriteCmd,
        *,
        path_arg: Path | None = None,
        init_arg: str | None = None,
        changes_enabled: bool,
    ) -> CommandResult:
        if changes_enabled is True:
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
        command_results = CommandResult(
            completed_process=result, write_cmd=write_cmd
        )
        self._log_in_app_and_operate_log(command_results)
        return command_results

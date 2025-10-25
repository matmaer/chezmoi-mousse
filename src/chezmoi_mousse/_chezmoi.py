from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from subprocess import CompletedProcess, run
from typing import TYPE_CHECKING

from chezmoi_mousse._names import Canvas

if TYPE_CHECKING:
    from chezmoi_mousse._names import ActiveCanvas

    from .gui.logs_tab import AppLog, DebugLog, OutputLog

type PathDict = dict[Path, str]

__all__ = [
    "WriteCmd",
    "Chezmoi",
    "CommandResults",
    "GlobalCmd",
    "LogUtils",
    "ManagedPaths",
    "ReadCmd",
    "ReadVerbs",
    "VerbArgs",
]


class GlobalCmd(Enum):
    default_args = [
        "--color=off",
        "--force",
        "--interactive=false",
        "--mode=file",
        "--no-pager",
        "--no-tty",
        "--progress=false",
    ]
    live_run = ["chezmoi"] + default_args
    dry_run = live_run + ["--dry-run"]


class VerbArgs(Enum):
    # encrypt = "--encrypt"
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


class ReadCmd(Enum):
    cat = GlobalCmd.live_run.value + [ReadVerbs.cat.value]
    cat_config = GlobalCmd.live_run.value + [ReadVerbs.cat_config.value]
    diff = GlobalCmd.live_run.value + [ReadVerbs.diff.value]
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
    status_paths = GlobalCmd.live_run.value + [
        ReadVerbs.status.value,
        VerbArgs.path_style_absolute.value,
    ]
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


class WriteCmd(Enum):
    add = ["add"]
    # add_encrypt = ["add", VerbArgs.encrypt.value]
    apply = ["apply"]
    destroy = ["destroy"]
    forget = ["forget"]
    init = ["init"]
    re_add = ["re-add"]


class LogUtils:

    @staticmethod
    def pretty_cmd_str(command: list[str]) -> str:
        filter_git_log_args = VerbArgs.git_log.value[3:]
        return "chezmoi " + " ".join(
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

    @staticmethod
    def strip_output(stdout: str):
        # remove trailing space and new lines but NOT leading whitespace
        stripped = stdout.lstrip("\n").rstrip()
        # remove intermediate empty lines
        return "\n".join(
            [line for line in stripped.splitlines() if line.strip() != ""]
        )


@dataclass
class CommandResults:
    completed_process_data: CompletedProcess[str]
    path_arg: Path | None

    @property
    def cmd_args(self) -> list[str]:
        return self.completed_process_data.args

    @property
    def pretty_cmd(self) -> str:
        return self._pretty_cmd_str(self.completed_process_data.args)

    @property
    def std_out(self) -> str:
        stripped_stdout = LogUtils.strip_output(
            self.completed_process_data.stdout
        )
        if (
            stripped_stdout == ""
            and "--dry-run" in self.completed_process_data.args
        ):
            return "No output on stdout, command was executed with --dry-run."
        elif stripped_stdout == "":
            return "No output on stdout."
        else:
            return stripped_stdout

    @property
    def std_err(self) -> str:
        stripped_stderr = self._strip_output(
            self.completed_process_data.stderr
        )
        if (
            stripped_stderr == ""
            and "--dry-run" in self.completed_process_data.args
        ):
            return "No output on stderr, command was executed with --dry-run."
        elif stripped_stderr == "":
            return "No output on stderr."
        else:
            return stripped_stderr

    @property
    def returncode(self) -> int:
        return self.completed_process_data.returncode

    def _strip_output(self, output: str):
        # remove trailing and leading new lines but NOT leading whitespace
        stripped = output.lstrip("\n").rstrip()
        # remove intermediate empty lines
        return "\n".join(
            [line for line in stripped.splitlines() if line.strip() != ""]
        )

    def _pretty_cmd_str(self, command_args: list[str]) -> str:
        filter_git_log_args = VerbArgs.git_log.value[3:]
        return "chezmoi " + " ".join(
            [
                _
                for _ in command_args[1:]
                if _
                not in GlobalCmd.default_args.value
                + filter_git_log_args
                + [
                    VerbArgs.format_json.value,
                    VerbArgs.path_style_absolute.value,
                ]
            ]
        )


@dataclass
class ManagedPaths:
    managed_dirs_stdout: str = ""  # ReadCmd.managed_dirs
    managed_files_stdout: str = ""  # ReadCmd.managed_files
    status_dirs_stdout: str = ""  # ReadCmd.status_dirs
    status_files_stdout: str = ""  # ReadCmd.status_files

    # caches corresponding to the stdout fields
    _cached_managed_dirs: list[Path] | None = None
    _cached_managed_files: list[Path] | None = None
    _cached_status_dirs_dict: PathDict | None = None
    _cached_status_files_dict: PathDict | None = None

    # caches splitting status into apply and re-add contexts
    _cached_apply_status_dirs: PathDict | None = None
    _cached_apply_status_files: PathDict | None = None
    _cached_re_add_status_dirs: PathDict | None = None
    _cached_re_add_status_files: PathDict | None = None

    # caches derived from the split status contexts
    _cached_apply_files_without_status: list[Path] | None = None
    _cached_re_add_files_without_status: list[Path] | None = None

    # other caches
    _cached_apply_status_paths: PathDict | None = None
    _cached_re_add_status_paths: PathDict | None = None

    def clear_cache(self) -> None:
        # clear caches corresponding to the stdout fields
        self._cached_managed_dirs = None
        self._cached_managed_files = None
        self._cached_status_dirs_dict = None
        self._cached_status_files_dict = None

        # clear caches splitting status into apply and re-add contexts
        self._cached_apply_status_dirs = None
        self._cached_apply_status_files = None
        self._cached_re_add_status_dirs = None
        self._cached_re_add_status_files = None

        # clear caches derived from the split status contexts
        self._cached_apply_files_without_status = None
        self._cached_re_add_files_without_status = None

        # clear other caches
        self._cached_apply_status_paths = None
        self._cached_re_add_status_paths = None

    # properties corresponding to the stdout fields

    @property
    def dirs(self) -> list[Path]:
        if self._cached_managed_dirs is None:
            self._cached_managed_dirs = [
                Path(line) for line in self.managed_dirs_stdout.splitlines()
            ]
        return self._cached_managed_dirs

    @property
    def files(self) -> list[Path]:
        if self._cached_managed_files is None:
            self._cached_managed_files = [
                Path(line) for line in self.managed_files_stdout.splitlines()
            ]
        return self._cached_managed_files

    @property
    def status_dirs(self) -> PathDict:
        if self._cached_status_dirs_dict is None:
            self._cached_status_dirs_dict = {
                Path(line[3:]): line[:2]
                for line in self.status_dirs_stdout.splitlines()
                if line.strip() != ""
            }
        return self._cached_status_dirs_dict

    @property
    def status_files(self) -> PathDict:
        if self._cached_status_files_dict is None:
            self._cached_status_files_dict = {
                Path(line[3:]): line[:2]
                for line in self.status_files_stdout.splitlines()
                if line.strip() != ""
            }
        return self._cached_status_files_dict

    # properties filtering status dirs into apply and re-add contexts

    @property
    def apply_status_dirs(self) -> PathDict:
        if self._cached_apply_status_dirs is None:
            self._cached_apply_status_dirs = {
                path: status_pair[1]
                for path, status_pair in self.status_dirs.items()
                if status_pair[1] in "ADM"  # Check second character only
            }
        return self._cached_apply_status_dirs

    @property
    def re_add_status_dirs(self) -> PathDict:
        # consider these dirs to always have status M
        # Existence for re-add operations will be checked later on.
        if self._cached_re_add_status_dirs is None:
            self._cached_re_add_status_dirs = {
                path: status_pair[0]
                for path, status_pair in self.status_dirs.items()
                if status_pair[0] == "M"
                or (status_pair[0] == " " and status_pair[1] in "ADM")
            }
        return self._cached_re_add_status_dirs

    # properties filtering status files into apply and re-add contexts

    @property
    def apply_status_files(self) -> PathDict:
        if self._cached_apply_status_files is None:
            self._cached_apply_status_files = {
                path: status_pair[1]
                for path, status_pair in self.status_files.items()
                if status_pair[1] in "ADM"  # Check second character only
            }
        return self._cached_apply_status_files

    @property
    def re_add_status_files(self) -> PathDict:
        # consider these files to have a status as chezmoi apply can be run.
        # Existence for re-add operations will be checked later on.
        if self._cached_re_add_status_files is None:
            self._cached_re_add_status_files = {
                path: status_pair[0]
                for path, status_pair in self.status_files.items()
                if status_pair[0] == "M"
                or (status_pair[0] == " " and status_pair[1] in "ADM")
            }
        return self._cached_re_add_status_files

    # properties for files without status, in apply and re-add contexts

    @property
    def apply_files_without_status(self) -> list[Path]:
        if self._cached_apply_files_without_status is None:
            self._cached_apply_files_without_status = [
                path
                for path in self.files
                if path not in self.apply_status_files
            ]
        return self._cached_apply_files_without_status

    @property
    def re_add_files_without_status(self) -> list[Path]:
        if self._cached_re_add_files_without_status is None:
            self._cached_re_add_files_without_status = [
                path
                for path in self.files
                if path not in self.re_add_status_files
            ]
        return self._cached_re_add_files_without_status

    # concat dicts, files override dirs on key collisions, should never happen
    @property
    def apply_status_paths(self) -> PathDict:
        return {**self.apply_status_dirs, **self.apply_status_files}

    @property
    def re_add_status_paths(self) -> PathDict:
        return {**self.re_add_status_dirs, **self.re_add_status_files}


class Chezmoi:

    def __init__(self, *, changes_enabled: bool, dev_mode: bool) -> None:

        self._changes_enabled = changes_enabled
        self._dev_mode = dev_mode
        self.managed_paths = ManagedPaths()
        self.app_log: AppLog | None = None
        self.output_log: OutputLog | None = None
        if self._dev_mode is True:
            self.debug_log: DebugLog | None = None

    #################################
    # Command execution and logging #
    #################################

    def _log_in_app_and_output_log(self, result: CommandResults):
        if self.app_log is not None and self.output_log is not None:
            self.app_log.log_cmd_results(result)
            self.output_log.log_cmd_results(result)

    def read(
        self, read_cmd: ReadCmd, path_arg: Path | None = None
    ) -> CommandResults:
        command: list[str] = read_cmd.value
        if path_arg is not None:
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
        command_results = CommandResults(
            completed_process_data=result, path_arg=path_arg
        )
        self._log_in_app_and_output_log(command_results)
        return command_results

    def perform(
        self,
        write_sub_cmd: WriteCmd,
        *,
        path_arg: Path | None = None,
        repo_url: str | None = None,
    ) -> CommandResults:
        if self._changes_enabled is True:
            base_cmd: list[str] = GlobalCmd.live_run.value
        else:
            base_cmd: list[str] = GlobalCmd.dry_run.value
        command: list[str] = base_cmd + write_sub_cmd.value

        if write_sub_cmd != WriteCmd.init and path_arg is not None:
            command: list[str] = command + [str(path_arg)]
        elif write_sub_cmd == WriteCmd.init and repo_url is not None:
            command: list[str] = command + [repo_url]

        result: CompletedProcess[str] = run(
            command, capture_output=True, shell=False, text=True, timeout=5
        )
        command_results = CommandResults(
            completed_process_data=result, path_arg=path_arg
        )
        self._log_in_app_and_output_log(command_results)
        return command_results

    def all_status_files(self, active_canvas: "ActiveCanvas") -> PathDict:
        if active_canvas == Canvas.apply:
            return self.managed_paths.apply_status_files
        else:
            return self.managed_paths.re_add_status_files

    def status_dirs_in(
        self, active_canvas: "ActiveCanvas", dir_path: Path
    ) -> PathDict:
        if active_canvas == Canvas.apply:
            result = {
                path: status
                for path, status in self.managed_paths.apply_status_dirs.items()
                if path.parent == dir_path
            }
            # Add dirs that contain status files but don't have direct status
            for path in self.managed_paths.dirs:
                if (
                    path.parent == dir_path
                    and path not in result
                    and self._has_apply_status_files_in(path)
                ):
                    result[path] = " "
            return dict(sorted(result.items()))
        else:
            result = {
                path: status
                for path, status in self.managed_paths.re_add_status_dirs.items()
                if path.parent == dir_path and path.exists()
            }
            # Add dirs that contain status files but don't have direct status
            for path in self.managed_paths.dirs:
                if (
                    path.parent == dir_path
                    and path not in result
                    and path.exists()
                    and self._has_re_add_status_files_in(path)
                ):
                    result[path] = " "
            return dict(sorted(result.items()))

    def dirs_without_status_in(
        self, active_canvas: "ActiveCanvas", dir_path: Path
    ) -> PathDict:
        if active_canvas == Canvas.apply:
            status_dirs = self.managed_paths.apply_status_dirs
            has_status_check = self._has_apply_status_files_in
        else:
            status_dirs = self.managed_paths.re_add_status_dirs
            has_status_check = self._has_re_add_status_files_in

        result = {
            path: "X"
            for path in self.managed_paths.dirs
            if path.parent == dir_path
            and path not in status_dirs
            and not has_status_check(path)
        }
        # For re_add canvas, filter out non-existing directories
        if active_canvas == Canvas.re_add:
            result = {
                path: status
                for path, status in result.items()
                if path.exists()
            }
        return result

    def _has_apply_status_files_in(self, dir_path: Path) -> bool:
        return any(
            path.is_relative_to(dir_path)
            for path in self.managed_paths.apply_status_files.keys()
        )

    def _has_re_add_status_files_in(self, dir_path: Path) -> bool:
        # Create this list without calling exists()
        potential_files = [
            path
            for path in self.managed_paths.re_add_status_files.keys()
            if path.is_relative_to(dir_path)
        ]
        # Check if any of the potential files exist
        return any(path.exists() for path in potential_files)

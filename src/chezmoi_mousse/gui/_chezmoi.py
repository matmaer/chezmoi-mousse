from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from subprocess import CompletedProcess, run
from typing import Literal

from chezmoi_mousse import (
    ChangeCmd,
    GlobalCmd,
    PaneBtn,
    PathDict,
    ReadCmd,
    SplashReturnData,
)

# TODO: implement 'chezmoi verify', if exit 0, display message in Tree
# widgets inform the user why the Tree widget is empty
# TODO: implement spinner for commands taking a bit longer like operations


__all__ = ["Chezmoi"]


@dataclass
class DirPathStatus:
    path: Path
    status: str


@dataclass
class FilePathStatus:
    path: Path
    status: str


@dataclass
class ManagedStatus:

    dirs: list[Path] = field(default_factory=list[Path])
    files: list[Path] = field(default_factory=list[Path])
    status_dirs: list[DirPathStatus] = field(
        default_factory=list[DirPathStatus]
    )
    status_files: list[FilePathStatus] = field(
        default_factory=list[FilePathStatus]
    )


class Chezmoi:

    def __init__(self, *, changes_enabled: bool) -> None:
        self.changes_enabled = changes_enabled

        self.app_log: Callable[[CompletedProcess[str]], None] | None = None
        self.debug_log: Callable[[CompletedProcess[str]], None] | None = None
        self.output_log: Callable[[CompletedProcess[str]], None] | None = None

        self.managed = ManagedStatus()

    # COMMAND TYPES

    @property
    def _read_cmd(self) -> type[ReadCmd]:
        return ReadCmd

    @property
    def _change_cmd(self) -> type[ChangeCmd]:
        return ChangeCmd

    # CACHED CHEZMOI CMD OUTPUTS

    @property
    def apply_dirs(self) -> PathDict:
        return self._create_status_dict(PaneBtn.apply_tab, "dirs")

    @property
    def apply_files(self) -> PathDict:
        return self._create_status_dict(PaneBtn.apply_tab, "files")

    @property
    def re_add_dirs(self) -> PathDict:
        return self._create_status_dict(PaneBtn.re_add_tab, "dirs")

    @property
    def re_add_files(self) -> PathDict:
        return self._create_status_dict(PaneBtn.re_add_tab, "files")

    # METHODS

    def _strip_stdout(self, stdout: str):
        # remove trailing and leading new lines but NOT leading whitespace
        stripped = stdout.lstrip("\n").rstrip()
        # remove intermediate empty lines
        return "\n".join(
            [line for line in stripped.splitlines() if line.strip()]
        )

    def _log_in_app_and_output_log(self, result: CompletedProcess[str]):
        result.stdout = self._strip_stdout(result.stdout)
        if self.app_log is not None:
            self.app_log(result)
        if self.output_log is not None:
            self.output_log(result)

    def read(self, read_cmd: ReadCmd, path: Path | None = None) -> str:
        command: list[str] = read_cmd.value
        if path is not None:
            command: list[str] = command + [str(path)]
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
        self._log_in_app_and_output_log(result)
        return self._strip_stdout(result.stdout)

    def perform(
        self, change_sub_cmd: ChangeCmd, change_arg: str | None = None
    ) -> None:
        if self.changes_enabled:
            base_cmd: list[str] = GlobalCmd.live_run.value
        else:
            base_cmd: list[str] = GlobalCmd.dry_run.value
        command: list[str] = base_cmd + change_sub_cmd.value

        if change_arg is not None:
            command: list[str] = command + [change_arg]

        self._log_in_app_and_output_log(
            run(
                command, capture_output=True, shell=False, text=True, timeout=5
            )
        )

    def refresh_managed(
        self, splash_data: SplashReturnData | None = None
    ) -> None:
        if splash_data is not None:
            self.managed.dirs = [
                Path(line) for line in splash_data.managed_dirs.splitlines()
            ]
            self.managed.files = [
                Path(line) for line in splash_data.managed_files.splitlines()
            ]
            self.managed.status_dirs = [
                DirPathStatus(Path(line[3:]), line[:2])
                for line in splash_data.dir_status_lines.splitlines()
            ]
            self.managed.status_files = [
                FilePathStatus(Path(line[3:]), line[:2])
                for line in splash_data.file_status_lines.splitlines()
            ]
            return
        # get data from chezmoi managed stdout
        self.managed.dirs = [
            Path(line) for line in self.read(ReadCmd.managed_dirs).splitlines()
        ]
        self.managed.files = [
            Path(line)
            for line in self.read(ReadCmd.managed_files).splitlines()
        ]
        # get data from chezmoi status stdout
        self.managed.status_dirs = [
            DirPathStatus(Path(line[3:]), line[:2])
            for line in self.read(ReadCmd.dir_status_lines).splitlines()
        ]
        self.managed.status_files = [
            FilePathStatus(Path(line[3:]), line[:2])
            for line in self.read(ReadCmd.file_status_lines).splitlines()
        ]

    def files_with_status_in(
        self, tab_name: str, dir_path: Path
    ) -> list[Path]:
        files_dict: PathDict = {}
        if tab_name == PaneBtn.apply_tab.name:
            files_dict = self.apply_files
        elif tab_name == PaneBtn.re_add_tab.name:
            files_dict = self.re_add_files
        return [
            p
            for p, status in files_dict.items()
            if status != "X" and p.parent == dir_path
        ]

    def files_without_status_in(
        self, tab_name: str, dir_path: Path
    ) -> list[Path]:
        files_dict: PathDict = {}
        if tab_name == PaneBtn.apply_tab.name:
            files_dict = self.apply_files
        elif tab_name == PaneBtn.re_add_tab.name:
            files_dict = self.re_add_files
        return [
            p
            for p, status in files_dict.items()
            if status == "X" and p.parent == dir_path
        ]

    def managed_dirs_in(self, dir_path: Path) -> list[Path]:
        # checks only direct children
        return [p for p in self.managed.dirs if p.parent == dir_path]

    def _create_status_dict(
        self,
        tab_name: Literal[PaneBtn.apply_tab, PaneBtn.re_add_tab],
        kind: Literal["dirs", "files"],
    ) -> PathDict:
        path_dict: PathDict = {}
        status_idx: int = 0
        status_codes: str = ""
        if kind == "dirs":
            managed_paths = self.managed.dirs
            status_lines = [
                p.status + " " + str(p.path) for p in self.managed.status_dirs
            ]
        elif kind == "files":
            managed_paths = self.managed.files
            status_lines = [
                p.status + " " + str(p.path) for p in self.managed.status_files
            ]

        if tab_name == PaneBtn.apply_tab:
            status_codes = "ADM"
            status_idx = 1
        elif tab_name == PaneBtn.re_add_tab:
            status_codes = "M"
            status_idx = 0

        paths_with_status_dict = {}
        if tab_name == PaneBtn.re_add_tab:
            # For re_add_tab, include files with "M" at status_idx=0 OR
            # files with space at status_idx=0 AND "M" at status_idx=1
            for line in status_lines:
                if line[status_idx] in status_codes or (
                    line[status_idx] == " " and line[1] == "M"
                ):
                    paths_with_status_dict[Path(line[3:])] = (
                        line[status_idx]
                        if line[status_idx] != " "
                        else line[1]
                    )
        else:
            paths_with_status_dict = {
                Path(line[3:]): line[status_idx]
                for line in status_lines
                if line[status_idx] in status_codes
            }

        for path in managed_paths:
            if path in paths_with_status_dict:
                path_dict[path] = paths_with_status_dict[path]
            else:
                path_dict[path] = "X"
        return path_dict

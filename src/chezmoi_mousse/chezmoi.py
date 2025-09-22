import json
import os
import tempfile
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from shutil import which
from subprocess import CompletedProcess, run
from typing import Literal

from chezmoi_mousse.constants import IoVerbs, OperateVerbs, ReadVerbs, TabName
from chezmoi_mousse.id_typing import ParsedJson, PathDict

CHEZMOI_CMD = "chezmoi"


class GlobalCmd(Enum):
    chezmoi = [CHEZMOI_CMD]
    default_args = [
        "--color=off",
        "--force",
        "--interactive=false",
        "--mode=file",
        "--no-pager",
        "--no-tty",
        "--progress=false",
    ]
    live_run = chezmoi + default_args
    dry_run = live_run + ["--dry-run"]


class VerbArgs(Enum):
    encrypt = "--encrypt"
    format_json = "--format=json"
    git_log = [
        "--",
        "--no-pager",
        "log",
        "--date-order",
        "--format=%ar by %cn;%s",
        "--max-count=50",
        "--no-color",
        "--no-decorate",
        "--no-expand-tabs",
    ]
    include_dirs = "--include=dirs"
    include_files = "--include=files"
    path_style_absolute = "--path-style=absolute"
    reverse = "--reverse"


class ReadCmd(Enum):
    cat = GlobalCmd.live_run.value + [ReadVerbs.cat]
    cat_config = GlobalCmd.live_run.value + [ReadVerbs.cat_config]
    data = GlobalCmd.live_run.value + [ReadVerbs.data]
    diff = GlobalCmd.live_run.value + [ReadVerbs.diff]
    diff_reverse = GlobalCmd.live_run.value + [
        ReadVerbs.diff,
        VerbArgs.reverse.value,
    ]
    dir_status_lines = GlobalCmd.live_run.value + [
        IoVerbs.status,
        VerbArgs.path_style_absolute.value,
        VerbArgs.include_dirs.value,
    ]
    doctor = GlobalCmd.live_run.value + [IoVerbs.doctor]
    dump_config = GlobalCmd.live_run.value + [
        VerbArgs.format_json.value,
        IoVerbs.dump_config,
    ]
    file_status_lines = GlobalCmd.live_run.value + [
        IoVerbs.status,
        VerbArgs.path_style_absolute.value,
        VerbArgs.include_files.value,
    ]
    git_log = (
        GlobalCmd.live_run.value + [ReadVerbs.git] + VerbArgs.git_log.value
    )
    ignored = GlobalCmd.live_run.value + [ReadVerbs.ignored]
    managed_dirs = GlobalCmd.live_run.value + [
        IoVerbs.managed,
        VerbArgs.path_style_absolute.value,
        VerbArgs.include_dirs.value,
    ]
    managed_files = GlobalCmd.live_run.value + [
        IoVerbs.managed,
        VerbArgs.path_style_absolute.value,
        VerbArgs.include_files.value,
    ]
    source_path = GlobalCmd.live_run.value + [ReadVerbs.source_path]


@dataclass
class InitConfig:
    changes_enabled: bool = os.environ.get("MOUSSE_ENABLE_CHANGES") == "1"
    chezmoi_cmd = CHEZMOI_CMD
    chezmoi_found: bool = which(CHEZMOI_CMD) is not None
    config_dump: ParsedJson | None = None
    destDir: Path = Path.home()
    dev_mode: bool = os.environ.get("CHEZMOI_MOUSSE_DEV") == "1"
    git_autoadd: bool = False
    git_autocommit: bool = False
    git_autopush: bool = False
    sourceDir: Path = Path(tempfile.gettempdir())

    def __post_init__(self):
        if os.environ.get("PRETEND_CHEZMOI_NOT_FOUND") == "1":
            self.chezmoi_found = False
        if self.chezmoi_found:
            result: CompletedProcess[str] = run(
                ReadCmd.dump_config.value,
                capture_output=True,
                shell=False,
                text=True,  # returns stdout as str instead of bytes
            )
            self.config_dump = json.loads(result.stdout)
            if self.config_dump is not None:
                self.destDir = Path(self.config_dump["destDir"])
                self.sourceDir = Path(self.config_dump["sourceDir"])
                self.git_autoadd = self.config_dump["git"]["autoadd"]
                self.git_autocommit = self.config_dump["git"]["autocommit"]
                self.git_autopush = self.config_dump["git"]["autopush"]


INIT_CFG = InitConfig()


class IoCmd(Enum):
    """For backwards compatibility, will be removed in future."""

    doctor = ReadCmd.doctor.value
    dir_status_lines = ReadCmd.dir_status_lines.value
    file_status_lines = ReadCmd.file_status_lines.value
    managed_dirs = ReadCmd.managed_dirs.value
    managed_files = ReadCmd.managed_files.value


@dataclass
class ReadCmdCache:
    dir_status_lines: CompletedProcess[str] | None = None
    doctor: CompletedProcess[str] | None = None
    file_status_lines: CompletedProcess[str] | None = None
    managed_dirs: CompletedProcess[str] | None = None
    managed_files: CompletedProcess[str] | None = None


def _run_cmd(long_command: list[str]) -> CompletedProcess[str] | None:
    if not INIT_CFG.chezmoi_found:
        return None
    # if a command contains failed, earlier on another command failed
    elif "failed" in long_command:
        return None

    # TODO: implement spinner for commands taking a bit longer like operations
    # TODO: set different timeout values depending on nature of command
    # TODO: implement 'chezmoi verify', if exit 0, display message in Tree
    # widgets inform the user why the Tree widget is empty

    return run(
        long_command,
        capture_output=True,
        shell=False,
        text=True,  # returns stdout as str instead of bytes
        timeout=5,
    )


class ChangeCommand:
    """Used for backwards compatibility, will be removed in future."""

    def __init__(self) -> None:
        self.base_cmd: list[str] = GlobalCmd.live_run.value
        if not INIT_CFG.changes_enabled:
            self.base_cmd = GlobalCmd.dry_run.value

    def add(self, path: Path) -> None:
        _run_cmd(self.base_cmd + [OperateVerbs.add, str(path)])

    def add_encrypted(self, path: Path) -> None:
        _run_cmd(self.base_cmd + [OperateVerbs.add, "--encrypt", str(path)])

    def re_add(self, path: Path) -> None:
        _run_cmd(self.base_cmd + [OperateVerbs.re_add, str(path)])

    def apply(self, path: Path) -> None:
        _run_cmd(self.base_cmd + [OperateVerbs.apply, str(path)])

    def destroy(self, path: Path) -> None:
        _run_cmd(self.base_cmd + [OperateVerbs.destroy, str(path)])

    def forget(self, path: Path) -> None:
        _run_cmd(self.base_cmd + [OperateVerbs.forget, str(path)])

    def init_clone_repo(self, repo_url: str) -> None:
        _run_cmd(self.base_cmd + [OperateVerbs.init, repo_url])

    def init_new_repo(self) -> None:
        _run_cmd(self.base_cmd + [OperateVerbs.init])

    def purge(self) -> None:
        _run_cmd(self.base_cmd + [OperateVerbs.purge])


@dataclass
class ChangeCmd:

    base_cmd: list[str] = field(default_factory=list[str])

    def add(self) -> list[str]:
        return self.base_cmd + [OperateVerbs.add]

    def add_encrypted(self) -> list[str]:
        return self.base_cmd + [OperateVerbs.add, VerbArgs.encrypt.value]

    def re_add(self) -> list[str]:
        return self.base_cmd + [OperateVerbs.re_add]

    def apply(self) -> list[str]:
        return self.base_cmd + [OperateVerbs.apply]

    def destroy(self) -> list[str]:
        return self.base_cmd + [OperateVerbs.destroy]

    def forget(self) -> list[str]:
        return self.base_cmd + [OperateVerbs.forget]

    def init_clone_repo(self) -> list[str]:
        return self.base_cmd + [OperateVerbs.init]

    def init_new_repo(self) -> list[str]:
        return self.base_cmd + [OperateVerbs.init]

    def purge(self) -> list[str]:
        return self.base_cmd + [OperateVerbs.purge]

    def __post_init__(self, dry_run: bool = False) -> None:
        self.base_cmd: list[str] = GlobalCmd.dry_run.value
        if not INIT_CFG.changes_enabled:
            self.base_cmd = GlobalCmd.dry_run.value


class ReadCommand:
    """Used for backwards compatibility, will be removed in future."""

    def __init__(self, *, dest_dir: Path, source_dir: Path):
        self.dest_dir = dest_dir
        self.source_dir = source_dir

    def cat(self, file_path: Path) -> list[str]:
        result: CompletedProcess[str] | None = _run_cmd(
            GlobalCmd.live_run.value + [ReadVerbs.cat] + [str(file_path)]
        )
        if result is None:
            return []
        return result.stdout.lstrip("\n").rstrip().splitlines()

    def cat_config(self) -> list[str]:
        result: CompletedProcess[str] | None = _run_cmd(
            GlobalCmd.live_run.value + [ReadVerbs.cat_config]
        )
        if result is None:
            return []
        return [
            line
            for line in result.stdout.lstrip("\n").rstrip().splitlines()
            if line.strip()  # Filter out empty lines from config output
        ]

    def diff(self, file_path: Path) -> list[str]:
        result: CompletedProcess[str] | None = _run_cmd(
            GlobalCmd.live_run.value + [ReadVerbs.diff] + [str(file_path)]
        )
        if result is None:
            return []
        return result.stdout.lstrip("\n").rstrip().splitlines()

    def diff_reversed(self, file_path: Path) -> list[str]:
        result: CompletedProcess[str] | None = _run_cmd(
            GlobalCmd.live_run.value
            + [ReadVerbs.diff]
            + [VerbArgs.reverse.value, str(file_path)]
        )
        if result is None:
            return []
        return result.stdout.lstrip("\n").rstrip().splitlines()

    def git_log(self, path: Path) -> list[str]:
        source_path = self.source_path(path)
        command = (
            GlobalCmd.live_run.value
            + [ReadVerbs.git]
            + VerbArgs.git_log.value
            + [str(source_path)]
        )
        result: CompletedProcess[str] | None = _run_cmd(command)
        if result is None:
            return []
        return result.stdout.lstrip("\n").rstrip().splitlines()

    def ignored(self) -> list[str]:
        result: CompletedProcess[str] | None = _run_cmd(
            GlobalCmd.live_run.value + [ReadVerbs.ignored]
        )
        if result is None:
            return []
        return result.stdout.lstrip("\n").rstrip().splitlines()

    def source_path(self, path: Path) -> Path:
        if path == self.dest_dir:
            return self.source_dir
        result: CompletedProcess[str] | None = _run_cmd(
            GlobalCmd.live_run.value + [ReadVerbs.source_path] + [str(path)]
        )
        if result is None:
            return Path()
        return Path(result.stdout.strip())

    def template_data(self) -> list[str]:
        result: CompletedProcess[str] | None = _run_cmd(
            GlobalCmd.live_run.value + [ReadVerbs.data]
        )
        if result is None:
            return []
        return result.stdout.lstrip("\n").rstrip().splitlines()


@dataclass
class InputOutput:

    long_command: list[str]
    arg_id: str
    std_out: str = ""

    @property
    def list_out(self):
        return self.std_out.splitlines()

    def update(self) -> None:
        result: CompletedProcess[str] | None = _run_cmd(self.long_command)
        if result is None:
            self.std_out = ""
        else:
            self.std_out = result.stdout


class Chezmoi:

    dir_status_lines: InputOutput  # for backwards compatibility
    doctor: InputOutput  # for backwards compatibility
    file_status_lines: InputOutput  # for backwards compatibility
    managed_dirs: InputOutput  # for backwards compatibility
    managed_files: InputOutput  # for backwards compatibility
    perform = ChangeCommand()  # for backwards compatibility

    def __init__(self) -> None:
        self.run = ReadCommand(
            dest_dir=INIT_CFG.destDir, source_dir=INIT_CFG.sourceDir
        )
        self.change_cmd = ChangeCmd()
        if INIT_CFG.config_dump is None:
            self.config_dump = {}
        else:
            self.config_dump = INIT_CFG.config_dump

        self.io_commands: dict[str, list[str]] = {}
        io_cmds: list[IoCmd] = [
            IoCmd.dir_status_lines,
            IoCmd.doctor,
            IoCmd.file_status_lines,
            IoCmd.managed_dirs,
            IoCmd.managed_files,
        ]
        for long_cmd in io_cmds:
            self.io_commands[long_cmd.name] = long_cmd.value
            setattr(
                self,
                long_cmd.name,
                InputOutput(long_cmd.value, arg_id=long_cmd.name),
            )

    @property
    def dir_paths(self) -> list[Path]:
        return [Path(p) for p in self.managed_dirs.list_out]

    @property
    def file_paths(self) -> list[Path]:
        return [Path(p) for p in self.managed_files.list_out]

    @property
    def apply_dirs(self) -> PathDict:
        return self._create_status_dict(TabName.apply_tab, "dirs")

    @property
    def apply_files(self) -> PathDict:
        return self._create_status_dict(TabName.apply_tab, "files")

    @property
    def read_cmd(self) -> type[ReadCmd]:
        return ReadCmd

    @property
    def re_add_dirs(self) -> PathDict:
        return self._create_status_dict(TabName.re_add_tab, "dirs")

    @property
    def re_add_files(self) -> PathDict:
        return self._create_status_dict(TabName.re_add_tab, "files")

    def read(self, read_cmd: ReadCmd, path: Path | None = None) -> str:
        cmd = read_cmd.value
        if path is not None:
            cmd = cmd + [str(path)]
        # CompletedProcess type arg is str as we use text=True
        result: CompletedProcess[str] = run(
            cmd, capture_output=True, shell=False, text=True, timeout=5
        )
        if result.returncode != 0:
            # TODO callback to log stderr
            return ""
        if result.stdout == "":
            # TODO callback to log stderr
            return ""
        # remove trailing and leading new lines but NOT leading whitespace
        stdout = result.stdout.lstrip("\n").rstrip()
        # remove intermediate empty lines
        return "\n".join(
            # TODO callback to log stderr
            [line for line in stdout.splitlines() if line.strip()]
        )

    def files_with_status_in(
        self, tab_name: TabName, dir_path: Path
    ) -> list[Path]:
        files_dict: PathDict = {}
        if tab_name == TabName.apply_tab:
            files_dict = self.apply_files
        elif tab_name == TabName.re_add_tab:
            files_dict = self.re_add_files
        return [
            p
            for p, status in files_dict.items()
            if status != "X" and p.parent == dir_path
        ]

    def files_without_status_in(
        self, tab_name: TabName, dir_path: Path
    ) -> list[Path]:
        files_dict: PathDict = {}
        if tab_name == TabName.apply_tab:
            files_dict = self.apply_files
        elif tab_name == TabName.re_add_tab:
            files_dict = self.re_add_files
        return [
            p
            for p, status in files_dict.items()
            if status == "X" and p.parent == dir_path
        ]

    def managed_dirs_in(self, dir_path: Path) -> list[Path]:
        # checks only direct children
        return [p for p in self.dir_paths if p.parent == dir_path]

    def update_managed_status_data(self) -> None:
        # Update data that the managed_status property depends on
        # TODO: do not run when operation is cancelled and properly update
        # Tree widgets after a relevant operation
        # DirectoryTree refreshes correctly
        self.managed_dirs.update()
        self.managed_files.update()
        self.dir_status_lines.update()
        self.file_status_lines.update()

    def _create_status_dict(
        self, tab_name: TabName, kind: Literal["dirs", "files"]
    ) -> PathDict:
        path_dict: PathDict = {}
        status_idx: int = 0
        status_codes: str = ""
        if kind == "dirs":
            managed_paths = self.dir_paths
            status_lines = self.dir_status_lines.list_out
        elif kind == "files":
            managed_paths = self.file_paths
            status_lines = self.file_status_lines.list_out

        if tab_name == TabName.apply_tab:
            status_codes = "ADM"
            status_idx = 1
        elif tab_name == TabName.re_add_tab:
            status_codes = "M"
            status_idx = 0

        paths_with_status_dict = {}
        if tab_name == TabName.re_add_tab:
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

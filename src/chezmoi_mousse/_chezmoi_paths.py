from dataclasses import dataclass, field
from pathlib import Path

from rich.text import Text
from textual.widgets import DataTable, Label, RichLog, Static

from ._chezmoi_command import ChezmoiCommand, CommandResult
from ._str_enums import StatusCode

type StatusPath = dict[Path, StatusCode]

__all__ = ["ChezmoiPaths"]


@dataclass(slots=True)
class PathWidgets:
    # widgets for a managed file or dir path and the root dir
    content: list[Label | Static]
    diff: list[Label | Static]
    git_log: DataTable[Text]


@dataclass(slots=True)
class FileWidgets(PathWidgets):
    # file widgets only, used when they don't exist on disk in the Contents tab
    cat: RichLog


@dataclass(slots=True)
class DirNode:
    dir_widgets: PathWidgets
    status_files: dict[Path, FileWidgets]
    no_status_files: dict[Path, FileWidgets]


@dataclass
class PathsCache:
    managed_dirs: list[Path] = field(default_factory=list[Path])  # used in the Add tab
    managed_files: list[Path] = field(default_factory=list[Path])  # used in the Add tab
    apply_dirs: list[StatusPath] = field(default_factory=list[dict[Path, StatusCode]])
    apply_files: list[StatusPath] = field(default_factory=list[dict[Path, StatusCode]])
    re_add_dirs: list[StatusPath] = field(default_factory=list[dict[Path, StatusCode]])
    re_add_files: list[StatusPath] = field(default_factory=list[dict[Path, StatusCode]])
    apply_dir_nodes: dict[Path, DirNode] = field(default_factory=dict[Path, DirNode])
    re_add_dir_nodes: dict[Path, DirNode] = field(default_factory=dict[Path, DirNode])


class ChezmoiPaths:
    def __init__(
        self,
        managed_dirs_cmd_result: CommandResult,
        managed_files_cmd_result: CommandResult,
        status_dirs_cmd_result: CommandResult,
        status_files_cmd_result: CommandResult,
    ) -> None:
        self.cmd = ChezmoiCommand()
        self.managed_dirs_result = managed_dirs_cmd_result
        self.managed_files_result = managed_files_cmd_result
        self.status_dirs_result = status_dirs_cmd_result
        self.status_files_result = status_files_cmd_result
        self.cache: PathsCache = PathsCache()
        self.update_cache(
            self.managed_dirs_result,
            self.managed_files_result,
            self.status_dirs_result,
            self.status_files_result,
        )

    def _create_status_dicts(
        self, managed_paths: list[Path], status_lines: list[str], index: int
    ) -> list[StatusPath]:
        status_paths: list[StatusPath] = []
        for line in status_lines:
            path = Path(line[3:])
            if path not in managed_paths:
                status_paths.append({path: StatusCode.no_status})
            else:
                status_paths.append({path: StatusCode(line[index])})
        return status_paths

    def update_cache(
        self,
        managed_dirs: CommandResult,
        managed_files: CommandResult,
        status_dirs: CommandResult,
        status_files: CommandResult,
    ):
        dir_paths = [Path(p) for p in managed_dirs.std_out.splitlines()]
        file_paths = [Path(p) for p in managed_files.std_out.splitlines()]
        self.cache = PathsCache(
            managed_dirs=dir_paths,  # used in the Add tab
            managed_files=file_paths,  # used in the Add tab
            apply_dirs=self._create_status_dicts(
                dir_paths, status_dirs.std_out.splitlines(), index=0
            ),
            apply_files=self._create_status_dicts(
                file_paths, status_files.std_out.splitlines(), index=0
            ),
            re_add_dirs=self._create_status_dicts(
                dir_paths, status_dirs.std_out.splitlines(), index=1
            ),
            re_add_files=self._create_status_dicts(
                file_paths, status_files.std_out.splitlines(), index=1
            ),
        )

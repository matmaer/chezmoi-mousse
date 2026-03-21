from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

from textual.widgets import Label, Static

from ._run_cmd import ChezmoiCommand
from ._str_enum_names import Tcss
from ._str_enums import StatusCode, TabLabel

if TYPE_CHECKING:
    from typing import Any

    from ._run_cmd import CommandResult

__all__ = ["CMD", "CachedData", "ParsedJson"]


type ParsedJson = dict[str, Any]


@dataclass(slots=True)
class PathSets:
    managed_paths: set[Path] = field(default_factory=lambda: set())
    status_paths: set[Path] = field(default_factory=lambda: set())
    managed_dirs: set[Path] = field(default_factory=lambda: set())
    managed_dirs_plus_dest_dir: set[Path] = field(default_factory=lambda: set())
    managed_files: set[Path] = field(default_factory=lambda: set())
    status_dirs: set[Path] = field(default_factory=lambda: set())
    status_files: set[Path] = field(default_factory=lambda: set())
    x_files: set[Path] = field(default_factory=lambda: set())
    x_dirs: set[Path] = field(default_factory=lambda: set())
    n_dirs: set[Path] = field(default_factory=lambda: set())

    def get_sub_dirs_in(self, dir_path: Path) -> set[Path]:
        return {p for p in self.managed_dirs if p.parent == dir_path}

    def has_status_paths(self, dir_path: Path) -> bool:
        return any(
            p.is_relative_to(dir_path) for p in self.status_dirs | self.status_files
        )


class CachedData:
    def __init__(self) -> None:
        # command result caches (instance attributes so deepcopy snapshots work)
        self.cat_config: CommandResult | None = None
        self.doctor: CommandResult | None = None
        self.dump_config: CommandResult | None = None
        self.git_log: CommandResult | None = None
        self.ignored: CommandResult | None = None
        self.managed_dirs: CommandResult | None = None
        self.managed_files: CommandResult | None = None
        self.status_dirs: CommandResult | None = None
        self.status_files: CommandResult | None = None
        self.template_data: CommandResult | None = None
        self.verify: CommandResult | None = None

        # parsed config cache
        self.dest_dir: Path = Path().home()
        self.git_auto_commit: bool = False
        self.git_auto_push: bool = False

        # cached for frequent lookups
        self.sets: PathSets = PathSets()

    @property
    def no_status_paths(self) -> bool:
        return self.verify is not None and self.verify.exit_code == 0

    @property
    def _dir_status_pairs(self) -> dict[Path, str]:
        if self.status_dirs is None:
            return {}
        return {
            Path(line[3:]): line[:2] for line in self.status_dirs.std_out.splitlines()
        }

    @property
    def _file_status_pairs(self) -> dict[Path, str]:
        if self.status_files is None:
            return {}
        return {
            Path(line[3:]): line[:2] for line in self.status_files.std_out.splitlines()
        }

    @property
    def status_pairs(self) -> dict[Path, str]:
        return self._dir_status_pairs | self._file_status_pairs

    def _get_status_dirs(self, canvas_name: str) -> dict[Path, StatusCode]:
        if self.status_dirs is None:
            return {}
        index = 0 if canvas_name == TabLabel.apply else 1
        return {k: StatusCode(v[index]) for k, v in self._dir_status_pairs.items()}

    def _get_status_files(self, canvas_name: str) -> dict[Path, StatusCode]:
        if self.status_files is None:
            return {}
        index = 0 if canvas_name == TabLabel.apply else 1
        return {k: StatusCode(v[index]) for k, v in self._file_status_pairs.items()}

    def get_x_files_in(self, dir_path: Path) -> dict[Path, StatusCode]:
        return {
            path: StatusCode.Space
            for path in self.sets.managed_files
            if path.parent == dir_path and path not in self.sets.status_files
        }

    def get_x_dirs_in(self, dir_path: Path) -> dict[Path, StatusCode]:
        return {
            path: StatusCode.Space
            for path in self.sets.managed_dirs
            if path.parent == dir_path and path not in self.sets.status_files
        }

    def get_path_status(self, path: Path, canvas_name: str) -> StatusCode:
        paths_dict = self._get_status_dirs(canvas_name) | self._get_status_files(
            canvas_name
        )
        status = paths_dict.get(path, StatusCode.Space)
        if (
            path in self.sets.n_dirs
            and status == StatusCode.Space
            or path == self.dest_dir
        ):
            return StatusCode.Nested
        return status

    def get_status_files_in(
        self, dir_path: Path, canvas_name: str, recursive: bool
    ) -> dict[Path, StatusCode]:
        status_files = self._get_status_files(canvas_name)
        if recursive:
            return {p: s for p, s in status_files.items() if p.is_relative_to(dir_path)}
        return {p: s for p, s in status_files.items() if p.parent == dir_path}

    def get_status_dirs_in(
        self, dir_path: Path, canvas_name: str, recursive: bool
    ) -> dict[Path, StatusCode]:
        status_dirs = self._get_status_dirs(canvas_name)
        if recursive:
            return {p: s for p, s in status_dirs.items() if p.is_relative_to(dir_path)}
        return {p: s for p, s in status_dirs.items() if p.parent == dir_path}

    # get_n_dirs is only used to build the ManagedTree, it never needs to be recursive
    def get_n_dirs_in(self, dir_path: Path, canvas_name: str) -> dict[Path, StatusCode]:
        status_dirs = self._get_status_dirs(canvas_name)
        return {
            p: s
            for p, s in status_dirs.items()
            if p.parent == dir_path and p in self.sets.n_dirs
        }

    def get_dir_widgets(self, dir_path: Path, canvas_name: str) -> list[Static | Label]:
        has_status_paths = self.sets.has_status_paths(dir_path)
        all_status_files_in = self.get_status_files_in(
            dir_path, canvas_name, recursive=True
        )
        all_status_dirs_in = self.get_status_dirs_in(
            dir_path, canvas_name, recursive=True
        )
        widgets: list[Static | Label] = []
        if dir_path == CMD.cache.dest_dir:
            widgets.append(
                Label("Destination directory", classes=Tcss.main_section_label)
            )
            if CMD.cache.no_status_paths is True:
                widgets.append(
                    Static(
                        "No managed paths or paths with a status are in the chezmoi "
                        "repository. Switch to the Add tab to add paths.",
                        classes=Tcss.added,
                    )
                )
            elif has_status_paths is True:
                text = "No diffs are available because no paths have a status."
                widgets.append(Static(text, classes=Tcss.info))
                text = "<- Select an unchanged path."
                widgets.append(Static(text, classes=Tcss.added))
                text = (
                    "Switch to the Contents tab to view the contents of the selected "
                    "path.\n"
                    "Switch to the Git-Log tab to view the git log output for the "
                    "selected path."
                )
                widgets.append(Static(text, classes=Tcss.info))
            else:
                text = "<- Select a file or directory in the tree to view its diff."
                widgets.append(Static(text, classes=Tcss.added))
                text = "This is the destination directory, it has no diff output."
                widgets.append(Static(text, classes=Tcss.info))
        if all_status_dirs_in:
            widgets.append(
                Label(
                    "Contains directories with a status", classes=Tcss.sub_section_label
                )
            )
            for path, status in all_status_dirs_in.items():
                widgets.append(Static(f"{status.color_tag}{path}[/]"))
        if all_status_files_in:
            widgets.append(
                Label("Contains files with a status", classes=Tcss.sub_section_label)
            )
            for path, status in all_status_files_in.items():
                widgets.append(Static(f"{status.color_tag}{path}[/]"))
        return widgets

    def update_path_sets(self) -> None:
        def parse_paths_from_result(result: CommandResult | None) -> set[Path]:
            if result is None:
                return set()
            return {Path(line) for line in result.std_out.splitlines()}

        self.sets.managed_dirs = parse_paths_from_result(self.managed_dirs)
        self.sets.managed_files = parse_paths_from_result(self.managed_files)
        self.sets.managed_dirs_plus_dest_dir = {self.dest_dir} | self.sets.managed_dirs
        self.sets.status_dirs = set(self._dir_status_pairs.keys())
        self.sets.status_files = set(self._file_status_pairs.keys())
        # derived assignments
        self.sets.managed_paths = self.sets.managed_dirs | self.sets.managed_files
        self.sets.status_paths = self.sets.status_dirs | self.sets.status_files
        self.sets.x_dirs = {
            d for d in self.sets.managed_dirs if d not in self.sets.status_dirs
        }
        self.sets.x_files = {
            f for f in self.sets.managed_files if f not in self.sets.status_files
        }
        self.sets.n_dirs = {
            dir_path
            for dir_path in self.sets.x_dirs
            if any(
                status_path.is_relative_to(dir_path)
                for status_path in self.sets.status_paths
                if dir_path not in self.sets.status_dirs
            )
        }


@dataclass(slots=True)
class Commands:
    run_cmd: ChezmoiCommand = field(default_factory=ChezmoiCommand)
    cache: CachedData = CachedData()
    loading_modal_results: list[CommandResult] = field(default_factory=lambda: [])
    changed_paths: list[Path] = field(default_factory=lambda: [])


CMD = Commands()

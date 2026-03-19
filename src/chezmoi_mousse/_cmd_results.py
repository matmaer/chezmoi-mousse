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

__all__ = ["CMD", "CachedData", "DirNode", "ParsedJson"]


type ParsedJson = dict[str, Any]


@dataclass(slots=True)
class DirNode:
    dir_path: Path
    status_files_in: dict[Path, StatusCode]
    real_status_dirs_in: dict[Path, StatusCode]
    tree_status_dirs_in: dict[Path, StatusCode]
    nested_status_dirs: dict[Path, StatusCode]
    nested_status_files: dict[Path, StatusCode]
    tree_x_dirs_in: dict[Path, StatusCode]

    # property to return if the dir has any nested paths with a status
    @property
    def _has_status_paths(self) -> bool:
        return bool(
            self.status_files_in
            or self.real_status_dirs_in
            or self.nested_status_dirs
            or self.nested_status_files
        )

    @property
    def dir_widgets(self) -> list[Static | Label]:
        # Populate dir_widgets for the destDir
        widgets: list[Static | Label] = []
        if self.dir_path == CMD.cache.dest_dir:
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
            elif self._has_status_paths is True:
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
        if self.real_status_dirs_in:
            widgets.append(
                Label(
                    "Contains directories with a status", classes=Tcss.sub_section_label
                )
            )
            for path, status in self.real_status_dirs_in.items():
                widgets.append(Static(f"{status.color_tag}{path}[/]"))
        if self.status_files_in:
            widgets.append(
                Label("Contains files with a status", classes=Tcss.sub_section_label)
            )
            for path, status in self.status_files_in.items():
                widgets.append(Static(f"{status.color_tag}{path}[/]"))
        if self.nested_status_files:
            widgets.append(
                Label(
                    "Contains nested files with a status",
                    classes=Tcss.sub_section_label,
                )
            )
            for path, status in sorted(self.nested_status_files.items()):
                widgets.append(Static(f"{status.color_tag}{path}[/]"))
        return widgets


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
    x_dirs_with_status_children: set[Path] = field(default_factory=lambda: set())


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

        # dir node caches
        self.re_add_dir_nodes: dict[Path, DirNode] = {}
        self.apply_dir_nodes: dict[Path, DirNode] = {}

        self.dest_dir: Path = Path().home()
        self.git_auto_commit: bool = False
        self.git_auto_push: bool = False

        # cached for frequent lookups
        self.sets: PathSets = PathSets()

    @property
    def _apply_status_dirs(self) -> dict[Path, StatusCode]:
        if self.status_dirs is None:
            return {}
        return {
            Path(line[3:]): StatusCode(line[0])
            for line in self.status_dirs.std_out.splitlines()
        }

    @property
    def _apply_status_files(self) -> dict[Path, StatusCode]:
        if self.status_files is None:
            return {}
        return {
            Path(line[3:]): StatusCode(line[0])
            for line in self.status_files.std_out.splitlines()
        }

    @property
    def _re_add_status_dirs(self) -> dict[Path, StatusCode]:
        if self.status_dirs is None:
            return {}
        return {
            Path(line[3:]): StatusCode(line[1])
            for line in self.status_dirs.std_out.splitlines()
        }

    @property
    def _re_add_status_files(self) -> dict[Path, StatusCode]:
        if self.status_files is None:
            return {}
        return {
            Path(line[3:]): StatusCode(line[1])
            for line in self.status_files.std_out.splitlines()
        }

    @property
    def _dir_status_pairs(self) -> dict[Path, str]:
        if self.status_dirs is None:
            return {}
        return {
            Path(line[3:]): line[:2]
            for line in list(self.status_dirs.std_out.splitlines())
        }

    @property
    def _file_status_pairs(self) -> dict[Path, str]:
        if self.status_files is None:
            return {}
        return {
            Path(line[3:]): line[:2]
            for line in list(self.status_files.std_out.splitlines())
        }

    @property
    def status_pairs(self) -> dict[Path, str]:
        return self._dir_status_pairs | self._file_status_pairs

    @property
    def tree_x_dirs(self) -> list[Path]:
        return [
            d
            for d in self.sets.managed_dirs
            if d not in self.sets.x_dirs_with_status_children
        ]

    @property
    def no_status_paths(self) -> bool:
        return self.verify is not None and self.verify.exit_code == 0

    def get_x_files_in(self, dir_path: Path) -> dict[Path, StatusCode]:
        return {
            path: StatusCode.Space
            for path in self.sets.managed_files
            if path.parent == dir_path and path not in self.sets.status_files
        }

    def get_path_status(self, path: Path, canvas_name: str) -> StatusCode:
        if canvas_name == TabLabel.apply:
            paths_dict = self._apply_status_dirs | self._apply_status_files
        else:
            paths_dict = self._re_add_status_dirs | self._re_add_status_files
        status = paths_dict.get(path, StatusCode.Space)
        if (
            path in self.sets.x_dirs_with_status_children
            and status == StatusCode.Space
            or path == self.dest_dir
        ):
            return StatusCode.Nested
        return status

    def get_dir_node(self, dir_path: Path, canvas_name: str) -> DirNode:
        if canvas_name == TabLabel.apply:
            status_files = self._apply_status_files
            status_dirs = self._apply_status_dirs
        else:
            status_files = self._re_add_status_files
            status_dirs = self._re_add_status_dirs
        # sub dir paths are the same for apply and re_add contexts
        sub_dir_paths = [
            p for p in self.sets.managed_dirs_plus_dest_dir if p.parent == dir_path
        ]
        tree_status_dirs_in: dict[Path, StatusCode] = {}
        tree_x_dirs_in: dict[Path, StatusCode] = {}
        for sub_dir in sub_dir_paths:
            if (
                sub_dir in status_dirs
                or sub_dir in self.sets.x_dirs_with_status_children
            ):
                tree_status_dirs_in[sub_dir] = status_dirs.get(
                    sub_dir, StatusCode.Space
                )
            else:
                tree_x_dirs_in[sub_dir] = StatusCode.Space

        return DirNode(
            dir_path=dir_path,
            status_files_in={
                p: s for p, s in status_files.items() if p.parent == dir_path
            },
            real_status_dirs_in={
                p: s for p, s in status_dirs.items() if p.parent == dir_path
            },
            tree_status_dirs_in=dict(sorted(tree_status_dirs_in.items())),
            tree_x_dirs_in=dict(sorted(tree_x_dirs_in.items())),
            nested_status_dirs={
                p: s
                for p, s in status_dirs.items()
                if p.is_relative_to(dir_path) and len(p.relative_to(dir_path).parts) > 1
            },
            nested_status_files={
                p: s
                for p, s in status_files.items()
                if p.is_relative_to(dir_path) and len(p.relative_to(dir_path).parts) > 1
            },
        )

    def update_path_sets(self) -> None:

        def managed_dir_paths() -> set[Path]:
            if self.managed_dirs is None:
                return set()
            return {Path(line) for line in self.managed_dirs.std_out.splitlines()}

        def managed_file_paths() -> set[Path]:
            if self.managed_files is None:
                return set()
            return {Path(line) for line in self.managed_files.std_out.splitlines()}

        self.sets.managed_dirs = managed_dir_paths()

        self.sets.managed_files = set(managed_file_paths())
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
        self.sets.x_dirs_with_status_children = {
            dir_path
            for dir_path in self.sets.x_dirs
            if any(
                status_path.is_relative_to(dir_path)
                for status_path in self.sets.status_paths
            )
        }


@dataclass(slots=True)
class Commands:
    run_cmd: ChezmoiCommand = field(default_factory=ChezmoiCommand)
    cache: CachedData = CachedData()
    loading_modal_results: list[CommandResult] = field(default_factory=lambda: [])
    changed_paths: list[Path] = field(default_factory=lambda: [])


CMD = Commands()

from __future__ import annotations

from dataclasses import dataclass, field
from functools import cached_property
from pathlib import Path
from types import MappingProxyType
from typing import TYPE_CHECKING

from chezmoi_mousse.app_ids import AppIds
from chezmoi_mousse.cm_command import ReadCmd
from chezmoi_mousse.named_tuples import CommandResult, ManagedTreePaths, ReadCmdGroups
from chezmoi_mousse.str_enums import PathKind, StatusCode, TabLabel

if TYPE_CHECKING:
    from chezmoi_mousse.cm_types import ParsedJson, PathKindMap, StatusMap
    from chezmoi_mousse.named_tuples import ManagedResults


__all__ = ["CmAttributes", "ManagedPaths", "ResultCollector"]


@dataclass(slots=True)
class ResultCollector:

    dest_dir: Path = field(init=False)
    cat_config: CommandResult = field(init=False)
    doctor: CommandResult = field(init=False)
    dump_config: CommandResult = field(init=False)
    git_log: CommandResult = field(init=False)
    git_remote: CommandResult = field(init=False)
    ignored: CommandResult = field(init=False)
    managed_dirs: CommandResult = field(init=False)
    managed_files: CommandResult = field(init=False)
    parsed_dump_config: ParsedJson = field(init=False)
    parsed_template_data: ParsedJson = field(init=False)
    status_dirs: CommandResult = field(init=False)
    status_files: CommandResult = field(init=False)
    template_data: CommandResult = field(init=False)
    managed_paths_instance: ManagedPaths = field(init=False)

    # Used for logging after the splash screen is disimissed and we push the MainScreen
    @property
    def splash_results_list(self) -> list[CommandResult]:
        return [
            self.doctor,
            self.git_log,
            self.dump_config,
            self.cat_config,
            self.template_data,
            self.ignored,
            self.git_remote,
            self.managed_dirs,
            self.managed_files,
            self.status_dirs,
            self.status_files,
        ]


@dataclass(frozen=True, slots=True, kw_only=True)
class ChangedPaths:
    added_paths: list[Path] = field(default_factory=lambda: [])
    changed_status_paths: list[Path] = field(default_factory=lambda: [])
    removed_paths: list[Path] = field(default_factory=lambda: [])

    @property
    def no_changes(self) -> bool:
        return (
            not self.added_paths
            and not self.changed_status_paths
            and not self.removed_paths
        )

    @classmethod
    def clear_changes(cls) -> None:
        cls.added_paths: list[Path] = []
        cls.changed_status_paths: list[Path] = []
        cls.removed_paths: list[Path] = []


@dataclass(frozen=True, kw_only=True)
class ManagedPaths:
    """Contains only immutable fields and attribute outputs to avoid asyncio related
    issues."""

    results: ManagedResults

    def __post_init__(self) -> None:

        # warm all public cached_property attributes
        # self.__dict__.items() to maintain the order
        for attr, value in self.__dict__.items():
            if not attr.startswith("_") and isinstance(value, cached_property):
                getattr(self, attr)

    @cached_property
    def managed_dirs(self) -> frozenset[Path]:
        return frozenset(Path(line) for line in self.results.managed_dirs.out_lines)

    @cached_property
    def managed_files(self) -> frozenset[Path]:
        return frozenset(Path(line) for line in self.results.managed_files.out_lines)

    @cached_property
    def unchanged_dirs(self) -> frozenset[Path]:
        status_dirs = frozenset(
            Path(line[3:]) for line in self.results.status_dirs.out_lines
        )
        return self.managed_dirs - status_dirs

    @cached_property
    def unchanged_files(self) -> frozenset[Path]:
        status_files = frozenset(
            Path(line[3:]) for line in self.results.status_files.out_lines
        )
        return self.managed_files - status_files

    # not cached, fast boolean logic

    @property
    def no_managed_paths(self) -> bool:
        return not self.managed_dirs and not self.managed_files

    def _get_status_map(self, lines: list[str], status_col: int) -> StatusMap:
        temp_dict: dict[Path, StatusCode] = {}

        for line in lines:
            if line[status_col] != StatusCode.Space:
                temp_dict[Path(line[3:])] = StatusCode(line[status_col])

        return MappingProxyType(temp_dict)

    def _get_path_kind_map(self, paths: frozenset[Path]) -> PathKindMap:
        temp_dict: dict[Path, PathKind] = {}

        for path in paths:
            if path.is_symlink():
                temp_dict[path] = PathKind.SYMLINK
            elif path.exists():
                temp_dict[path] = PathKind.EXISTS_TRUE
            elif not path.exists():
                temp_dict[path] = PathKind.EXISTS_FALSE
            else:
                temp_dict[path] = PathKind.UNHANDLED

        return MappingProxyType(temp_dict)

    def _compute_managed_tree_paths(self, status_col: int) -> ManagedTreePaths:
        """Results accessed by the ManagedTree classes for Apply and ReAdd tab.

        Includes all paths, also destDir, managed_dirs etc which are the same for both
        contexts. This povides convenient access and we convert them there to sorted
        lists before we refresh the trees.
        """
        dest_dir = self.results.dest_dir

        managed_dirs_map: PathKindMap = self._get_path_kind_map(self.managed_dirs)
        managed_files_map: PathKindMap = self._get_path_kind_map(self.managed_files)

        status_dirs_map: StatusMap = self._get_status_map(
            lines=self.results.status_dirs.out_lines, status_col=status_col
        )
        status_files_map: StatusMap = self._get_status_map(
            lines=self.results.status_files.out_lines, status_col=status_col
        )

        n_dirs = frozenset(
            parent
            for path in (status_dirs_map.keys() | status_files_map.keys())
            for parent in path.parents
            if parent != dest_dir
            and parent not in status_dirs_map
            and parent.is_relative_to(dest_dir)
        )

        return ManagedTreePaths(
            dest_dir=dest_dir,
            managed_dirs_map=managed_dirs_map,
            managed_files_map=managed_files_map,
            status_dirs_map=status_dirs_map,
            status_files_map=status_files_map,
            n_dirs=n_dirs,
            no_managed_paths=self.no_managed_paths,
            no_status_paths=(not status_dirs_map and not status_files_map),
            tree_status_dirs=(n_dirs | status_dirs_map.keys()),
            unchanged_dirs=self.unchanged_dirs,
            unchanged_files=self.unchanged_files,
        )

    # cached properties used by the ManagedTree class

    @cached_property
    def apply_tree_paths(self) -> ManagedTreePaths:
        return self._compute_managed_tree_paths(status_col=1)

    @cached_property
    def re_add_tree_paths(self) -> ManagedTreePaths:
        return self._compute_managed_tree_paths(status_col=0)


@dataclass
class CmAttributes:

    add_id = AppIds(TabLabel.add)
    apply_id = AppIds(TabLabel.apply)
    config_id = AppIds(TabLabel.config)
    debug_id = AppIds(TabLabel.debug)
    logs_id = AppIds(TabLabel.logs)
    re_add_id = AppIds(TabLabel.re_add)

    dest_dir: Path = field(init=False)
    auto_add: bool = field(init=False)
    auto_commit: bool = field(init=False)
    auto_push: bool = field(init=False)
    cmd_results: ResultCollector = field(init=False)
    paths: ManagedPaths = field(init=False)

    read_cmd_groups: ReadCmdGroups = field(
        default=ReadCmdGroups(
            splash_only=[
                ReadCmd.doctor,
                ReadCmd.git_log,
                ReadCmd.cat_config,
                ReadCmd.ignored,
                ReadCmd.git_remote,
            ],
            json_output=[ReadCmd.dump_config, ReadCmd.template_data],
            managed=[
                ReadCmd.managed_dirs,
                ReadCmd.managed_files,
                ReadCmd.status_dirs,
                ReadCmd.status_files,
            ],
        ),
        repr=False,
    )

    dry_run: bool | None = None
    changes: ChangedPaths = ChangedPaths()

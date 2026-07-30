from __future__ import annotations

from dataclasses import dataclass, field
from functools import cached_property
from itertools import chain
from pathlib import Path

from chezmoi_mousse.app_ids import AppIds
from chezmoi_mousse.cm_command import ReadCmd
from chezmoi_mousse.cm_types import (
    ManagedResults,
    ReadCmdGroups,
    ResultCollector,
    TreePathStatus,
)
from chezmoi_mousse.str_enums import StatusCode, TabLabel

__all__ = ["CmAttributes"]


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
    results: ManagedResults

    def __post_init__(self) -> None:
        # warm the TreePathStatus NamedTuple
        _ = self._apply_tree_path_status
        _ = self._re_add_tree_path_status

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

    # method helpers for derived cached_property attributes

    def _compute_tree_path_status(self, status_col: int) -> TreePathStatus:
        dest_dir = self.results.dest_dir

        status_dirs = frozenset(
            Path(line[3:])
            for line in self.results.status_dirs.out_lines
            if line[status_col] != StatusCode.Space
        )

        status_files = frozenset(
            Path(line[3:])
            for line in self.results.status_files.out_lines
            if line[status_col] != StatusCode.Space
        )

        n_dirs = frozenset(
            parent
            for path in (status_dirs | status_files)
            for parent in path.parents
            if parent != dest_dir
            and parent not in status_dirs
            and parent.is_relative_to(dest_dir)
        )

        return TreePathStatus(status_dirs, status_files, n_dirs)

    def _has_status_paths(self, status_col: int) -> bool:
        return any(
            line[status_col] != StatusCode.Space
            for line in chain(
                self.results.status_dirs.out_lines, self.results.status_files.out_lines
            )
        )

    # derived private cached properties

    @cached_property
    def _apply_tree_path_status(self) -> TreePathStatus:
        return self._compute_tree_path_status(status_col=1)

    @cached_property
    def _re_add_tree_path_status(self) -> TreePathStatus:
        return self._compute_tree_path_status(status_col=0)

    # derived public cached properties

    @cached_property
    def no_apply_paths(self) -> bool:
        return not self._has_status_paths(status_col=1)

    @cached_property
    def no_re_add_paths(self) -> bool:
        return not self._has_status_paths(status_col=0)

    # anything derived from 'TreePathStatus' is already cached

    @property
    def apply_n_dirs(self) -> frozenset[Path]:
        return self._apply_tree_path_status.n_dirs

    @property
    def apply_tree_status_dirs(self) -> frozenset[Path]:
        return (
            self._apply_tree_path_status.status_dirs
            | self._apply_tree_path_status.n_dirs
        )

    @property
    def apply_status_files(self) -> frozenset[Path]:
        return self._apply_tree_path_status.status_files

    @property
    def re_add_n_dirs(self) -> frozenset[Path]:
        return self._re_add_tree_path_status.n_dirs

    @property
    def re_add_tree_status_dirs(self) -> frozenset[Path]:
        return (
            self._re_add_tree_path_status.status_dirs
            | self._re_add_tree_path_status.n_dirs
        )

    @property
    def re_add_status_files(self) -> frozenset[Path]:
        return self._re_add_tree_path_status.status_files

    # fast boolean logic, no need to cache

    @property
    def no_status_paths(self) -> bool:
        return self.no_apply_paths and self.no_re_add_paths

    @property
    def no_managed_paths(self) -> bool:
        return not self.managed_dirs and not self.managed_files


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

    dry_run: bool = field(default=True)
    changes: ChangedPaths = ChangedPaths()

from __future__ import annotations

from dataclasses import dataclass, field
from functools import cached_property
from pathlib import Path
from types import MappingProxyType
from typing import TYPE_CHECKING, ClassVar

from chezmoi_mousse.app_ids import AppIds
from chezmoi_mousse.functions import ResultCollector
from chezmoi_mousse.named_tuples import ManagedTreePaths
from chezmoi_mousse.str_enums import PathKind, StatusCode, TabLabel

if TYPE_CHECKING:
    from chezmoi_mousse.cm_types import PathKindMap, StatusMap


__all__ = ["CmAttributes", "ManagedPaths"]


@dataclass(frozen=True, kw_only=True)
class ManagedPaths:
    rc: ClassVar[type[ResultCollector]] = ResultCollector

    def __post_init__(self) -> None:
        # warm all public cached_property attributes
        for attr_name, value in type(self).__dict__.items():
            if isinstance(value, cached_property):
                getattr(self, attr_name)

    def _get_managed_path_kind_map(self, managed_output: list[str]) -> PathKindMap:
        temp_dict: dict[Path, PathKind] = {}
        paths: list[Path] = [Path(line) for line in managed_output]

        for path in paths:
            if path.is_symlink():
                temp_dict[path] = PathKind.SYMLINK
            elif not path.exists():
                temp_dict[path] = PathKind.EXISTS_FALSE
            else:
                temp_dict[path] = PathKind.UNHANDLED

        # sort the temp_dict by path
        return MappingProxyType(dict(sorted(temp_dict.items())))

    @cached_property
    def _dest_dir(self) -> Path:
        return self.rc.get_dest_dir()

    @cached_property
    def managed_dirs(self) -> PathKindMap:
        return self._get_managed_path_kind_map(
            self.rc.managed_dirs_result.std_out.splitlines()
        )

    @cached_property
    def managed_files(self) -> PathKindMap:
        return self._get_managed_path_kind_map(
            self.rc.managed_files_result.std_out.splitlines()
        )

    # not cached, fast boolean logic
    @property
    def no_managed_paths(self) -> bool:
        return not self.managed_dirs and not self.managed_files

    def _get_status_map(self, lines: list[str], status_col: int) -> StatusMap:
        temp_dict: dict[Path, StatusCode] = {}

        for line in lines:
            temp_dict[Path(line[3:])] = StatusCode(line[status_col])

        return MappingProxyType(dict(sorted(temp_dict.items())))

    def _get_tree_status_map(
        self, status_dirs: StatusMap, n_dirs: frozenset[Path]
    ) -> StatusMap:
        tree_status_dirs: dict[Path, StatusCode] = dict(status_dirs)
        for path in n_dirs:
            tree_status_dirs[path] = StatusCode.N_DIR
        return MappingProxyType(dict(sorted(tree_status_dirs.items())))

    def _create_managed_tree_paths_instance(self, status_col: int) -> ManagedTreePaths:
        dirs_map: StatusMap = self._get_status_map(
            self.rc.status_dirs_result.std_out.splitlines(), status_col
        )
        status_dirs: StatusMap = MappingProxyType(
            {k: v for k, v in dirs_map.items() if v != StatusCode.Space}
        )
        files_map: StatusMap = self._get_status_map(
            self.rc.status_files_result.std_out.splitlines(), status_col
        )
        status_files: StatusMap = MappingProxyType(
            {k: v for k, v in files_map.items() if v != StatusCode.Space}
        )

        _n_dirs = frozenset(
            parent
            for path in (status_dirs | status_files)
            for parent in path.parents
            if parent not in status_dirs
            and parent.is_relative_to(self._dest_dir)
            and parent != self._dest_dir
        )

        _unchanged_dirs = frozenset(
            path
            for path in self.managed_dirs
            if path not in status_dirs and path not in status_files
        )

        return ManagedTreePaths(
            dest_dir=self._dest_dir,
            managed_dirs=self.managed_dirs,
            managed_files=self.managed_files,
            n_dirs=_n_dirs,
            no_managed_paths=self.no_managed_paths,
            no_status_paths=(not status_dirs and not status_files),
            status_dirs=status_dirs,
            status_files=status_files,
            tree_status_dirs=self._get_tree_status_map(dirs_map, _n_dirs),
            unchanged_dirs=_unchanged_dirs,
            unchanged_files=frozenset(
                path
                for path in self.managed_files
                if path not in status_dirs and path not in status_files
            ),
            unchanged_tree_dirs=frozenset(
                path for path in _unchanged_dirs if path not in _n_dirs
            ),
        )

    # cached properties used by the ManagedTree class

    @cached_property
    def apply_tree_paths(self) -> ManagedTreePaths:
        return self._create_managed_tree_paths_instance(status_col=1)

    @cached_property
    def re_add_tree_paths(self) -> ManagedTreePaths:
        return self._create_managed_tree_paths_instance(status_col=0)

    @cached_property
    def managed_paths_set(self) -> frozenset[Path]:
        return frozenset(self.managed_dirs | self.managed_files)


@dataclass
class CmAttributes:
    rc: ClassVar[type[ResultCollector]] = ResultCollector

    add_id = AppIds(TabLabel.add)
    apply_id = AppIds(TabLabel.apply)
    config_id = AppIds(TabLabel.config)
    debug_id = AppIds(TabLabel.debug)
    logs_id = AppIds(TabLabel.logs)
    re_add_id = AppIds(TabLabel.re_add)

    dry_run: bool = True

    dest_dir: Path = field(init=False)
    auto_add: bool = field(init=False)
    auto_commit: bool = field(init=False)
    auto_push: bool = field(init=False)
    paths: ManagedPaths = field(init=False)

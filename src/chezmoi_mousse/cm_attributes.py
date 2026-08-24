from __future__ import annotations

from dataclasses import dataclass, field
from functools import cached_property
from pathlib import Path
from typing import TYPE_CHECKING

from chezmoi_mousse import store
from chezmoi_mousse.named_tuples import ManagedTreePaths
from chezmoi_mousse.str_enums import StatusCode

if TYPE_CHECKING:
    pass


__all__ = ["CmAttributes", "ManagedPaths"]


@dataclass(frozen=True, kw_only=True)
class ManagedPaths:
    def __post_init__(self) -> None:
        # warm all public cached_property attributes
        for attr_name, value in type(self).__dict__.items():
            if isinstance(value, cached_property):
                getattr(self, attr_name)

    # not cached, fast boolean logic
    @property
    def no_managed_paths(self) -> bool:
        return not store.managed_dirs and not store.managed_files

    def _get_status_map(self, lines: list[str], status_col: int) -> dict[Path, str]:
        temp_dict: dict[Path, str] = {}

        for line in lines:
            temp_dict[Path(line[3:])] = line[status_col]

        return dict(sorted(temp_dict.items()))

    def _get_tree_status_map(
        self, status_dirs: dict[Path, StatusCode], n_dirs: frozenset[Path]
    ) -> dict[Path, StatusCode]:
        tree_status_dirs: dict[Path, StatusCode] = dict(status_dirs)
        for path in n_dirs:
            tree_status_dirs[path] = StatusCode.N_DIR
        return dict(sorted(tree_status_dirs.items()))

    def _create_managed_tree_paths_instance(self, status_col: int) -> ManagedTreePaths:
        apply_dir_codes: dict[Path, StatusCode] = {
            path: status.apply_status for path, status in store.status_dirs.items()
        }
        re_add_dir_codes: dict[Path, StatusCode] = {
            path: status.re_add_status for path, status in store.status_dirs.items()
        }

        apply_status_dirs: dict[Path, StatusCode] = {
            path: status
            for path, status in apply_dir_codes.items()
            if status != StatusCode.Space
        }
        apply_status_files: dict[Path, StatusCode] = {
            path: status.apply_status
            for path, status in store.status_files.items()
            if status.apply_status != StatusCode.Space
        }

        re_add_status_dirs: dict[Path, StatusCode] = {
            path: status
            for path, status in re_add_dir_codes.items()
            if status != StatusCode.Space
        }
        re_add_status_files: dict[Path, StatusCode] = {
            path: status.re_add_status
            for path, status in store.status_files.items()
            if status.re_add_status != StatusCode.Space
        }
        dirs_map = apply_dir_codes if status_col == 1 else re_add_dir_codes
        status_dirs = apply_status_dirs if status_col == 1 else re_add_status_dirs
        status_files = apply_status_files if status_col == 1 else re_add_status_files

        _n_dirs = frozenset(
            parent
            for path in status_dirs | status_files
            for parent in path.parents
            if parent not in status_dirs
            and parent.is_relative_to(store.cfg.dest_dir)
            and parent != store.cfg.dest_dir
        )

        _unchanged_dirs = frozenset(
            path
            for path in store.managed_dirs
            if path not in status_dirs and path not in status_files
        )

        return ManagedTreePaths(
            n_dirs=_n_dirs,
            no_status_paths=(not status_dirs and not status_files),
            status_dirs=status_dirs,
            status_files=status_files,
            tree_status_dirs=self._get_tree_status_map(dirs_map, _n_dirs),
            unchanged_dirs=_unchanged_dirs,
            unchanged_files=frozenset(
                path
                for path in store.managed_files
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


@dataclass
class CmAttributes:
    paths: ManagedPaths = field(init=False)

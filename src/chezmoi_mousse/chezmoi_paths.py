from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

from chezmoi_mousse import path_funcs
from chezmoi_mousse.data_types import DirData, NodeData

if TYPE_CHECKING:
    from chezmoi_mousse.str_enums import StatusCode as Sc

__all__ = ["ChezmoiTreePaths", "CmPathChanges"]


type NodeDict = dict[Path, NodeData]


@dataclass(slots=True, kw_only=True)
class ChezmoiTreePaths:
    """The raw source of truth received from chezmoi stdout."""

    _dest_dir: Path
    _man_dirs: dict[Path, Path]
    _man_files: dict[Path, Path]
    _status_dirs: dict[Path, Sc]
    _status_files: dict[Path, Sc]
    _un_man_dirs: set[Path]
    _un_man_files: set[Path]

    file_node_data: NodeDict = field(default_factory=dict[Path, NodeData])
    dir_node_data: NodeDict = field(default_factory=dict[Path, NodeData])

    def __post_init__(self) -> None:
        managed_paths = self._man_dirs.keys() | self._man_files.keys()
        un_managed_paths = self._un_man_dirs | self._un_man_files
        status_paths = self._status_dirs.keys() | self._status_files.keys()
        wanted_files = {
            p for p in self._un_man_files if not path_funcs.is_unwanted_file(p)
        }

        wanted_dirs = {
            p for p in self._un_man_dirs if not path_funcs.is_unwanted_dir(p)
        }
        wanted_paths = wanted_dirs | wanted_files

        self._populate_file_node_data(wanted_files=wanted_files)
        self._populate_dir_node_data(
            managed_paths=managed_paths,
            status_paths=status_paths,
            un_managed_paths=un_managed_paths,
            wanted_paths=wanted_paths,
        )

        self.file_node_data = path_funcs.sort_path_dict(self.file_node_data)
        self.dir_node_data = path_funcs.sort_path_dict(self.dir_node_data)
        all_paths = managed_paths | un_managed_paths
        all_paths.add(self._dest_dir)
        node_data_paths = self.dir_node_data.keys() | self.file_node_data.keys()
        # assert all paths are accounted for
        assert all_paths == node_data_paths, (
            "Mismatch between all paths and node data paths"
        )

    def _populate_file_node_data(self, *, wanted_files: set[Path]) -> None:
        for path in self._man_files.keys() | self._un_man_files:
            managed = path in self._man_files
            self.file_node_data[path] = NodeData(
                dir_path=False,
                exists=True if not managed else path.exists(),
                managed=managed,
                path=path,
                source_path=self._man_files.get(path, None),
                status=self._status_files.get(path, None),
                wanted=path in wanted_files,
            )

    def _populate_dir_node_data(
        self,
        *,
        managed_paths: set[Path],
        status_paths: set[Path],
        un_managed_paths: set[Path],
        wanted_paths: set[Path],
    ) -> None:

        for path in {self._dest_dir} | self._man_dirs.keys() | self._un_man_dirs:
            has_nested_status = False
            has_nested_managed = False
            managed = path in self._man_dirs
            is_dest_dir = path == self._dest_dir
            if is_dest_dir:
                has_nested_status = bool(status_paths)
                has_nested_managed = bool(managed_paths)
            elif managed:
                has_nested_status = path_funcs.any_nested_in(
                    dir_path=path, check_paths=status_paths
                )
                has_nested_managed = path_funcs.any_nested_in(
                    dir_path=path, check_paths=managed_paths
                )
            has_nested_wanted = path_funcs.any_nested_in(
                dir_path=path, check_paths=wanted_paths
            )
            has_nested_un_managed = path_funcs.any_nested_in(
                dir_path=path, check_paths=un_managed_paths
            )
            empty_dir = True
            if has_nested_managed or has_nested_un_managed:
                empty_dir = False
            elif not managed and not has_nested_un_managed:
                empty_dir = any(path.iterdir())
            self.dir_node_data[path] = NodeData(
                dir_data=DirData(
                    dest_dir=is_dest_dir,
                    empty=empty_dir,
                    nested_managed=has_nested_managed,
                    nested_status=has_nested_status,
                    nested_un_managed=has_nested_un_managed,
                    nested_wanted=has_nested_wanted,
                ),
                dir_path=True,
                exists=path.exists() if managed else True,
                managed=managed,
                path=path,
                source_path=self._man_dirs.get(path),
                status=self._status_dirs.get(path, None),
                wanted=path in wanted_paths,
            )

    @property
    def dest_dir_node_data(self) -> NodeData:
        return self.dir_node_data[self._dest_dir]


@dataclass(slots=True, kw_only=True)
class CmPathChanges:
    _old_tree_paths: ChezmoiTreePaths
    _new_tree_paths: ChezmoiTreePaths

    changes_available: bool = False
    add_tree_dirs: NodeDict = field(default_factory=dict[Path, NodeData])
    add_tree_files: NodeDict = field(default_factory=dict[Path, NodeData])
    remove_tree_dirs: set[Path] = field(default_factory=set[Path])
    remove_tree_files: set[Path] = field(default_factory=set[Path])
    change_tree_dirs: NodeDict = field(default_factory=dict[Path, NodeData])
    change_tree_files: NodeDict = field(default_factory=dict[Path, NodeData])

    def __post_init__(self) -> None:
        if self._new_tree_paths != self._old_tree_paths:
            self.changes_available = True

        self._update_add_fields()
        self._update_remove_fields()
        self._update_change_fields()

    def _update_add_fields(self) -> None:

        def get_added_dict(new_nodes: NodeDict, old_nodes: NodeDict) -> NodeDict:
            added = {k: v for k, v in new_nodes.items() if k not in old_nodes}
            return path_funcs.sort_path_dict(added)

        self.add_tree_dirs = get_added_dict(
            self._new_tree_paths.dir_node_data, self._old_tree_paths.dir_node_data
        )
        self.add_tree_files = get_added_dict(
            self._new_tree_paths.file_node_data, self._old_tree_paths.file_node_data
        )

    def _update_remove_fields(self) -> None:
        removed_dirs: set[Path] = (
            self._old_tree_paths.dir_node_data.keys()
            - self._new_tree_paths.dir_node_data.keys()
        )
        removed_files: set[Path] = (
            self._old_tree_paths.file_node_data.keys()
            - self._new_tree_paths.file_node_data.keys()
        )
        self.remove_tree_dirs = path_funcs.get_common_top_level(removed_dirs)
        self.remove_tree_files = {
            p for p in removed_files if self.remove_tree_dirs.isdisjoint(p.parents)
        }

    def _update_change_fields(self) -> None:

        def get_changes_dict(dict1: NodeDict, dict2: NodeDict) -> NodeDict:
            return {
                k: node2
                for k, node2 in dict2.items()
                if k in dict1 and dict1[k] != node2
            }

        all_changed_dirs = get_changes_dict(
            self._old_tree_paths.dir_node_data, self._new_tree_paths.dir_node_data
        )
        self.change_tree_dirs = path_funcs.sort_path_dict(all_changed_dirs)
        change_tree_files = get_changes_dict(
            self._old_tree_paths.file_node_data, self._new_tree_paths.file_node_data
        )
        self.change_tree_files = path_funcs.sort_path_dict(change_tree_files)

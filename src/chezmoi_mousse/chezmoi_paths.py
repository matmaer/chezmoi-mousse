from __future__ import annotations

from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import TYPE_CHECKING

from chezmoi_mousse import path_funcs
from chezmoi_mousse.data_types import DirData, IterDirResult, NodeData

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
        extended_files = {p for p in self._un_man_files if path_funcs.is_extend_file(p)}
        filtered_files = self._un_man_files - extended_files
        extended_dirs = {p for p in self._un_man_dirs if path_funcs.is_extend_dir(p)}
        filtered_dirs = {p for p in self._un_man_dirs if p not in extended_dirs}
        filtered_paths = filtered_dirs | filtered_files

        self._populate_file_node_data(filtered_files=filtered_files)
        self._populate_dir_node_data(
            managed_paths=managed_paths,
            status_paths=status_paths,
            un_managed_paths=un_managed_paths,
            filtered_paths=filtered_paths,
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

    def _populate_file_node_data(self, *, filtered_files: set[Path]) -> None:

        for path in self._man_files.keys() | self._un_man_files:
            managed = path in self._man_files
            exists = True if not managed else path.exists()
            status: Sc | None = self._status_files.get(path, None)
            self.file_node_data[path] = NodeData(
                dir_path=False,
                exists=exists,
                managed=managed,
                path=path,
                source_path=self._man_files.get(path, None),
                status=status,
                filtered=path in filtered_files,
            )

    def _populate_dir_node_data(
        self,
        *,
        managed_paths: set[Path],
        status_paths: set[Path],
        un_managed_paths: set[Path],
        filtered_paths: set[Path],
    ) -> None:
        for path in {self._dest_dir} | self._man_dirs.keys() | self._un_man_dirs:
            nested_status = False
            nested_managed = False
            nested_filtered = False
            nested_un_managed = False

            managed = path in self._man_dirs
            is_dest_dir = path == self._dest_dir
            status = self._status_dirs.get(path, None)
            exists = True if not managed else path.exists()

            if is_dest_dir:
                nested_status = bool(status_paths)
                nested_managed = bool(managed_paths)
                nested_filtered = bool(filtered_paths)
                nested_un_managed = bool(un_managed_paths)

            else:
                nested_filtered = path_funcs.any_nested_in(
                    dir_path=path, check_paths=filtered_paths
                )
                nested_un_managed = path_funcs.any_nested_in(
                    dir_path=path, check_paths=un_managed_paths
                )
            if managed:
                nested_status = path_funcs.any_nested_in(
                    dir_path=path, check_paths=status_paths
                )
                nested_managed = path_funcs.any_nested_in(
                    dir_path=path, check_paths=managed_paths
                )

            self.dir_node_data[path] = NodeData(
                dir_data=DirData(
                    dest_dir=is_dest_dir,
                    nested_managed=nested_managed,
                    nested_status=nested_status,
                    nested_un_managed=nested_un_managed,
                    nested_filtered=nested_filtered,
                ),
                dir_path=True,
                exists=exists,
                managed=managed,
                path=path,
                source_path=self._man_dirs.get(path),
                status=status,
                filtered=path in filtered_paths,
            )

    @property
    def dest_dir_node_data(self) -> NodeData:
        return self.dir_node_data[self._dest_dir]

    def load_un_man_children(self, dir_path: Path) -> IterDirResult:
        dirs = {p: n for p, n in self.dir_node_data.items() if p.parent == dir_path}
        files = {p: n for p, n in self.file_node_data.items() if p.parent == dir_path}
        if dirs or files:
            return IterDirResult(error="", dirs=dirs, files=files)
        result = path_funcs.get_un_man_children(dir_path)
        self.dir_node_data.update(result.dirs)
        self.file_node_data.update(result.files)
        # The children tell us more about this dir than chezmoi unmanaged did.
        children = [*result.dirs.values(), *result.files.values()]
        dir_node = self.dir_node_data[dir_path]
        dir_node.dir_data = replace(
            dir_node.dir_data,
            nested_un_managed=bool(children),
            nested_filtered=any(child.filtered for child in children),
        )
        return result

    def reload_un_man_children(self, old_tree_paths: ChezmoiTreePaths) -> None:
        # Reload the unmanaged dirs of which the children were loaded on demand
        old_paths = old_tree_paths.dir_node_data.keys() | old_tree_paths.file_node_data
        new_paths = self.dir_node_data.keys() | self.file_node_data.keys()
        loaded_dirs = {p.parent for p in old_paths - new_paths}
        # parents first, so nested loaded dirs exist when we get to them
        for dir_path in sorted(loaded_dirs, key=lambda p: len(p.parts)):
            dir_node = self.dir_node_data.get(dir_path)
            if dir_node is None or dir_node.managed or dir_node.dir_data.dest_dir:
                continue
            self.load_un_man_children(dir_path)

    def reuse_unchanged_node_data(self, old_tree_paths: ChezmoiTreePaths) -> None:
        """Keep the old NodeData object for unchanged paths, so the trees and
        store.cm_paths keep sharing the same objects."""
        for new_dict, old_dict in (
            (self.dir_node_data, old_tree_paths.dir_node_data),
            (self.file_node_data, old_tree_paths.file_node_data),
        ):
            for path, node_data in new_dict.items():
                old_node_data = old_dict.get(path)
                if old_node_data is not None and old_node_data == node_data:
                    new_dict[path] = old_node_data


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
        self.remove_tree_dirs = path_funcs.get_common_top_level(dir_paths=removed_dirs)
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

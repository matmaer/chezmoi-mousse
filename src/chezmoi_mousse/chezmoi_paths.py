from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

from chezmoi_mousse import path_funcs
from chezmoi_mousse.data_types import NodeData
from chezmoi_mousse.str_enums import LabelStr

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
    _status_path_set: set[Path]
    _un_man_dirs: set[Path]
    _un_man_files: set[Path]
    _un_man_paths: set[Path]

    file_node_data: NodeDict = field(default_factory=dict[Path, NodeData])
    dir_node_data: NodeDict = field(default_factory=dict[Path, NodeData])

    def __post_init__(self) -> None:

        self._add_dest_dir_node_data()

        self._populate_file_node_data()

        self._populate_dir_node_data()

        self.file_node_data = path_funcs.sort_path_dict(self.file_node_data)
        self.dir_node_data = path_funcs.sort_path_dict(self.dir_node_data)
        man_paths = self._man_dirs.keys() | self._man_files.keys()
        all_paths = man_paths | self._un_man_paths
        all_paths.add(self._dest_dir)
        node_data_paths = self.dir_node_data.keys() | self.file_node_data.keys()
        # assert all paths are accounted for
        assert all_paths == node_data_paths, (
            "Mismatch between all paths and node data paths"
        )

    def _add_dest_dir_node_data(self) -> None:
        has_nested_managed = bool(self._man_dirs.keys() | self._man_files.keys())
        self.dir_node_data[self._dest_dir] = NodeData(
            dest_dir=True,
            dir_path=True,
            exists=True,
            has_nested_managed=has_nested_managed,
            has_nested_status=bool(self._status_path_set),
            has_nested_unmanaged=bool(self._un_man_paths),
            managed=False,
            main_label=LabelStr.dest_dir,
            path=self._dest_dir,
            source_path=None,
            status=None,
            un_wanted_dir=False,
            un_wanted_file=False,
        )

    def _populate_file_node_data(
        self,
    ) -> None:
        for path in self._man_files.keys() | self._un_man_files:
            managed = path in self._man_files
            status_file = path in self._status_files
            is_unwanted = False if managed else path_funcs.is_unwanted_file(path)
            if managed:
                main_label = (
                    LabelStr.status_file if status_file else LabelStr.space_file
                )
            else:
                main_label = (
                    LabelStr.un_wanted_file if is_unwanted else LabelStr.un_man_file
                )
            status = self._status_files.get(path, None)
            source_path = self._man_dirs.get(path)
            self.file_node_data[path] = NodeData(
                dir_path=False,
                exists=True if managed else path.exists(),
                has_nested_status=False,
                has_nested_managed=False,
                main_label=main_label,
                managed=managed,
                path=path,
                source_path=source_path,
                status=status,
                un_wanted_dir=False,
                un_wanted_file=is_unwanted,
            )

    def _populate_dir_node_data(self) -> None:
        un_wanted_dirs = {p for p in self._un_man_dirs if path_funcs.is_unwanted_dir(p)}
        for path in self._man_dirs.keys() | self._un_man_dirs:
            managed = path in self._man_dirs
            status = self._status_dirs.get(path, None)
            is_un_unwanted = False if managed else path in un_wanted_dirs
            has_nested_status = False
            nested_unmanaged = False
            if managed:
                has_nested_status = path_funcs.any_nested_in(
                    dir_path=path, check_paths=self._status_path_set
                )
                nested_unmanaged = path_funcs.any_nested_in(
                    dir_path=path, check_paths=self._un_man_paths
                )
            if managed:
                main_label = (
                    LabelStr.real_status_dir
                    if status is not None
                    else (
                        LabelStr.man_d_no_nested_status
                        if has_nested_status
                        else LabelStr.man_dir_no_status
                    )
                )
            else:
                main_label = (
                    LabelStr.un_wanted_dir if is_un_unwanted else LabelStr.un_man_dir
                )
            has_nested_managed = path_funcs.any_nested_in(
                dir_path=path,
                check_paths=self._man_dirs.keys() | self._man_files.keys(),
            )

            self.dir_node_data[path] = NodeData(
                dir_path=True,
                exists=path.exists() if managed else True,
                has_nested_managed=has_nested_managed,
                has_nested_status=has_nested_status,
                has_nested_unmanaged=nested_unmanaged,
                main_label=main_label,
                managed=managed,
                path=path,
                source_path=self._man_dirs.get(path),
                status=status,
                un_wanted_dir=is_un_unwanted,
                un_wanted_file=False,
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
    remove_tree_dirs: list[Path] = field(default_factory=list[Path])
    remove_tree_files: list[Path] = field(default_factory=list[Path])
    remove_node_map_paths: set[Path] = field(default_factory=set[Path])
    change_tree_dirs: NodeDict = field(default_factory=dict[Path, NodeData])
    change_tree_files: NodeDict = field(default_factory=dict[Path, NodeData])

    def __post_init__(self) -> None:
        if self._new_tree_paths != self._old_tree_paths:
            self.changes_available = True

        def get_added_dict(new_nodes: NodeDict, old_nodes: NodeDict) -> NodeDict:
            added = {k: v for k, v in new_nodes.items() if k not in old_nodes}
            return path_funcs.sort_path_dict(added)

        self.add_tree_dirs = get_added_dict(
            self._new_tree_paths.dir_node_data, self._old_tree_paths.dir_node_data
        )
        self.add_tree_files = get_added_dict(
            self._new_tree_paths.file_node_data, self._old_tree_paths.file_node_data
        )

        all_removed_dirs: set[Path] = (
            self._old_tree_paths.dir_node_data.keys()
            - self._new_tree_paths.dir_node_data.keys()
        )
        self.remove_tree_dirs = path_funcs.get_sorted_top_parents(all_removed_dirs)
        all_removed_files: set[Path] = (
            self._old_tree_paths.file_node_data.keys()
            - self._new_tree_paths.file_node_data.keys()
        )
        self.remove_node_map_paths = all_removed_dirs | all_removed_files
        self.remove_tree_files = [
            path
            for path in all_removed_files
            if not any(parent in self.remove_tree_dirs for parent in path.parents)
        ]

        def get_changes_dict(dict1: NodeDict, dict2: NodeDict) -> NodeDict:
            common_paths = dict1.keys() & dict2.keys()
            changes_dict = {
                k: dict2[k] for k in common_paths if dict1[k].status != dict2[k].status
            }
            return path_funcs.sort_path_dict(changes_dict)

        self.change_tree_dirs = get_changes_dict(
            self._old_tree_paths.dir_node_data, self._new_tree_paths.dir_node_data
        )
        self.change_tree_files = get_changes_dict(
            self._old_tree_paths.file_node_data, self._new_tree_paths.file_node_data
        )

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
    _un_wanted_dirs: set[Path]
    man_paths: set[Path]

    file_node_data: dict[Path, NodeData] = field(default_factory=dict[Path, NodeData])
    dir_node_data: dict[Path, NodeData] = field(default_factory=dict[Path, NodeData])

    def __post_init__(self) -> None:

        self._add_dest_dir_node_data()

        self._populate_file_node_data()

        self._populate_dir_node_data()

        self.file_node_data = path_funcs.sort_path_dict(self.file_node_data)
        self.dir_node_data = path_funcs.sort_path_dict(self.dir_node_data)

        all_paths = self.man_paths | self._un_man_paths
        all_paths.add(self._dest_dir)
        node_data_paths = self.dir_node_data.keys() | self.file_node_data.keys()
        # assert all paths are accounted for
        assert all_paths == node_data_paths, (
            "Mismatch between all paths and node data paths"
        )

    def _add_dest_dir_node_data(self) -> None:
        self.dir_node_data[self._dest_dir] = NodeData(
            dest_dir=True,
            dir_path=True,
            exists=True,
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
                main_label=main_label,
                managed=managed,
                path=path,
                source_path=source_path,
                status=status,
                un_wanted_dir=False,
                un_wanted_file=is_unwanted,
            )

    def _populate_dir_node_data(self) -> None:
        for path in self._man_dirs.keys() | self._un_man_dirs:
            managed = path in self._man_dirs
            status = self._status_dirs.get(path, None)
            is_un_unwanted = False if managed else path in self._un_wanted_dirs
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
            source_path = self._man_dirs.get(path)

            self.dir_node_data[path] = NodeData(
                dir_path=True,
                exists=path.exists() if managed else True,
                has_nested_status=has_nested_status,
                has_nested_unmanaged=nested_unmanaged,
                main_label=main_label,
                managed=managed,
                path=path,
                source_path=source_path,
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

    added_dirs: list[Path] = field(default_factory=list[Path])
    added_files: list[Path] = field(default_factory=list[Path])
    removed_files: list[Path] = field(default_factory=list[Path])
    changed_dirs: dict[Path, NodeData] = field(default_factory=dict[Path, NodeData])
    changed_files: dict[Path, NodeData] = field(default_factory=dict[Path, NodeData])
    top_removed_dirs: list[Path] = field(default_factory=list[Path])
    changes_available: bool = False

    def __post_init__(self) -> None:
        if self._new_tree_paths != self._old_tree_paths:
            self.changes_available = True
        self.added_dirs = path_funcs.sort_paths(
            self._new_tree_paths.dir_node_data.keys()
            - self._old_tree_paths.dir_node_data.keys()
        )
        self.added_files = path_funcs.sort_paths(
            self._new_tree_paths.file_node_data.keys()
            - self._old_tree_paths.file_node_data.keys()
        )
        removed_dirs = path_funcs.sort_paths(
            self._old_tree_paths.dir_node_data.keys()
            - self._new_tree_paths.dir_node_data.keys()
        )
        self.top_removed_dirs = path_funcs.get_sorted_top_parents(removed_dirs)
        self.removed_files = path_funcs.sort_paths(
            self._old_tree_paths.file_node_data.keys()
            - self._new_tree_paths.file_node_data.keys()
        )

        def get_changes_dict(
            dict1: dict[Path, NodeData], dict2: dict[Path, NodeData]
        ) -> dict[Path, NodeData]:
            return {
                key: dict2[key]
                for key in dict1.keys() & dict2.keys()
                if dict1[key] != dict2[key]
            }

        self.changed_dirs = get_changes_dict(
            self._old_tree_paths.dir_node_data,
            self._new_tree_paths.dir_node_data,
        )
        self.changed_files = get_changes_dict(
            self._old_tree_paths.file_node_data,
            self._new_tree_paths.file_node_data,
        )

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
    _status_dirs_pcr: dict[Path, Sc]
    _status_files_pcr: dict[Path, Sc]
    man_dir_set: set[Path]
    man_file_set: set[Path]
    man_path_set: set[Path]
    _space_dir_set: set[Path]
    _space_file_set: set[Path]
    status_path_set: set[Path]
    _un_man_dir_set: set[Path]
    _un_man_file_set: set[Path]
    _un_man_path_set: set[Path]

    file_node_data: dict[Path, NodeData] = field(default_factory=dict[Path, NodeData])
    dir_node_data: dict[Path, NodeData] = field(default_factory=dict[Path, NodeData])

    def __post_init__(self) -> None:

        self._add_dest_dir_node_data()

        self._populate_file_node_data()

        self._populate_default_dir_node_data()

        self._update_has_nested_status()
        self._update_has_nested_managed()

        self.file_node_data = path_funcs.sort_path_dict(self.file_node_data)
        self.dir_node_data = path_funcs.sort_path_dict(self.dir_node_data)

        all_paths = self.man_path_set | self._un_man_path_set
        all_paths.add(self._dest_dir)
        node_data_paths = self.dir_node_data.keys() | self.file_node_data.keys()
        # assert all paths are accounted for
        assert all_paths == node_data_paths, (
            "Mismatch between all paths and node data paths"
        )

    def _add_dest_dir_node_data(self) -> None:
        self.dir_node_data[self._dest_dir] = NodeData(
            dest_dir=True,
            exists=True,
            main_label=LabelStr.dest_dir,
            managed_dir=False,
            managed_file=False,
            path=self._dest_dir,
            status_dir=False,
            status_file=False,
            status=None,
            un_man_dir=False,
            un_man_file=False,
            un_wanted_dir=False,
            un_wanted_file=False,
            has_nested_managed_dirs=bool(self.man_dir_set),
            has_nested_managed=bool(self.man_path_set),
            has_nested_status=bool(self.status_path_set),
            has_nested_un_managed=bool(self._un_man_path_set),
        )

    def _populate_file_node_data(
        self,
    ) -> None:
        for path in self.man_file_set:
            main_label = (
                LabelStr.status_file
                if path not in self._space_file_set
                else LabelStr.space_file
            )
            status = self._status_files_pcr.get(path, None)
            self.file_node_data[path] = NodeData(
                exists=path.exists(),
                main_label=main_label,
                managed_dir=False,
                managed_file=True,
                path=path,
                status_dir=False,
                status_file=path not in self._space_file_set,
                status=status,
                un_man_dir=False,
                un_man_file=False,
                un_wanted_dir=False,
                un_wanted_file=False,
                has_nested_un_managed=False,
            )
        for path in self._un_man_file_set:
            is_unwanted = path_funcs.is_unwanted_file(path)
            main_label = (
                LabelStr.un_wanted_file if is_unwanted else LabelStr.un_man_file
            )
            self.file_node_data[path] = NodeData(
                exists=True,
                main_label=main_label,
                managed_dir=False,
                managed_file=False,
                path=path,
                status_dir=False,
                status_file=False,
                status=None,
                un_man_dir=False,
                un_man_file=True,
                un_wanted_dir=False,
                un_wanted_file=is_unwanted,
                has_nested_un_managed=False,
            )

    def _populate_default_dir_node_data(self) -> None:
        for path in self.man_dir_set:
            status_dir = path in self._status_dirs_pcr
            status = self._status_dirs_pcr.get(path, None)
            main_label = (
                LabelStr.real_status_dir if status_dir else LabelStr.man_dir_no_status
            )
            has_nested_un_managed = path_funcs.any_nested_in(
                dir_path=path, check_paths=self._un_man_path_set
            )
            self.dir_node_data[path] = NodeData(
                exists=path.exists(),
                main_label=main_label,  # different
                managed_dir=True,
                managed_file=False,
                path=path,
                status_dir=status_dir,  # different
                status_file=False,
                status=status,  # different
                un_man_dir=False,
                un_man_file=False,
                un_wanted_dir=False,
                un_wanted_file=False,
                has_nested_un_managed=has_nested_un_managed,
            )
        for path in self._un_man_path_set:
            is_un_unwanted = path_funcs.is_unwanted_dir(path)
            main_label = (
                LabelStr.un_wanted_dir if is_un_unwanted else LabelStr.un_man_dir
            )
            has_nested_un_managed = path_funcs.any_nested_in(
                dir_path=path, check_paths=self._un_man_path_set
            )
            self.dir_node_data[path] = NodeData(
                exists=True,
                main_label=main_label,
                managed_dir=False,
                managed_file=False,
                path=path,
                status_dir=False,
                status_file=False,
                status=None,
                un_man_dir=True,
                un_man_file=False,
                un_wanted_dir=is_un_unwanted,
                un_wanted_file=False,
                has_nested_un_managed=has_nested_un_managed,
            )

    def _update_has_nested_status(self) -> None:
        for path in self.man_dir_set:
            if path_funcs.any_nested_in(
                dir_path=path, check_paths=self.status_path_set
            ):
                self.dir_node_data[path].main_label = LabelStr.man_d_no_nested_status
                self.dir_node_data[path].has_nested_status = True

    def _update_has_nested_managed(self) -> None:
        for path in self.man_dir_set:
            if path_funcs.any_nested_in(dir_path=path, check_paths=self.man_path_set):
                self.dir_node_data[path].has_nested_managed = True

    @property
    def dest_dir_node_data(self) -> NodeData:
        return self.dir_node_data[self._dest_dir]


@dataclass(slots=True, kw_only=True)
class CmPathChanges:
    _old_tree_paths: ChezmoiTreePaths
    _new_tree_paths: ChezmoiTreePaths

    added_dirs: list[Path] = field(default_factory=list[Path])
    added_files: list[Path] = field(default_factory=list[Path])
    removed_dirs: list[Path] = field(default_factory=list[Path])
    removed_files: list[Path] = field(default_factory=list[Path])
    changed_dirs: dict[Path, NodeData] = field(default_factory=dict[Path, NodeData])
    changed_files: dict[Path, NodeData] = field(default_factory=dict[Path, NodeData])
    top_removed_dirs: list[Path] = field(default_factory=list[Path])

    def __post_init__(self) -> None:
        self.added_dirs = path_funcs.sort_paths(
            [
                path
                for path in self._new_tree_paths.man_dir_set
                if path not in self._old_tree_paths.man_dir_set
            ]
        )
        self.added_files = path_funcs.sort_paths(
            [
                path
                for path in self._new_tree_paths.man_file_set
                if path not in self._old_tree_paths.man_file_set
            ]
        )
        self.removed_dirs = path_funcs.sort_paths(
            self._old_tree_paths.man_dir_set - self._new_tree_paths.man_dir_set
        )
        self.removed_files = path_funcs.sort_paths(
            self._old_tree_paths.man_file_set - self._new_tree_paths.man_file_set
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
        self.top_removed_dirs = path_funcs.get_sorted_top_parents(self.removed_dirs)

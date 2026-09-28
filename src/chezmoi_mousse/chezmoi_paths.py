from __future__ import annotations

from dataclasses import dataclass, field
from functools import cached_property
from pathlib import Path

from chezmoi_mousse import path_funcs
from chezmoi_mousse.named_tuples import NodeData
from chezmoi_mousse.str_enums import LabelStr, StatusCode as Sc

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
    missing_managed: set[Path]
    space_dir_set: set[Path]
    space_file_set: set[Path]
    space_path_set: set[Path]
    status_path_set: set[Path]
    un_man_dir_set: set[Path]
    un_man_file_set: set[Path]
    un_man_path_set: set[Path]

    file_node_data: dict[Path, NodeData] = field(default_factory=dict[Path, NodeData])
    dir_node_data: dict[Path, NodeData] = field(default_factory=dict[Path, NodeData])
    add_btn_paths: set[Path] = field(default_factory=set[Path])
    apply_btn_paths: set[Path] = field(default_factory=set[Path])
    destroy_btn_paths: set[Path] = field(default_factory=set[Path])
    forget_btn_paths: set[Path] = field(default_factory=set[Path])
    re_add_btn_paths: set[Path] = field(default_factory=set[Path])

    def __post_init__(self) -> None:

        self._update_file_node_data(
            self._status_files_pcr, self.space_file_set, self.un_man_file_set
        )

        tree_status_dirs = self._update_status_dir_node_data(
            self.space_dir_set, self._status_dirs_pcr, self.status_path_set
        )
        self._update_space_dir_node_data(
            self.space_dir_set, tree_status_dirs, self.un_man_dir_set
        )
        self.file_node_data = path_funcs.sort_path_dict(self.file_node_data)
        self.dir_node_data = path_funcs.sort_path_dict(self.dir_node_data)
        self._update_button_sets(self.dir_node_data | self.file_node_data)

    def _add_file_node_dict_key(
        self, main_label: LabelStr, path: Path, status: Sc
    ) -> None:
        assert self.file_node_data.get(path, None) is None, (
            f"File node data for path {path} already exists"
        )
        self.file_node_data[path] = NodeData(
            main_label=main_label,
            path=path,
            status=status,
        )

    def _update_file_node_data(
        self,
        status_files_pcr: dict[Path, Sc],
        space_file_set: set[Path],
        un_man_file_set: set[Path],
    ) -> None:
        for path, status in status_files_pcr.items():
            self._add_file_node_dict_key(LabelStr.status_file, path, status)

        for path in space_file_set:
            self._add_file_node_dict_key(LabelStr.space_file, path, Sc.SS)

        for path in un_man_file_set:
            if path_funcs.is_unwanted_file(path):
                self._add_file_node_dict_key(LabelStr.un_wanted_file, path, Sc.XX)
            else:
                self._add_file_node_dict_key(LabelStr.un_man_file, path, Sc.UU)

    def _add_dir_node_dict_key(
        self, main_label: LabelStr, path: Path, status: Sc
    ) -> None:
        assert self.dir_node_data.get(path, None) is None, (
            f"Dir node data for path {path} already exists"
        )
        self.dir_node_data[path] = NodeData(
            main_label=main_label,
            path=path,
            status=status,
        )

    def _update_status_dir_node_data(
        self,
        space_dir_set: set[Path],
        status_dirs_pcr: dict[Path, Sc],
        status_path_set: set[Path],
    ) -> dict[Path, Sc]:
        tt_dirs: dict[Path, Sc] = {}
        for path in space_dir_set:
            if path_funcs.any_nested_in(dir_path=path, check_paths=status_path_set):
                self._add_dir_node_dict_key(LabelStr.tt_status_dir, path, Sc.TT)
                tt_dirs[path] = Sc.TT
        for path, status in status_dirs_pcr.items():
            self._add_dir_node_dict_key(LabelStr.real_status_dir, path, status)
        return tt_dirs | status_dirs_pcr

    def _update_space_dir_node_data(
        self,
        space_dir_set: set[Path],
        tree_status_dirs: dict[Path, Sc],
        un_man_dir_set: set[Path],
    ) -> None:
        for path in space_dir_set:
            if path not in tree_status_dirs and path not in un_man_dir_set:
                self._add_dir_node_dict_key(LabelStr.space_dir, path, Sc.SS)

        unwanted_dirs = {
            path for path in un_man_dir_set if path_funcs.is_unwanted_dir(path)
        }
        for path in un_man_dir_set:
            if path in tree_status_dirs:
                continue
            if path in unwanted_dirs:
                self._add_dir_node_dict_key(LabelStr.un_wanted_dir, path, Sc.XX)
            else:
                self._add_dir_node_dict_key(LabelStr.un_man_dir, path, Sc.UU)

    def _update_button_sets(self, all_path_data: dict[Path, NodeData]) -> None:
        for path, node_data in all_path_data.items():
            if node_data.status != Sc.SS:
                self.add_btn_paths.add(path)
            if node_data.status not in (Sc.UU, Sc.XX):
                self.forget_btn_paths.add(path)
                if path not in self.missing_managed:
                    self.destroy_btn_paths.add(path)
            if node_data.status not in (Sc.SS, Sc.UU, Sc.XX):
                self.apply_btn_paths.add(path)
                self.re_add_btn_paths.add(path)

    @cached_property
    def space_paths(self) -> dict[Path, Sc]: ...


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

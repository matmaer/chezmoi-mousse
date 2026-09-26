from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from chezmoi_mousse import path_funcs
from chezmoi_mousse.named_tuples import NodeData
from chezmoi_mousse.str_enums import LabelStr, StatusCode as Sc

__all__ = ["ChezmoiTreePaths", "CmPathChanges"]


@dataclass(slots=True, kw_only=True)
class ChezmoiTreePaths:
    """The raw source of truth received from chezmoi stdout."""

    _status_dirs_pcr: dict[Path, Sc]
    _status_files_pcr: dict[Path, Sc]
    _un_man_dir_set: frozenset[Path]
    _un_man_file_set: frozenset[Path]
    man_dir_set: frozenset[Path]
    man_file_set: frozenset[Path]
    man_path_set: frozenset[Path]
    missing_managed: frozenset[Path]
    status_dir_set: frozenset[Path]
    status_file_set: frozenset[Path]
    status_path_set: frozenset[Path]

    file_node_data: dict[Path, NodeData] = field(default_factory=dict[Path, NodeData])
    dir_node_data: dict[Path, NodeData] = field(default_factory=dict[Path, NodeData])
    add_btn_paths: set[Path] = field(default_factory=set[Path])
    apply_btn_paths: set[Path] = field(default_factory=set[Path])
    destroy_btn_paths: set[Path] = field(default_factory=set[Path])
    forget_btn_paths: set[Path] = field(default_factory=set[Path])
    re_add_btn_paths: set[Path] = field(default_factory=set[Path])

    def __post_init__(self) -> None:

        self._update_file_node_data(
            self._status_files_pcr, self.man_file_set, self._un_man_file_set
        )
        self._update_dir_node_data(
            self._status_dirs_pcr,
            self.man_dir_set,
            self.status_path_set,
            self._un_man_dir_set,
        )
        self.file_node_data = path_funcs.sort_path_dict(self.file_node_data)
        self.dir_node_data = path_funcs.sort_path_dict(self.dir_node_data)
        self.update_button_sets(self.dir_node_data | self.file_node_data)

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
        man_file_set: frozenset[Path],
        un_man_file_set: frozenset[Path],
    ) -> None:
        for path, status in status_files_pcr.items():
            self._add_file_node_dict_key(LabelStr.status_file, path, status)

        man_space_files = man_file_set - self.status_file_set
        for path in man_space_files:
            self._add_file_node_dict_key(LabelStr.space_file, path, Sc.SS)

        for path in un_man_file_set:
            if path_funcs.is_unwanted_file(path):
                self._add_file_node_dict_key(LabelStr.unwanted_file, path, Sc.XX)
            else:
                self._add_file_node_dict_key(LabelStr.unmanaged_file, path, Sc.UU)

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

    def _update_dir_node_data(
        self,
        status_dirs_pcr: dict[Path, Sc],
        man_dir_set: frozenset[Path],
        status_paths: frozenset[Path],
        un_man_dir_set: frozenset[Path],
    ) -> None:
        all_dirs_with_nested_sp: set[Path] = {
            path
            for path in man_dir_set
            if path_funcs.any_nested_in(dir_path=path, check_paths=status_paths)
        }
        status_dirs_with_nested_sp = status_dirs_pcr.keys() & all_dirs_with_nested_sp
        dirty_status_dirs = status_dirs_pcr.keys() & status_dirs_with_nested_sp
        clean_status_dirs = status_dirs_pcr.keys() - dirty_status_dirs

        # we keep the path and real status, but just the label is different
        for path, status in status_dirs_pcr.items():
            if path in clean_status_dirs:
                self._add_dir_node_dict_key(LabelStr.clean_status_dir, path, status)
            elif path in dirty_status_dirs:
                self._add_dir_node_dict_key(LabelStr.dirty_status_dir, path, status)
            else:
                self._add_dir_node_dict_key(LabelStr.status_dir, path, status)

        all_space_dirs = man_dir_set - status_dirs_pcr.keys()
        dirty_space_dirs = all_space_dirs & all_dirs_with_nested_sp
        clean_space_dirs = all_space_dirs - dirty_space_dirs

        for path in clean_space_dirs:
            self._add_dir_node_dict_key(LabelStr.clean_space_dir, path, Sc.SS)

        for path in dirty_space_dirs:
            self._add_dir_node_dict_key(LabelStr.dirty_space_dir, path, Sc.TT)

        for path in un_man_dir_set:
            if path_funcs.is_unwanted_dir(path):
                self._add_dir_node_dict_key(LabelStr.unwanted_dir, path, Sc.XX)
            else:
                self._add_dir_node_dict_key(LabelStr.unmanaged_dir, path, Sc.UU)

    def update_button_sets(self, all_path_data: dict[Path, NodeData]) -> None:
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

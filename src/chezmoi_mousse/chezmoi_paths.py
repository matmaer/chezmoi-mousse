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

    def _add_file_node_dict_key(
        self, main_label: LabelStr, path: Path, status: Sc
    ) -> None:
        assert self.file_node_data.get(path, None) is None
        self.file_node_data[path] = NodeData(
            main_label=main_label,
            path=path,
            status=status,
        )

    def _update_file_node_data_dict(self) -> None:
        for path, status in self._status_files_pcr.items():
            self._add_file_node_dict_key(LabelStr.status_file, path, status)

        man_space_files = self.man_file_set - self.status_file_set
        for path in man_space_files:
            self._add_file_node_dict_key(LabelStr.space_file, path, Sc.SS)

        for path in self._un_man_file_set:
            if path_funcs.is_unwanted_file(path):
                self._add_file_node_dict_key(LabelStr.unwanted_file, path, Sc.XX)
            else:
                self._add_file_node_dict_key(LabelStr.unmanaged_file, path, Sc.UU)

    def _add_dir_node_dict_key(
        self, main_label: LabelStr, path: Path, status: Sc
    ) -> None:
        assert self.dir_node_data.get(path, None) is None
        self.dir_node_data[path] = NodeData(
            main_label=main_label,
            path=path,
            status=status,
        )

    def _update_dir_node_data_dict(self) -> None:
        dirs_with_nested_sp = {
            path
            for path in self.man_dir_set
            if path_funcs.any_nested_in(dir_path=path, check_paths=self.status_path_set)
        }
        clean_status_dirs = self.status_dir_set - dirs_with_nested_sp
        dirty_status_dirs = self.status_dir_set & dirs_with_nested_sp

        for path, status in self._status_dirs_pcr.items():
            if path in clean_status_dirs:
                self._add_dir_node_dict_key(LabelStr.clean_status_dir, path, status)
            elif path in dirty_status_dirs:
                self._add_dir_node_dict_key(LabelStr.dirty_status_dir, path, status)

        space_dir_set = self.man_dir_set - self.status_dir_set
        clean_space_dirs = space_dir_set - dirs_with_nested_sp
        dirty_space_dirs = space_dir_set & dirs_with_nested_sp

        for path in clean_space_dirs:
            self._add_dir_node_dict_key(LabelStr.clean_space_dir, path, Sc.SS)

        for path in dirty_space_dirs:
            self._add_dir_node_dict_key(LabelStr.dirty_space_dir, path, Sc.TT)

        for path in self._un_man_dir_set:
            if path_funcs.is_unwanted_dir(path):
                self._add_dir_node_dict_key(LabelStr.unwanted_dir, path, Sc.XX)
            else:
                self._add_dir_node_dict_key(LabelStr.unmanaged_dir, path, Sc.UU)

    def __post_init__(self) -> None:

        self._update_file_node_data_dict()
        self._update_dir_node_data_dict()
        self.file_node_data = path_funcs.sort_path_dict(self.file_node_data)
        self.dir_node_data = path_funcs.sort_path_dict(self.dir_node_data)


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


@dataclass
class CmOpButtonSets:
    _cm_paths: ChezmoiTreePaths

    add_paths: set[Path] = field(default_factory=set[Path])
    apply_paths: set[Path] = field(default_factory=set[Path])
    destroy_paths: set[Path] = field(default_factory=set[Path])
    forget_paths: set[Path] = field(default_factory=set[Path])
    re_add_paths: set[Path] = field(default_factory=set[Path])

    def __post_init__(self) -> None:

        # TODO: improve this logic to decide if a button should be enabled or not
        all_paths: dict[Path, NodeData] = (
            self._cm_paths.dir_node_data | self._cm_paths.file_node_data
        )
        for path, status in all_paths.items():
            if status == Sc.UU:
                self.add_paths.add(path)
                continue
            self.forget_paths.add(path)
            if path not in self._cm_paths.missing_managed:
                self.destroy_paths.add(path)
            if status == Sc.SS:
                continue
            if status[1] in (Sc.A, Sc.D, Sc.M):
                self.apply_paths.add(path)
            if status[0] in (Sc.A, Sc.D, Sc.M):
                self.re_add_paths.add(path)

        tt_paths = {path for path, status in all_paths.items() if status == Sc.TT}

        for path in tt_paths:
            if path_funcs.any_nested_in(dir_path=path, check_paths=self.add_paths):
                self.add_paths.add(path)
            if path_funcs.any_nested_in(dir_path=path, check_paths=self.apply_paths):
                self.apply_paths.add(path)
            if path_funcs.any_nested_in(dir_path=path, check_paths=self.re_add_paths):
                self.re_add_paths.add(path)

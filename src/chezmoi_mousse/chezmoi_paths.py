from __future__ import annotations

from dataclasses import dataclass, field
from functools import cached_property
from pathlib import Path

from chezmoi_mousse import path_funcs
from chezmoi_mousse.data_types import NodeData
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

        self._populate_file_node_data(
            self._status_files_pcr, self.space_file_set, self.un_man_file_set
        )

        self._populate_default_dir_node_data()
        self._update_node_data_for_tt_dirs()  # overwrite Sc.SS with Sc.TT
        self._update_node_data_for_vv_dirs()  # overwrite remaining Sc.SS with Sc.VV
        self._update_uu_dirs_with_xx_parent()  # overwrite Sc.UU with Sc.XX
        self._update_node_data_for_yy_dirs()  # overwrite remaining Sc.SS with Sc.YY
        self._update_node_data_for_zz_dirs()  # overwrite remaining Sc.SS with Sc.ZZ

        self.file_node_data = path_funcs.sort_path_dict(self.file_node_data)
        self.dir_node_data = path_funcs.sort_path_dict(self.dir_node_data)
        self._update_button_sets(self.dir_node_data | self.file_node_data)

        all_paths = self.man_path_set | self.un_man_path_set
        node_data_paths = self.dir_node_data.keys() | self.file_node_data.keys()
        # assert all paths are accounted for
        assert all_paths == node_data_paths, (
            "Mismatch between all paths and node data paths"
        )

    def _populate_file_node_data(
        self,
        status_files_pcr: dict[Path, Sc],
        space_file_set: set[Path],
        un_man_file_set: set[Path],
    ) -> None:
        for path, status in status_files_pcr.items():
            self.file_node_data[path] = NodeData(
                main_label=LabelStr.status_file,
                path=path,
                status=status,
                exists=path.exists(),
            )
        for path in space_file_set:
            self.file_node_data[path] = NodeData(
                main_label=LabelStr.space_file,
                path=path,
                status=Sc.SS,
                exists=path.exists(),
            )
        for path in un_man_file_set:
            if path_funcs.is_unwanted_file(path):
                self.file_node_data[path] = NodeData(
                    LabelStr.un_wanted_file, path, Sc.XX, exists=True
                )
            else:
                self.file_node_data[path] = NodeData(
                    LabelStr.un_man_file, path, Sc.UU, exists=True
                )

    def _populate_default_dir_node_data(self) -> None:
        for path, status in self._status_dirs_pcr.items():
            self.dir_node_data[path] = NodeData(
                LabelStr.real_status_dir, path, status, exists=path.exists()
            )
        for path in self.space_dir_set:
            self.dir_node_data[path] = NodeData(
                LabelStr.man_dir_no_status, path, Sc.SS, exists=path.exists()
            )
        for path in self.un_man_dir_set:
            if path_funcs.is_unwanted_dir(path):
                self.dir_node_data[path] = NodeData(
                    LabelStr.un_wanted_dir, path, Sc.XX, exists=True
                )
            else:
                self.dir_node_data[path] = NodeData(
                    LabelStr.un_man_dir, path, Sc.UU, exists=True
                )

    def _update_node_data_for_tt_dirs(self) -> None:
        for path, node_data in self.dir_node_data.items():
            if node_data.status is not Sc.SS:
                continue
            if path_funcs.any_nested_in(
                dir_path=path, check_paths=self.status_path_set
            ):
                node_data.main_label = LabelStr.tt_status_dir
                node_data.status = Sc.TT

    def _update_node_data_for_vv_dirs(self) -> None:
        for path, node_data in self.dir_node_data.items():
            if node_data.status is not Sc.SS:
                continue
            if path_funcs.any_nested_in(dir_path=path, check_paths=self.man_path_set):
                node_data.main_label = LabelStr.un_man_dir
                node_data.status = Sc.VV

    def _update_uu_dirs_with_xx_parent(self) -> None:
        xx_dirs: set[Path] = {
            node_data.path
            for node_data in self.dir_node_data.values()
            if node_data.status is Sc.XX
        }
        for node_data in self.dir_node_data.values():
            if node_data.status is not Sc.UU:
                continue
            if path_funcs.any_parents_for(node_data.path, check_paths=xx_dirs):
                self.dir_node_data[node_data.path].status = Sc.XX

    def _update_node_data_for_yy_dirs(self) -> None:
        all_node_data = self.dir_node_data | self.file_node_data
        uu_paths: set[Path] = {
            path
            for path, node_data in all_node_data.items()
            if node_data.status is Sc.UU
        }
        for path, node_data in self.dir_node_data.items():
            if node_data.status is not Sc.SS:
                continue
            if path_funcs.any_nested_in(dir_path=path, check_paths=uu_paths):
                node_data.main_label = LabelStr.un_man_dir
                node_data.status = Sc.YY

    def _update_node_data_for_zz_dirs(self) -> None:
        zz_paths: set[Path] = {
            path
            for path, node_data in self.dir_node_data.items()
            if node_data.status is Sc.ZZ
        }
        for path, node_data in self.dir_node_data.items():
            if node_data.status is not Sc.SS:
                continue
            if path_funcs.any_nested_in(dir_path=path, check_paths=zz_paths):
                node_data.main_label = LabelStr.un_man_dir
                node_data.status = Sc.ZZ

    def _update_button_sets(self, all_path_data: dict[Path, NodeData]) -> None:
        for path, node_data in all_path_data.items():
            if node_data.status != Sc.SS:
                self.add_btn_paths.add(path)
            if node_data.status not in (Sc.UU, Sc.XX):
                self.forget_btn_paths.add(path)
                if node_data.exists:
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

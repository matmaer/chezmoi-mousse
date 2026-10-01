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
        self._update_has_nested_managed_dirs()

        self._update_node_data_for_tt_dirs()  # overwrite Sc.SS with Sc.TT
        self._update_node_data_for_vv_dirs()  # overwrite remaining Sc.SS with Sc.VV
        self._update_uu_dirs_with_xx_parent()  # overwrite Sc.UU with Sc.XX
        self._update_node_data_for_yy_dirs()  # overwrite remaining Sc.SS with Sc.YY
        self._update_node_data_for_zz_dirs()  # overwrite remaining Sc.SS with Sc.ZZ

        self.file_node_data = path_funcs.sort_path_dict(self.file_node_data)
        self.dir_node_data = path_funcs.sort_path_dict(self.dir_node_data)

        all_paths = self.man_path_set | self._un_man_path_set
        node_data_paths = self.dir_node_data.keys() | self.file_node_data.keys()
        # assert all paths are accounted for
        assert all_paths == node_data_paths, (
            "Mismatch between all paths and node data paths"
        )

    def _add_dest_dir_node_data(self) -> None:
        self.dir_node_data[self._dest_dir] = NodeData(
            main_label=LabelStr.dest_dir,
            path=self._dest_dir,
            status=Sc.QQ,
            exists=True,
            dest_dir=True,
            has_nested_status=bool(self.status_path_set),
            has_nested_managed=bool(self.man_path_set),
            has_nested_managed_dirs=bool(self.man_dir_set),
        )

    def _populate_file_node_data(
        self,
    ) -> None:
        for path, status in self._status_files_pcr.items():
            self.file_node_data[path] = NodeData(
                main_label=LabelStr.status_file,
                path=path,
                status=status,
                exists=path.exists(),
                in_status_files_cr=True,
                in_managed_files_cr=True,
                is_space_path=False,
            )
        for path in self._space_file_set:
            self.file_node_data[path] = NodeData(
                main_label=LabelStr.space_file,
                path=path,
                status=Sc.SS,
                exists=path.exists(),
                in_managed_files_cr=True,
                is_space_path=True,
            )
        for path in self._un_man_file_set:
            if path_funcs.is_unwanted_file(path):
                self.file_node_data[path] = NodeData(
                    main_label=LabelStr.un_wanted_file,
                    path=path,
                    status=Sc.XX,
                    exists=True,
                    in_un_man_files_cr=True,
                    matches_unwanted_file=True,
                )
            else:
                self.file_node_data[path] = NodeData(
                    main_label=LabelStr.un_man_file,
                    path=path,
                    status=Sc.UU,
                    exists=True,
                    in_un_man_files_cr=True,
                )

    def _populate_default_dir_node_data(self) -> None:
        for path, status in self._status_dirs_pcr.items():
            self.dir_node_data[path] = NodeData(
                main_label=LabelStr.real_status_dir,
                path=path,
                status=status,
                exists=path.exists(),
                in_status_dirs_cr=True,
                in_managed_dirs_cr=True,
            )
        for path in self._space_dir_set:
            self.dir_node_data[path] = NodeData(
                main_label=LabelStr.man_dir_no_status,
                path=path,
                status=Sc.SS,
                exists=path.exists(),
                in_managed_dirs_cr=True,
                is_space_path=True,
            )
        for path in self._un_man_dir_set:
            if path_funcs.is_unwanted_dir(path):
                self.dir_node_data[path] = NodeData(
                    main_label=LabelStr.un_wanted_dir,
                    path=path,
                    status=Sc.XX,
                    exists=True,
                    in_un_man_dirs_cr=True,
                    matches_unwanted_dir=True,
                )
            else:
                self.dir_node_data[path] = NodeData(
                    main_label=LabelStr.un_man_dir,
                    path=path,
                    status=Sc.UU,
                    exists=True,
                    in_un_man_dirs_cr=True,
                )

    def _update_has_nested_status(self) -> None:
        for path in self.man_dir_set:
            if path_funcs.any_nested_in(
                dir_path=path, check_paths=self.status_path_set
            ):
                self.dir_node_data[path].has_nested_status = True

    def _update_has_nested_managed(self) -> None:
        for path in self.man_dir_set:
            if path_funcs.any_nested_in(dir_path=path, check_paths=self.man_path_set):
                self.dir_node_data[path].has_nested_managed = True

    def _update_has_nested_managed_dirs(self) -> None:
        for path in self.man_dir_set:
            if path_funcs.any_nested_in(dir_path=path, check_paths=self.man_dir_set):
                self.dir_node_data[path].has_nested_managed_dirs = True

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
            node_data.has_nested_managed = True
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

    @cached_property
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

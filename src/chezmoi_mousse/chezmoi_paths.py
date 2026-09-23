from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from chezmoi_mousse import path_funcs
from chezmoi_mousse.str_enums import LabelStr, StatusCode as Sc

__all__ = ["ChezmoiTreePaths", "CmPathChanges"]


@dataclass(slots=True, kw_only=True)
class ChezmoiTreePaths:
    """The raw source of truth received from chezmoi stdout."""

    _status_dirs_pcr: dict[Path, Sc]
    _status_files_pcr: dict[Path, Sc]

    man_dir_set: frozenset[Path]
    man_file_set: frozenset[Path]
    _un_man_dir_set: frozenset[Path]
    _un_man_file_set: frozenset[Path]
    man_path_set: frozenset[Path] = frozenset()
    missing_managed: frozenset[Path] = frozenset()

    status_dir_set: frozenset[Path]
    status_file_set: frozenset[Path]

    status_paths: frozenset[Path] = frozenset()
    _clean_status_dirs: frozenset[Path] = frozenset()
    _dirty_status_dirs: frozenset[Path] = frozenset()

    _space_dirs: frozenset[Path] = frozenset()
    _space_files: frozenset[Path] = frozenset()
    _clean_space_dirs: frozenset[Path] = frozenset()
    _dirty_space_dirs: frozenset[Path] = frozenset()

    # fields for the 8 operate trees (we only need 4 as the other 4 are just the
    # expanded version of the other 4 operate trees, we have 8 here because we have
    # files and dirs in different dicts for each of those 4 trees
    all_tree_dirs: dict[Path, Sc] = field(default_factory=dict[Path, Sc])
    all_tree_files: dict[Path, Sc] = field(default_factory=dict[Path, Sc])
    man_tree_dirs: dict[Path, Sc] = field(default_factory=dict[Path, Sc])
    man_tree_files: dict[Path, Sc] = field(default_factory=dict[Path, Sc])
    status_tree_dirs: dict[Path, Sc] = field(default_factory=dict[Path, Sc])
    status_tree_files: dict[Path, Sc] = field(default_factory=dict[Path, Sc])
    un_man_tree_dirs: dict[Path, Sc] = field(default_factory=dict[Path, Sc])
    un_man_tree_files: dict[Path, Sc] = field(default_factory=dict[Path, Sc])

    path_labels: dict[Path, LabelStr] = field(default_factory=dict[Path, LabelStr])

    def __post_init__(self) -> None:

        self.populate_path_set_fields()

        # # add status files to all trees and set path_labels
        for path, status in self._status_files_pcr.items():
            self.path_labels[path] = LabelStr.status_file
            self.all_tree_files[path] = status
            self.man_tree_files[path] = status
            self.status_tree_files[path] = status
            self.un_man_tree_files[path] = status

        # add managed files without a status to all trees except the status tree and
        # set path_labels which is different for clean and dirty status dirs
        for path in self._space_files:
            self.path_labels[path] = LabelStr.space_file
            self.all_tree_files[path] = Sc.SS
            self.man_tree_files[path] = Sc.SS
            self.un_man_tree_files[path] = Sc.SS

        # Set labels and real status code for status dirs
        for path, status in self._status_dirs_pcr.items():
            status = self._status_dirs_pcr[path]
            if path in self._clean_status_dirs:
                self.path_labels[path] = LabelStr.clean_status_dir
            elif path in self._dirty_status_dirs:
                self.path_labels[path] = LabelStr.dirty_status_dir
            self.status_tree_files[path] = status
            self.all_tree_dirs[path] = status
            self.man_tree_dirs[path] = status
            self.un_man_tree_dirs[path] = status

        # process managed dirs without a status: overwrite status with Sc.TT if needed
        # and set the path_label
        for path in self._clean_space_dirs:
            self.path_labels[path] = LabelStr.clean_space_dir
            self.all_tree_dirs[path] = Sc.SS
            self.man_tree_dirs[path] = Sc.SS
            self.un_man_tree_dirs[path] = Sc.SS
        for path in self._dirty_space_dirs:
            self.path_labels[path] = LabelStr.dirty_space_dir
            self.status_tree_dirs[path] = Sc.TT
            self.all_tree_dirs[path] = Sc.TT
            self.man_tree_dirs[path] = Sc.TT
            self.un_man_tree_dirs[path] = Sc.TT

        # process unmanaged dirs
        for path in self._un_man_dir_set:
            is_unwanted = path_funcs.is_unwanted_dir(path)
            if is_unwanted:
                self.path_labels[path] = LabelStr.unwanted_dir
                self.all_tree_dirs.setdefault(path, Sc.XX)
            else:
                self.path_labels[path] = LabelStr.unmanaged_dir
                self.all_tree_dirs[path] = Sc.UU
                self.un_man_tree_dirs[path] = Sc.UU

        # process unmanaged files
        for path in self._un_man_file_set:
            is_unwanted = path_funcs.is_unwanted_file(path)
            if is_unwanted:
                self.path_labels[path] = LabelStr.unwanted_file
                self.all_tree_files[path] = Sc.XX
            else:
                self.path_labels[path] = LabelStr.unmanaged_file
                self.all_tree_files[path] = Sc.UU
                self.un_man_tree_files[path] = Sc.UU

        # 7. Sort all 8 tree dictionaries
        self.all_tree_dirs = path_funcs.sort_path_dict(self.all_tree_dirs)
        self.all_tree_files = path_funcs.sort_path_dict(self.all_tree_files)
        self.man_tree_dirs = path_funcs.sort_path_dict(self.man_tree_dirs)
        self.man_tree_files = path_funcs.sort_path_dict(self.man_tree_files)
        self.status_tree_dirs = path_funcs.sort_path_dict(self.status_tree_dirs)
        self.status_tree_files = path_funcs.sort_path_dict(self.status_tree_files)
        self.un_man_tree_dirs = path_funcs.sort_path_dict(self.un_man_tree_dirs)
        self.un_man_tree_files = path_funcs.sort_path_dict(self.un_man_tree_files)

    def populate_path_set_fields(self) -> None:
        self.man_path_set = self.man_dir_set | self.man_file_set
        self.missing_managed = frozenset(p for p in self.man_path_set if not p.exists())
        self.status_paths = self.status_dir_set | self.status_file_set

        self._space_files = self.man_file_set - self.status_file_set
        self._space_dirs = self.man_dir_set - self.status_dir_set

        # now process the directories, for their dirty or clean status
        dirs_with_nested_sp = {
            path
            for path in self.man_dir_set
            if path_funcs.any_nested_in(dir_path=path, check_paths=self.status_paths)
        }

        self._clean_space_dirs = self._space_dirs - dirs_with_nested_sp
        self._dirty_space_dirs = self._space_dirs & dirs_with_nested_sp
        self._clean_status_dirs = self.status_dir_set - dirs_with_nested_sp
        self._dirty_status_dirs = self.status_dir_set & dirs_with_nested_sp


@dataclass(slots=True, kw_only=True)
class CmPathChanges:
    _old_tree_paths: ChezmoiTreePaths
    _new_tree_paths: ChezmoiTreePaths

    added_dirs: dict[Path, Sc] = field(default_factory=dict[Path, Sc])
    added_files: dict[Path, Sc] = field(default_factory=dict[Path, Sc])
    removed_dirs: list[Path] = field(default_factory=list[Path])
    removed_files: list[Path] = field(default_factory=list[Path])
    changed_dirs: dict[Path, Sc] = field(default_factory=dict[Path, Sc])
    changed_files: dict[Path, Sc] = field(default_factory=dict[Path, Sc])
    top_removed_dirs: list[Path] = field(default_factory=list[Path])

    def __post_init__(self) -> None:
        self.added_dirs = {
            path: status
            for path, status in self._new_tree_paths.man_tree_dirs.items()
            if path not in self._old_tree_paths.man_dir_set
        }
        self.added_files = {
            path: status
            for path, status in self._new_tree_paths.man_tree_files.items()
            if path not in self._old_tree_paths.man_file_set
        }

        self.removed_dirs = path_funcs.sort_paths(
            self._old_tree_paths.man_dir_set - self._new_tree_paths.man_dir_set
        )
        self.removed_files = path_funcs.sort_paths(
            self._old_tree_paths.man_file_set - self._new_tree_paths.man_file_set
        )

        def get_changes_dict(
            dict1: dict[Path, Sc], dict2: dict[Path, Sc]
        ) -> dict[Path, Sc]:
            return {
                key: dict2[key]
                for key in dict1.keys() & dict2.keys()
                if dict1[key] != dict2[key]
            }

        self.changed_dirs = get_changes_dict(
            self._old_tree_paths.man_tree_dirs, self._new_tree_paths.man_tree_dirs
        )
        self.changed_files = get_changes_dict(
            self._old_tree_paths.man_tree_files, self._new_tree_paths.man_tree_files
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
        all_paths: dict[Path, Sc] = (
            self._cm_paths.all_tree_dirs | self._cm_paths.all_tree_files
        )
        for path, status in all_paths.items():
            if status == Sc.UU:
                self.add_paths.add(path)
                continue
            # we are now checking for status other than Sc.UU, aka managed paths
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

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
    _un_man_dir_set: frozenset[Path]
    _un_man_file_set: frozenset[Path]
    man_dir_set: frozenset[Path]
    man_file_set: frozenset[Path]
    man_path_set: frozenset[Path]
    missing_managed: frozenset[Path]
    status_dir_set: frozenset[Path]
    status_file_set: frozenset[Path]
    status_path_set: frozenset[Path]

    # fields for the 6 'raw data' operate trees, for dirs and files so 12 in total

    managed_only_sp_dirs: dict[Path, Sc] = field(default_factory=dict[Path, Sc])
    managed_only_sp_files: dict[Path, Sc] = field(default_factory=dict[Path, Sc])

    managed_all_mp_dirs: dict[Path, Sc] = field(default_factory=dict[Path, Sc])
    managed_all_mp_files: dict[Path, Sc] = field(default_factory=dict[Path, Sc])

    un_man_plus_sp_dirs: dict[Path, Sc] = field(default_factory=dict[Path, Sc])
    un_man_plus_sp_files: dict[Path, Sc] = field(default_factory=dict[Path, Sc])
    un_man_plus_amp_dirs: dict[Path, Sc] = field(default_factory=dict[Path, Sc])
    un_man_plus_amp_files: dict[Path, Sc] = field(default_factory=dict[Path, Sc])

    un_wanted_plus_sp_dirs: dict[Path, Sc] = field(default_factory=dict[Path, Sc])
    un_wanted_plus_sp_files: dict[Path, Sc] = field(default_factory=dict[Path, Sc])
    un_wanted_plus_amp_dirs: dict[Path, Sc] = field(default_factory=dict[Path, Sc])
    un_wanted_plus_amp_files: dict[Path, Sc] = field(default_factory=dict[Path, Sc])

    path_labels: dict[Path, LabelStr] = field(default_factory=dict[Path, LabelStr])

    def __post_init__(self) -> None:

        self.add_status_files_and_store_label(
            dicts_to_update=(
                self.managed_only_sp_files,
                self.managed_all_mp_files,
                self.un_man_plus_sp_files,
                self.un_man_plus_amp_files,
                self.un_wanted_plus_sp_files,
                self.un_wanted_plus_amp_files,
            )
        )
        self.add_space_files_and_store_label(
            dicts_to_update=(
                self.managed_all_mp_files,
                self.un_man_plus_amp_files,
                self.un_wanted_plus_amp_files,
            )
        )

        dirs_with_nested_sp = {
            path
            for path in self.man_dir_set
            if path_funcs.any_nested_in(dir_path=path, check_paths=self.status_path_set)
        }
        all_dir_dicts: tuple[dict[Path, Sc], ...] = (
            self.managed_only_sp_dirs,
            self.managed_all_mp_dirs,
            self.un_man_plus_sp_dirs,
            self.un_man_plus_amp_dirs,
            self.un_wanted_plus_sp_dirs,
            self.un_wanted_plus_amp_dirs,
        )
        self.add_status_directories_and_store_label(dirs_with_nested_sp, all_dir_dicts)

        space_dir_set = self.man_dir_set - self.status_dir_set
        clean_space_dirs = space_dir_set - dirs_with_nested_sp
        dirty_space_dirs = space_dir_set & dirs_with_nested_sp
        self.process_space_directories(clean_space_dirs, dirty_space_dirs)

        self.sort_constructed_dicts()

    def add_status_files_and_store_label(
        self, dicts_to_update: tuple[dict[Path, Sc], ...]
    ) -> None:
        for path, status in self._status_files_pcr.items():
            assert path not in self.path_labels
            self.path_labels[path] = LabelStr.status_file
            for d in dicts_to_update:
                assert d.get(path, None) is None
                d[path] = status

    def add_space_files_and_store_label(
        self, dicts_to_update: tuple[dict[Path, Sc], ...]
    ) -> None:
        space_files = self.man_file_set - self.status_file_set
        dicts_to_update = (
            self.managed_all_mp_files,
            self.un_man_plus_amp_files,
            self.un_wanted_plus_amp_files,
        )
        for path in space_files:
            assert path not in self.path_labels
            self.path_labels[path] = LabelStr.space_file
            for d in dicts_to_update:
                assert d.get(path, None) is None
                d[path] = Sc.SS

    def add_status_directories_and_store_label(
        self,
        dirs_with_nested_status_paths: set[Path],
        dicts_to_update: tuple[dict[Path, Sc], ...],
    ) -> None:
        clean_status_dirs = self.status_dir_set - dirs_with_nested_status_paths
        dirty_status_dirs = self.status_dir_set & dirs_with_nested_status_paths

        for path, status in self._status_dirs_pcr.items():
            assert path not in self.path_labels
            if path in clean_status_dirs:
                self.path_labels[path] = LabelStr.clean_status_dir
            elif path in dirty_status_dirs:
                self.path_labels[path] = LabelStr.dirty_status_dir
            for d in dicts_to_update:
                assert d.get(path, None) is None
                d[path] = status

    def process_space_directories(
        self, clean_space_dirs: frozenset[Path], dirty_space_dirs: frozenset[Path]
    ) -> None:
        # process managed dirs without a status: overwrite status with Sc.TT if needed
        # and set the path_label
        for path in clean_space_dirs:
            self.path_labels[path] = LabelStr.clean_space_dir
        for path in dirty_space_dirs:
            self.path_labels[path] = LabelStr.dirty_space_dir
            # call setdefault() to avoid overwriting dirs with a real status
            self.managed_only_sp_dirs[path] = Sc.TT
            self.un_man_plus_sp_dirs[path] = Sc.TT
            self.un_wanted_plus_sp_dirs[path] = Sc.TT

        # add managed dirs without a status to all trees except 'only_sp' tree
        # call setdefault() to avoid overwriting Sc.TT
        space_dirs = self.man_dir_set - self.status_dir_set
        for path in space_dirs:
            self.managed_all_mp_dirs.setdefault(path, Sc.SS)
            self.un_man_plus_amp_dirs.setdefault(path, Sc.SS)
            self.un_wanted_plus_amp_dirs.setdefault(path, Sc.SS)

        # process unmanaged dirs
        for path in self._un_man_dir_set:
            is_unwanted = path_funcs.is_unwanted_dir(path)
            if is_unwanted:
                self.path_labels[path] = LabelStr.unwanted_dir
                self.un_wanted_plus_sp_dirs.setdefault(path, Sc.XX)
                self.un_wanted_plus_amp_dirs.setdefault(path, Sc.XX)
            else:
                self.path_labels[path] = LabelStr.unmanaged_dir
                self.un_man_plus_sp_dirs.setdefault(path, Sc.UU)
                self.un_man_plus_amp_dirs.setdefault(path, Sc.UU)
                self.un_wanted_plus_sp_dirs.setdefault(path, Sc.UU)
                self.un_wanted_plus_amp_dirs.setdefault(path, Sc.UU)

        # process unmanaged files
        for path in self._un_man_file_set:
            is_unwanted = path_funcs.is_unwanted_file(path)
            if is_unwanted:
                self.path_labels[path] = LabelStr.unwanted_file
                self.un_wanted_plus_sp_files.setdefault(path, Sc.XX)
                self.un_wanted_plus_amp_files.setdefault(path, Sc.XX)
            else:
                self.path_labels[path] = LabelStr.unmanaged_file
                self.un_man_plus_sp_files.setdefault(path, Sc.UU)
                self.un_man_plus_amp_files.setdefault(path, Sc.UU)
                self.un_wanted_plus_sp_files.setdefault(path, Sc.UU)
                self.un_wanted_plus_amp_files.setdefault(path, Sc.UU)

    def sort_constructed_dicts(self) -> None:
        self.managed_only_sp_dirs = path_funcs.sort_path_dict(self.managed_only_sp_dirs)
        self.managed_only_sp_files = path_funcs.sort_path_dict(
            self.managed_only_sp_files
        )

        self.managed_all_mp_dirs = path_funcs.sort_path_dict(self.managed_all_mp_dirs)
        self.managed_all_mp_files = path_funcs.sort_path_dict(self.managed_all_mp_files)

        self.un_man_plus_sp_dirs = path_funcs.sort_path_dict(self.un_man_plus_sp_dirs)
        self.un_man_plus_sp_files = path_funcs.sort_path_dict(self.un_man_plus_sp_files)

        self.un_man_plus_amp_dirs = path_funcs.sort_path_dict(self.un_man_plus_amp_dirs)
        self.un_man_plus_amp_files = path_funcs.sort_path_dict(
            self.un_man_plus_amp_files
        )

        self.un_wanted_plus_sp_dirs = path_funcs.sort_path_dict(
            self.un_wanted_plus_sp_dirs
        )
        self.un_wanted_plus_sp_files = path_funcs.sort_path_dict(
            self.un_wanted_plus_sp_files
        )

        self.un_wanted_plus_amp_dirs = path_funcs.sort_path_dict(
            self.un_wanted_plus_amp_dirs
        )
        self.un_wanted_plus_amp_files = path_funcs.sort_path_dict(
            self.un_wanted_plus_amp_files
        )


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
            for path, status in self._new_tree_paths.managed_all_mp_dirs.items()
            if path not in self._old_tree_paths.man_dir_set
        }
        self.added_files = {
            path: status
            for path, status in self._new_tree_paths.managed_all_mp_files.items()
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
            self._old_tree_paths.managed_all_mp_dirs,
            self._new_tree_paths.managed_all_mp_dirs,
        )
        self.changed_files = get_changes_dict(
            self._old_tree_paths.managed_all_mp_files,
            self._new_tree_paths.managed_all_mp_files,
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
            self._cm_paths.un_wanted_plus_sp_dirs
            | self._cm_paths.un_wanted_plus_sp_files
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

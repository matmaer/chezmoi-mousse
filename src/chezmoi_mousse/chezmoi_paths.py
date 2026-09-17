from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from chezmoi_mousse import path_funcs
from chezmoi_mousse.str_enums import StatusCode as Sc


@dataclass(slots=True, kw_only=True)
class ChezmoiTreePaths:
    """The raw source of truth received from Chezmoi. Takes the command results (cr)
    their stdout to construct the dicts."""

    _man_dirs_list: list[str]
    _man_files_list: list[str]
    _status_dirs_list: list[str]
    _status_files_list: list[str]
    _unman_dirs_list: list[str]
    _unman_files_list: list[str]

    all_dirs: dict[Path, Sc] = field(default_factory=dict[Path, Sc])
    all_files: dict[Path, Sc] = field(default_factory=dict[Path, Sc])
    managed_dirs: dict[Path, Sc] = field(default_factory=dict[Path, Sc])
    managed_files: dict[Path, Sc] = field(default_factory=dict[Path, Sc])
    status_dirs: dict[Path, Sc] = field(default_factory=dict[Path, Sc])
    status_files: dict[Path, Sc] = field(default_factory=dict[Path, Sc])

    def __post_init__(self) -> None:

        managed_dirs = {Path(p): Sc.SS for p in self._man_dirs_list}
        managed_files = {Path(p): Sc.SS for p in self._man_files_list}
        status_dirs = {
            Path(line[3:]): Sc(line[:2])
            for line in self._status_dirs_list
            if Sc.R.value not in line[:2]  # TODO: implement R
        }
        status_files = {
            Path(line[3:]): Sc(line[:2])
            for line in self._status_files_list
            if Sc.R.value not in line[:2]  # TODO: implement R
        }

        # Update managed files dict
        for path, status in status_files.items():
            managed_files[path] = status

        # add or update dir dicts with status Sc.SS but with nested status paths
        real_status_paths = status_dirs.keys() | status_files.keys()
        for path in managed_dirs:
            if path in status_dirs:
                continue  # we don't want to overwrite a real status
            if path_funcs.any_nested_in(dir_path=path, check_paths=real_status_paths):
                status_dirs[path] = Sc.TT
                managed_dirs[path] = Sc.TT  # overwrites Sc.SS

        # Add dict items for all managed paths
        all_dirs = {Path(p): Sc.UU for p in self._unman_dirs_list}
        all_files = {Path(p): Sc.UU for p in self._unman_files_list}
        for path, status in managed_files.items():
            all_files[path] = status
        for path, status in managed_dirs.items():
            all_dirs[path] = status

        self.all_dirs = path_funcs.sort_path_dict(all_dirs)
        self.all_files = path_funcs.sort_path_dict(all_files)
        self.managed_dirs = path_funcs.sort_path_dict(managed_dirs)
        self.managed_files = path_funcs.sort_path_dict(managed_files)
        self.status_dirs = path_funcs.sort_path_dict(status_dirs)
        self.status_files = path_funcs.sort_path_dict(status_files)


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
            for path, status in self._new_tree_paths.managed_dirs.items()
            if path not in self._old_tree_paths.managed_dirs
        }
        self.added_files = {
            path: status
            for path, status in self._new_tree_paths.managed_files.items()
            if path not in self._old_tree_paths.managed_files
        }

        self.removed_dirs = [
            path
            for path in self._old_tree_paths.managed_dirs
            if path not in self._new_tree_paths.managed_dirs
        ]
        self.removed_files = [
            path
            for path in self._old_tree_paths.managed_files
            if path not in self._new_tree_paths.managed_files
        ]

        def get_changes_dict(
            dict1: dict[Path, Sc], dict2: dict[Path, Sc]
        ) -> dict[Path, Sc]:
            return {
                key: dict2[key]
                for key in dict1.keys() & dict2.keys()
                if dict1[key] != dict2[key]
            }

        self.changed_dirs = get_changes_dict(
            self._old_tree_paths.managed_dirs, self._new_tree_paths.managed_dirs
        )
        self.changed_files = get_changes_dict(
            self._old_tree_paths.managed_files, self._new_tree_paths.managed_files
        )
        self.top_removed_dirs = path_funcs.get_sorted_top_parents(self.removed_dirs)


@dataclass
class ChezmoiPathSets:
    _cm_paths: ChezmoiTreePaths

    missing: set[Path] = field(default_factory=set[Path])
    add_paths: set[Path] = field(default_factory=set[Path])
    apply_paths: set[Path] = field(default_factory=set[Path])
    destroy_paths: set[Path] = field(default_factory=set[Path])
    forget_paths: set[Path] = field(default_factory=set[Path])
    re_add_paths: set[Path] = field(default_factory=set[Path])

    def __post_init__(self) -> None:
        # TODO: improve this logic to decide if a button should be enabled or not

        all_paths: dict[Path, Sc] = self._cm_paths.all_dirs | self._cm_paths.all_files
        managed_paths: set[Path] = (
            self._cm_paths.managed_dirs.keys() | self._cm_paths.managed_files.keys()
        )
        self.missing = {p for p in (managed_paths) if not p.exists()}

        for path, status in all_paths.items():
            if status == Sc.UU:
                self.add_paths.add(path)
                continue
            # we are now checking for status other than Sc.UU, aka managed paths
            self.forget_paths.add(path)
            if path not in self.missing:
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

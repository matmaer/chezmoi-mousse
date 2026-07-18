from __future__ import annotations

import json
import os
import shutil
from dataclasses import dataclass, field, fields
from functools import cached_property
from pathlib import Path
from typing import TYPE_CHECKING

from chezmoi_mousse.app_ids import AppIds
from chezmoi_mousse.run_cmd import ChezmoiCommand, CommandResult
from chezmoi_mousse.str_enums import StatusCode, TabLabel

if TYPE_CHECKING:
    from chezmoi_mousse.type_checking import ParsedJson

__all__ = ["AppState"]


@dataclass(frozen=True, slots=True)
class AppEnvVars:
    chezmoi_subshell: bool = os.environ.get("CHEZMOI_SUBSHELL") == "1"
    debug_mode: bool = os.environ.get("CHEZMOI_MOUSSE_DEBUG_MODE") == "1"
    pilot_mode: bool = os.environ.get("CHEZMOI_MOUSSE_PILOT_MODE") == "1"
    pretend_fail: bool = os.environ.get("CHEZMOI_MOUSSE_PRETEND_FAIL") == "1"


@dataclass(frozen=True, slots=True)
class TabIds:
    add = AppIds(TabLabel.add)
    apply = AppIds(TabLabel.apply)
    config = AppIds(TabLabel.config)
    debug = AppIds(TabLabel.debug)
    logs = AppIds(TabLabel.logs)
    re_add = AppIds(TabLabel.re_add)


@dataclass(slots=True, frozen=True, kw_only=True)
class CmdResults:
    cat_config: CommandResult
    doctor: CommandResult
    dump_config: CommandResult
    git_log: CommandResult
    ignored: CommandResult
    managed_dirs: CommandResult
    managed_files: CommandResult
    status_dirs: CommandResult
    status_files: CommandResult
    template_data: CommandResult


@dataclass
class AppData:
    chezmoi_bin: str | None = shutil.which("chezmoi")
    git_bin: str | None = shutil.which("git")

    run_cmd: ChezmoiCommand = field(default_factory=ChezmoiCommand)
    env_vars: AppEnvVars = field(default_factory=AppEnvVars)
    ids: TabIds = field(default_factory=TabIds)


class ParsedConfig:

    def __init__(self, dump_config_result: CommandResult) -> None:
        self.parsed_config: ParsedJson = json.loads(dump_config_result.std_out)

    @cached_property
    def dest_dir(self) -> Path:
        return Path(self.parsed_config["destDir"])

    @cached_property
    def auto_add(self) -> bool:
        return self.parsed_config["git"]["autoadd"]

    @cached_property
    def auto_commit(self) -> bool:
        return self.parsed_config["git"]["autocommit"]

    @cached_property
    def auto_push(self) -> bool:
        return self.parsed_config["git"]["autopush"]


@dataclass(slots=True, frozen=True, kw_only=True)
class PathSets:
    managed_dirs: frozenset[Path] = frozenset()
    managed_files: frozenset[Path] = frozenset()
    managed_paths: frozenset[Path] = frozenset()

    status_dirs: frozenset[Path] = frozenset()
    status_files: frozenset[Path] = frozenset()
    status_paths: frozenset[Path] = frozenset()

    apply_status_dirs: frozenset[Path] = frozenset()
    apply_status_files: frozenset[Path] = frozenset()
    apply_status_dirs: frozenset[Path] = frozenset()
    apply_n_dirs: frozenset[Path] = frozenset()

    re_add_status_files: frozenset[Path] = frozenset()
    re_add_status_dirs: frozenset[Path] = frozenset()
    re_add_status_paths: frozenset[Path] = frozenset()
    re_add_n_dirs: frozenset[Path] = frozenset()


@dataclass(slots=True, frozen=True, kw_only=True)
class PathStatus:
    apply_files: dict[Path, StatusCode] = field(default_factory=lambda: {})
    apply_dirs: dict[Path, StatusCode] = field(default_factory=lambda: {})
    apply_paths: dict[Path, StatusCode] = field(default_factory=lambda: {})
    re_add_files: dict[Path, StatusCode] = field(default_factory=lambda: {})
    re_add_dirs: dict[Path, StatusCode] = field(default_factory=lambda: {})
    re_add_paths: dict[Path, StatusCode] = field(default_factory=lambda: {})

    def _clear_cache(self) -> None:
        # clears the cache for the methods when creating a new instance
        for attr_name in dir(self.__class__):
            attr = getattr(self.__class__, attr_name)
            if hasattr(attr, "cache_clear") and callable(attr.cache_clear):
                attr.cache_clear()


@dataclass(frozen=True, slots=True, kw_only=True)
class ChangedPaths:
    added_paths: list[Path] = field(default_factory=lambda: [])
    changed_paths: list[Path] = field(default_factory=lambda: [])
    changed_status_paths: list[Path] = field(default_factory=lambda: [])
    loading_modal_results: list[CommandResult] = field(default_factory=lambda: [])
    removed_paths: list[Path] = field(default_factory=lambda: [])


@dataclass(frozen=True, slots=True, kw_only=True)
class AppIssues:
    cmd_results_error: str | None = None
    changed_config: str | None = None


@dataclass(slots=True, frozen=True, kw_only=True)
class AppState:
    path_sets: PathSets = PathSets()
    path_status: PathStatus = PathStatus()
    changed_paths: ChangedPaths = field(default_factory=lambda: ChangedPaths())


def update_app_state() -> AppState:
    try:
        [getattr(CmdResults, f.name) for f in fields(CmdResults)]
    except AttributeError as attrib_error:
        raise Exception from attrib_error
    return AppState()

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field, fields
from functools import cached_property
from pathlib import Path
from typing import TYPE_CHECKING

from chezmoi_mousse.app_ids import AppIds
from chezmoi_mousse.run_cmd import ChezmoiCommand, CommandResult, ReadCmd
from chezmoi_mousse.str_enums import StatusCode, TabLabel

if TYPE_CHECKING:
    from chezmoi_mousse.type_checking import ParsedJson

__all__ = ["CmAttributes"]


@dataclass(frozen=True, kw_only=True)
class CmdResults:
    cat_config: CommandResult = field(default_factory=lambda: CommandResult())
    doctor: CommandResult = field(default_factory=lambda: CommandResult())
    dump_config: CommandResult = field(default_factory=lambda: CommandResult())
    git_log: CommandResult = field(default_factory=lambda: CommandResult())
    ignored: CommandResult = field(default_factory=lambda: CommandResult())
    managed_dirs: CommandResult = field(default_factory=lambda: CommandResult())
    managed_files: CommandResult = field(default_factory=lambda: CommandResult())
    status_dirs: CommandResult = field(default_factory=lambda: CommandResult())
    status_files: CommandResult = field(default_factory=lambda: CommandResult())
    template_data: CommandResult = field(default_factory=lambda: CommandResult())


@dataclass(frozen=True, slots=True)
class TabIds:
    add = AppIds(TabLabel.add)
    apply = AppIds(TabLabel.apply)
    config = AppIds(TabLabel.config)
    debug = AppIds(TabLabel.debug)
    logs = AppIds(TabLabel.logs)
    re_add = AppIds(TabLabel.re_add)


@dataclass(frozen=True, slots=True, kw_only=True)
class ChangedPaths:
    any_changed_path: bool = True
    added_paths: list[Path] = field(default_factory=lambda: [])
    changed_status_paths: list[Path] = field(default_factory=lambda: [])
    removed_paths: list[Path] = field(default_factory=lambda: [])


@dataclass(slots=True, frozen=True, kw_only=True)
class PathSets:
    managed_dirs: frozenset[Path] = frozenset()
    managed_files: frozenset[Path] = frozenset()

    status_dirs: frozenset[Path] = frozenset()
    status_files: frozenset[Path] = frozenset()

    apply_status_dirs: frozenset[Path] = frozenset()
    apply_status_files: frozenset[Path] = frozenset()
    apply_status_paths: frozenset[Path] = frozenset()
    apply_n_dirs: frozenset[Path] = frozenset()

    re_add_status_files: frozenset[Path] = frozenset()
    re_add_status_dirs: frozenset[Path] = frozenset()
    re_add_status_paths: frozenset[Path] = frozenset()
    re_add_n_dirs: frozenset[Path] = frozenset()

    @cached_property
    def managed_paths(self) -> frozenset[Path]:
        return self.managed_dirs | self.managed_files

    @cached_property
    def status_paths(self) -> frozenset[Path]:
        return self.status_dirs | self.status_files

    @cached_property
    def unchanged_dirs(self) -> frozenset[Path]:
        return self.managed_dirs - self.status_dirs

    @cached_property
    def unchanged_files(self) -> frozenset[Path]:
        return self.managed_files - self.status_files

    @cached_property
    def unchanged_paths(self) -> frozenset[Path]:
        return self.unchanged_dirs | self.unchanged_files


@dataclass(slots=True, frozen=True, kw_only=True)
class PathStatus:
    apply_files: dict[Path, StatusCode] = field(default_factory=lambda: {})
    apply_dirs: dict[Path, StatusCode] = field(default_factory=lambda: {})
    apply_paths: dict[Path, StatusCode] = field(default_factory=lambda: {})
    re_add_files: dict[Path, StatusCode] = field(default_factory=lambda: {})
    re_add_dirs: dict[Path, StatusCode] = field(default_factory=lambda: {})
    re_add_paths: dict[Path, StatusCode] = field(default_factory=lambda: {})

    def __post_init__(self) -> None:
        # clears the cache for the methods when creating a new instance
        for attr_name in dir(self.__class__):
            attr = getattr(self.__class__, attr_name)
            if hasattr(attr, "cache_clear") and callable(attr.cache_clear):
                attr.cache_clear()


@dataclass(frozen=True, slots=True, kw_only=True)
class AppIssues:
    cmd_results_error: str | None = None
    changed_config: str | None = None


@dataclass(slots=True, frozen=True, kw_only=True)
class ParsedJsonStdout:
    config_dump: ParsedJson = field(default_factory=lambda: {})
    template_data: ParsedJson = field(default_factory=lambda: {})


@dataclass(slots=True, frozen=True)
class ParsedConfig:

    parsed_config_dump: ParsedJson = field(default_factory=lambda: {})

    @cached_property
    def dest_dir(self) -> Path:
        return Path(self.parsed_config_dump["destDir"])

    @cached_property
    def auto_add(self) -> bool:
        return self.parsed_config_dump["git"]["autoadd"]

    @cached_property
    def auto_commit(self) -> bool:
        return self.parsed_config_dump["git"]["autocommit"]

    @cached_property
    def auto_push(self) -> bool:
        return self.parsed_config_dump["git"]["autopush"]


@dataclass(slots=True, frozen=True, kw_only=True)
class ParsedJsonOutputs:

    config_dump: ParsedJson = field(default_factory=lambda: {})
    template_data: ParsedJson = field(default_factory=lambda: {})

    @cached_property
    def dest_dir(self) -> Path:
        return Path(self.config_dump["destDir"])

    @cached_property
    def auto_add(self) -> bool:
        return self.config_dump["git"]["autoadd"]

    @cached_property
    def auto_commit(self) -> bool:
        return self.config_dump["git"]["autocommit"]

    @cached_property
    def auto_push(self) -> bool:
        return self.config_dump["git"]["autopush"]


@dataclass(slots=True, frozen=True, kw_only=True)
class CmAttributes:
    parsed_json: dict[ReadCmd, ParsedJson] = field(default_factory=lambda: {})
    changed_paths: ChangedPaths = field(default_factory=lambda: ChangedPaths())
    debug_mode: bool = os.environ.get("CHEZMOI_MOUSSE_DEBUG_MODE") == "1"
    ids: TabIds = TabIds()
    path_sets: PathSets = PathSets()
    path_status: PathStatus = PathStatus()
    run_cmd: ChezmoiCommand = ChezmoiCommand()
    sets: PathSets = PathSets()

    @classmethod
    def _check_cmd_results(cls) -> None:
        try:
            [getattr(CmdResults, f.name) for f in fields(CmdResults)]
        except AttributeError as attrib_error:
            raise Exception from attrib_error

    @classmethod
    def update_attributes(cls, read_commands: list[ReadCmd] | None = None) -> None:
        if read_commands is None:
            cls._check_cmd_results()
            cls._update_parsed_json()

    @classmethod
    def _update_parsed_json(cls) -> None:
        for read_cmd in ReadCmd.json_output_commands():
            cmd_result = cls.get_cmd_result(read_cmd)
            cls.parsed_json[read_cmd] = json.loads(cmd_result.std_out)
            if read_cmd == ReadCmd.dump_config:
                cls.cfg = ParsedConfig(parsed_config_dump=cls.parsed_json[read_cmd])

    @classmethod
    def get_all_cmd_results(cls) -> list[CommandResult]:
        return [getattr(CmdResults, f.name) for f in fields(CmdResults)]

    @classmethod
    def get_cmd_result(cls, read_cmd: ReadCmd) -> CommandResult:
        return getattr(CmdResults, read_cmd.name)

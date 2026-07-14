import os
import shutil
import traceback
from dataclasses import dataclass, field
from functools import cached_property
from pathlib import Path
from typing import NamedTuple

from ._app_ids import AppIds
from ._cmd_results import CachedData, CmdResults, CommandResult, ParsedJson
from ._run_cmd import ChezmoiCommand
from ._str_enums import TabLabel

__all__ = ["AppData"]


class AppEnvVars(NamedTuple):
    chezmoi_subshell: bool = os.environ.get("CHEZMOI_SUBSHELL") == "1"
    debug_mode: bool = os.environ.get("CHEZMOI_MOUSSE_DEBUG_MODE") == "1"
    pilot_mode: bool = os.environ.get("CHEZMOI_MOUSSE_PILOT_MODE") == "1"
    pretend_fail: bool = os.environ.get("CHEZMOI_MOUSSE_PRETEND_FAIL") == "1"


class TabIds(NamedTuple):
    add = AppIds(TabLabel.add)
    apply = AppIds(TabLabel.apply)
    config = AppIds(TabLabel.config)
    debug = AppIds(TabLabel.debug)
    logs = AppIds(TabLabel.logs)
    re_add = AppIds(TabLabel.re_add)


@dataclass
class ParsedConfigDump:
    parsed_cfg: ParsedJson = field(default_factory=lambda: {})

    @cached_property
    def dest_dir(self) -> Path:
        return Path(self.parsed_cfg["destDir"])

    @cached_property
    def auto_add(self) -> bool:
        return self.parsed_cfg["git"]["autoadd"]

    @cached_property
    def auto_commit(self) -> bool:
        return self.parsed_cfg["git"]["autocommit"]

    @cached_property
    def auto_push(self) -> bool:
        return self.parsed_cfg["git"]["autopush"]


@dataclass
class AppData:

    chezmoi_bin: str | None = shutil.which("chezmoi")
    git_bin: str | None = shutil.which("git")
    stacktrace_path: Path = Path(__file__).parent / "stacktrace.log"

    ids: TabIds = field(default_factory=TabIds)
    env_vars: AppEnvVars = field(default_factory=AppEnvVars)
    run_cmd: ChezmoiCommand = field(default_factory=ChezmoiCommand)
    cmd_results: CmdResults = field(default_factory=CmdResults)
    cache: CachedData = CachedData.init_empty()
    cfg: ParsedConfigDump = field(default_factory=ParsedConfigDump)

    # keep track of changes after an operation
    added_paths: list[Path] = field(default_factory=lambda: [])
    changed_paths: list[Path] = field(default_factory=lambda: [])
    changed_status_paths: list[Path] = field(default_factory=lambda: [])
    loading_modal_results: list[CommandResult] = field(default_factory=lambda: [])
    removed_paths: list[Path] = field(default_factory=lambda: [])

    def __post_init__(self) -> None:
        if self.stacktrace_path.exists():
            self.stacktrace_path.unlink()

    def save_stacktrace(self):
        with Path.open(self.stacktrace_path, "a") as f:
            traceback.print_exc(file=f)

    def update_cache(self, update_cfg: bool = False):
        self.cache = CachedData(
            managed_dirs=self.cmd_results.managed_dirs_set,
            managed_files=self.cmd_results.managed_files_set,
            managed_paths=self.cmd_results.managed_paths_set,
            status_dirs=self.cmd_results.status_dirs_set,
            status_files=self.cmd_results.status_files_set,
            status_paths=self.cmd_results.status_paths_set,
            unchanged_dirs=self.cmd_results.unchanged_dirs_set,
            unchanged_files=self.cmd_results.unchanged_files_set,
            unchanged_paths=self.cmd_results.unchanged_paths_set,
            dir_status_lines=self.cmd_results.dir_status_lines,
            file_status_lines=self.cmd_results.file_status_lines,
            path_status_lines=self.cmd_results.path_status_lines,
        )
        if update_cfg:
            self.cfg = ParsedConfigDump()

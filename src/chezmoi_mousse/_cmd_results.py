from __future__ import annotations

from dataclasses import dataclass, field, fields
from pathlib import Path
from typing import TYPE_CHECKING

from textual.widgets import Button, Label, Static

from ._run_cmd import ChezmoiCommand, ReadCmd
from ._str_enum_names import Tcss
from ._str_enums import SectionLabel, StatusCode, TabLabel

if TYPE_CHECKING:
    from typing import Any

    from ._app_ids import AppIds
    from ._run_cmd import CommandResult

__all__ = ["CMD", "CachedData", "DirContentBtn", "ParsedJson"]

type ParsedJson = dict[str, Any]


class DirContentBtn(Button):
    def __init__(self, *, label: str, path: Path) -> None:
        super().__init__(label=label)
        self.path = path


@dataclass(slots=True)
class PathSets:
    managed_dirs: set[Path] = field(default_factory=lambda: set())
    managed_files: set[Path] = field(default_factory=lambda: set())
    status_dirs: set[Path] = field(default_factory=lambda: set())
    status_files: set[Path] = field(default_factory=lambda: set())
    # derived sets
    managed_paths: set[Path] = field(default_factory=lambda: set())
    n_dirs: set[Path] = field(default_factory=lambda: set())
    status_paths: set[Path] = field(default_factory=lambda: set())
    tree_x_dirs: set[Path] = field(default_factory=lambda: set())
    x_dirs: set[Path] = field(default_factory=lambda: set())
    x_files: set[Path] = field(default_factory=lambda: set())

    def __post_init__(self) -> None:
        self.managed_paths = self.managed_dirs | self.managed_files
        self.status_paths = self.status_dirs | self.status_files
        self.x_dirs = {d for d in self.managed_dirs if d not in self.status_dirs}
        self.x_files = {f for f in self.managed_files if f not in self.status_files}
        self.n_dirs = {
            d
            for d in self.x_dirs
            if any(
                sp.is_relative_to(d)
                for sp in self.status_paths
                if d not in self.status_dirs
            )
        }
        self.tree_x_dirs = {d for d in self.x_dirs if d not in self.n_dirs}

    @property
    def no_managed_paths(self) -> bool:
        return bool(not self.managed_dirs and not self.managed_files)

    def contains_status_paths(self, dir_path: Path) -> bool:
        return any(
            p.is_relative_to(dir_path) for p in self.status_dirs | self.status_files
        )

    def status_files_in(self, dir_path: Path) -> set[Path]:
        return {p for p in self.status_files if p.parent == dir_path}

    def managed_dirs_in(self, dir_path: Path) -> set[Path]:
        return {p for p in self.managed_dirs if p.parent == dir_path}

    def n_dirs_in(self, dir_path: Path) -> set[Path]:
        return {
            p for p in self.n_dirs if p.parent == dir_path and p not in self.status_dirs
        }

    def status_dirs_in(self, dir_path: Path) -> set[Path]:
        return {p for p in self.status_dirs if p.parent == dir_path}

    def tree_x_dirs_in(self, dir_path: Path) -> set[Path]:
        return {p for p in self.tree_x_dirs if p.parent == dir_path}


@dataclass(slots=True)
class CachedCmdResults:
    cat_config: CommandResult | None = None
    doctor: CommandResult | None = None
    dump_config: CommandResult | None = None
    git_log: CommandResult | None = None
    ignored: CommandResult | None = None
    managed_dirs: CommandResult | None = None
    managed_files: CommandResult | None = None
    status_dirs: CommandResult | None = None
    status_files: CommandResult | None = None
    template_data: CommandResult | None = None
    verify: CommandResult | None = None

    @property
    def all(self) -> list[CommandResult | None]:
        return [getattr(self, f.name) for f in fields(self)]


class CachedData:
    def __init__(self) -> None:

        self.cmd_results = CachedCmdResults()

        # parsed config cache
        self.dest_dir: Path = Path().home()
        self.git_auto_commit: bool = False
        self.git_auto_push: bool = False

        # cached for frequent lookups
        self.sets: PathSets = PathSets(
            managed_dirs=set(),
            managed_files=set(),
            status_dirs=set(),
            status_files=set(),
        )

    @property
    def no_status_paths(self) -> bool:
        return (
            self.cmd_results.verify is not None
            and self.cmd_results.verify.exit_code == 0
        )

    @property
    def _dir_status_pairs(self) -> dict[Path, str]:
        if self.cmd_results.status_dirs is None:
            return {}
        return {
            Path(line[3:]): line[:2]
            for line in self.cmd_results.status_dirs.std_out.splitlines()
        }

    @property
    def _file_status_pairs(self) -> dict[Path, str]:
        if self.cmd_results.status_files is None:
            return {}
        return {
            Path(line[3:]): line[:2]
            for line in self.cmd_results.status_files.std_out.splitlines()
        }

    def _get_status_dirs(self, app_ids: AppIds) -> dict[Path, StatusCode]:
        if self.cmd_results.status_dirs is None:
            return {}
        ds_idx = 0 if app_ids.canvas_name == TabLabel.apply else 1  # dir status index
        return {
            k: StatusCode(v[ds_idx])
            for k, v in self._dir_status_pairs.items()
            if v[ds_idx] != StatusCode.Space
        }

    def _get_status_files(self, app_ids: AppIds) -> dict[Path, StatusCode]:
        if self.cmd_results.status_files is None:
            return {}
        fs_idx = 0 if app_ids.canvas_name == TabLabel.apply else 1  # file status index
        return {
            k: StatusCode(v[fs_idx])
            for k, v in self._file_status_pairs.items()
            if v[fs_idx] != StatusCode.Space
        }

    def _get_status_files_in(
        self, dir_path: Path, app_ids: AppIds, recursive: bool
    ) -> dict[Path, StatusCode]:
        # Use the parsed status file dict to ensure key formats match
        status_files = self._get_status_files(app_ids)
        results: dict[Path, StatusCode] = {}
        for path, status in status_files.items():
            if recursive:
                if path.is_relative_to(dir_path):
                    results[path] = status
            elif path.parent == dir_path:
                results[path] = status
        return results

    def _get_status_dirs_in(
        self, dir_path: Path, app_ids: AppIds, recursive: bool
    ) -> dict[Path, StatusCode]:
        status_dirs = self._get_status_dirs(app_ids)
        results: dict[Path, StatusCode] = {}
        for path, status in status_dirs.items():
            if recursive:
                if path.is_relative_to(dir_path):
                    results[path] = status
            elif path.parent == dir_path:
                results[path] = status
        return results

    def get_path_status(self, path: Path, app_ids: AppIds) -> StatusCode:
        paths_dict = self._get_status_dirs(app_ids) | self._get_status_files(app_ids)
        return paths_dict.get(path, StatusCode.Space)

    def get_dir_widgets(
        self, dir_path: Path, app_ids: AppIds
    ) -> list[Static | Label | DirContentBtn]:
        widgets: list[Static | Label | DirContentBtn] = []
        if dir_path == self.dest_dir:
            widgets.append(
                Label("Destination directory", classes=Tcss.main_section_label)
            )
        if self.sets.no_managed_paths is True:
            widgets = [
                Label(SectionLabel.paths_with_status, classes=Tcss.main_section_label)
            ]
            widgets.append(
                Static(
                    "No managed paths are in the chezmoi repository, "
                    "switch to the Add tab to add some paths.",
                    classes=Tcss.added,
                )
            )
            return widgets
        elif self.sets.no_managed_paths is False and self.no_status_paths is True:
            widgets.append(
                Label(SectionLabel.paths_with_status, classes=Tcss.main_section_label)
            )
            widgets.append(
                Static(
                    "No diffs are available because no paths have a status. Toggle "
                    "the 'Show unchanged paths' switch to view all managed paths.",
                    classes=Tcss.info,
                )
            )
            return widgets

        if self.sets.contains_status_paths(dir_path):
            status_dirs_in = self._get_status_dirs_in(
                dir_path, app_ids, recursive=True
            ).items()
            if status_dirs_in:
                widgets.append(
                    Label(
                        "Contains directories with a status",
                        classes=Tcss.sub_section_label,
                    )
                )
                for path, status in status_dirs_in:
                    widgets.append(
                        DirContentBtn(label=f"{status.color_tag}{path}[/]", path=path)
                    )
            status_files_in = self._get_status_files_in(
                dir_path, app_ids, recursive=True
            )
            if status_files_in:
                widgets.append(
                    Label(
                        "Contains files with a status", classes=Tcss.sub_section_label
                    )
                )
                for path, status in status_files_in.items():
                    widgets.append(
                        DirContentBtn(label=f"{status.color_tag}{path}[/]", path=path)
                    )
        return widgets

    def update_path_sets(self) -> None:
        def parse_managed_paths(result: CommandResult | None) -> set[Path]:
            if result is None:
                return set()
            return {Path(line) for line in result.std_out.splitlines()}

        def parse_status_paths(result: CommandResult | None) -> set[Path]:
            if result is None:
                return set()
            return {Path(line[3:]) for line in result.std_out.splitlines()}

        self.sets = PathSets(
            managed_dirs=parse_managed_paths(self.cmd_results.managed_dirs),
            managed_files=parse_managed_paths(self.cmd_results.managed_files),
            status_dirs=parse_status_paths(self.cmd_results.status_dirs),
            status_files=parse_status_paths(self.cmd_results.status_files),
        )


@dataclass(slots=True)
class Commands:
    run_cmd: ChezmoiCommand = field(default_factory=ChezmoiCommand)
    cache: CachedData = CachedData()
    loading_modal_results: list[CommandResult] = field(default_factory=lambda: [])
    refresh_read_cmds: list[ReadCmd] = field(
        default_factory=lambda: [
            ReadCmd.managed_dirs,
            ReadCmd.managed_files,
            ReadCmd.status_dirs,
            ReadCmd.status_files,
        ]
    )
    changed_paths: list[Path] = field(default_factory=lambda: [])
    added_paths: list[Path] = field(default_factory=lambda: [])
    removed_paths: list[Path] = field(default_factory=lambda: [])
    changed_status_paths: list[Path] = field(default_factory=lambda: [])


CMD = Commands()

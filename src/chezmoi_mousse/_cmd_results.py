from __future__ import annotations

import json
from dataclasses import dataclass, field, fields
from pathlib import Path
from typing import TYPE_CHECKING

from textual.widgets import Label, Static

from ._run_cmd import ChezmoiCommand
from ._str_enum_names import Tcss
from ._str_enums import StatusCode

if TYPE_CHECKING:
    from typing import Any

    from ._run_cmd import CommandResult

__all__ = ["CMD", "CommandResults", "DirNode", "ParsedJson"]


type ParsedJson = dict[str, Any]


@dataclass(slots=True)
class CommandResults:
    cat_config: CommandResult | None = None
    doctor: CommandResult | None = None
    dump_config: CommandResult | None = None
    git_log: CommandResult | None = None
    ignored: CommandResult | None = None
    managed_dirs: CommandResult | None = None
    managed_files: CommandResult | None = None
    status: CommandResult | None = None
    status_dirs: CommandResult | None = None
    status_files: CommandResult | None = None
    template_data: CommandResult | None = None
    verify: CommandResult | None = None

    @property
    def _parsed_dump_config(self) -> ParsedJson | None:
        if self.dump_config is None:
            return None
        return json.loads(self.dump_config.completed_process.stdout)

    @property
    def dest_dir(self) -> Path:
        if self._parsed_dump_config is None:
            return Path().home()
        return Path(self._parsed_dump_config["destDir"])

    @property
    def git_auto_commit(self) -> bool:
        if self._parsed_dump_config is None:
            return False
        return self._parsed_dump_config["git"]["autocommit"]

    @property
    def git_auto_push(self) -> bool:
        if self._parsed_dump_config is None:
            return False
        return self._parsed_dump_config["git"]["autopush"]

    @property
    def executed_commands(self) -> list[CommandResult]:
        return [
            getattr(self, field.name)
            for field in fields(self)
            if getattr(self, field.name) is not None
        ]

    @property
    def managed_dir_paths(self) -> list[Path]:
        if self.managed_dirs is None:
            return []
        return [Path(line) for line in self.managed_dirs.std_out.splitlines()]

    @property
    def managed_file_paths(self) -> list[Path]:
        if self.managed_files is None:
            return []
        return [Path(line) for line in self.managed_files.std_out.splitlines()]

    def _parse_status_output(
        self, index: int, dirs: bool = False
    ) -> dict[Path, StatusCode]:
        status_lines = []
        if dirs and self.status_dirs is not None:
            status_lines = self.status_dirs.std_out.splitlines()
        elif not dirs and self.status_files is not None:
            status_lines = self.status_files.std_out.splitlines()
        if not status_lines:
            return {}
        return {Path(line[3:]): StatusCode(line[index]) for line in status_lines}

    @property
    def apply_status_dirs(self) -> dict[Path, StatusCode]:
        return self._parse_status_output(0, dirs=True)

    @property
    def apply_status_files(self) -> dict[Path, StatusCode]:
        return self._parse_status_output(0, dirs=False)

    @property
    def re_add_status_dirs(self) -> dict[Path, StatusCode]:
        return self._parse_status_output(1, dirs=True)

    @property
    def re_add_status_files(self) -> dict[Path, StatusCode]:
        return self._parse_status_output(1, dirs=False)

    @property
    def status_paths(self) -> set[Path]:
        if self.status_files is None:
            return set()
        return {Path(line[3:]) for line in self.status_files.std_out.splitlines()}

    @property
    def x_dirs_with_status_children(self) -> set[Path]:
        status_children: set[Path] = set()
        for path in self.status_paths:
            current = path.parent
            while current != current.parent:
                status_children.add(current)
                current = current.parent
        return status_children

    @property
    def tree_x_dirs(self) -> list[Path]:
        return [
            d
            for d in self.managed_dir_paths
            if d not in self.x_dirs_with_status_children
        ]

    @property
    def x_files(self) -> list[Path]:
        return [
            path for path in self.managed_file_paths if path not in self.status_paths
        ]

    @property
    def no_status_paths(self) -> bool:
        return self.verify is not None and self.verify.exit_code == 0

    @property
    def global_git_log_lines(self) -> list[str]:
        if self.git_log is None or not self.git_log.std_out:
            return ["No commits;No git log entries available yet."]
        return self.git_log.std_out.splitlines()


@dataclass(slots=True)
class DirNode:
    dir_path: Path
    dir_status: StatusCode
    x_files_in: dict[Path, StatusCode]
    status_files_in: dict[Path, StatusCode]
    real_status_dirs_in: dict[Path, StatusCode]
    tree_status_dirs_in: dict[Path, StatusCode]
    nested_status_dirs: dict[Path, StatusCode]
    nested_status_files: dict[Path, StatusCode]
    tree_x_dirs_in: dict[Path, StatusCode]
    no_status_paths: bool = False

    # property to return if the dir has any nested paths with a status
    @property
    def has_status_paths(self) -> bool:
        return bool(
            self.status_files_in
            or self.real_status_dirs_in
            or self.nested_status_dirs
            or self.nested_status_files
        )

    @property
    def node_colors(self) -> dict[str, str]:
        return {
            StatusCode.Added: "[$text-success]",
            StatusCode.Deleted: "[$text-error]",
            StatusCode.Modified: "[$text-warning]",
            StatusCode.No_Change: "[$warning-darken-2]",
            StatusCode.Run: "[$error]",
            StatusCode.No_Status: "[$text-secondary]",
        }

    @property
    def dir_widgets(self) -> list[Static | Label]:
        # Populate dir_widgets for the destDir
        widgets: list[Static | Label] = []
        if self.dir_path == CMD.cache.dest_dir:
            widgets.append(
                Label("Destination directory", classes=Tcss.main_section_label)
            )
            if not CMD.cache.managed_dir_paths and not CMD.cache.managed_file_paths:
                widgets.append(
                    Static(
                        "No managed paths or paths with a status are in the chezmoi "
                        "repository. Switch to the Add tab to add paths.",
                        classes=Tcss.added,
                    )
                )
            elif self.no_status_paths is True:
                text = "No diffs are available because no paths have a status."
                widgets.append(Static(text, classes=Tcss.info))
                text = "<- Select an unchanged path."
                widgets.append(Static(text, classes=Tcss.added))
                text = (
                    "Switch to the Contents tab to view the contents of the selected "
                    "path.\n"
                    "Switch to the Git-Log tab to view the git log output for the "
                    "selected path."
                )
                widgets.append(Static(text, classes=Tcss.info))
            else:
                text = "<- Select a file or directory in the tree to view its diff."
                widgets.append(Static(text, classes=Tcss.added))
                text = "This is the destination directory, it has no diff output."
                widgets.append(Static(text, classes=Tcss.info))
        if self.real_status_dirs_in:
            widgets.append(
                Label(
                    "Contains directories with a status", classes=Tcss.sub_section_label
                )
            )
            for path, status in self.real_status_dirs_in.items():
                widgets.append(Static(f"{self.node_colors[status]}{path}[/]"))
        if self.status_files_in:
            widgets.append(
                Label("Contains files with a status", classes=Tcss.sub_section_label)
            )
            for path, status in self.status_files_in.items():
                widgets.append(Static(f"{self.node_colors[status]}{path}[/]"))
        if self.nested_status_files:
            widgets.append(
                Label(
                    "Contains nested files with a status",
                    classes=Tcss.sub_section_label,
                )
            )
            for path, status in sorted(self.nested_status_files.items()):
                widgets.append(Static(f"{self.node_colors[status]}{path}[/]"))
        return widgets


class CachedData:
    # Adding these as type-only hints will allow autocomplete and static
    # analysis to work while the values remain dynamically populated.

    # Parsed config attributes
    dest_dir: Path
    git_auto_commit: bool
    git_auto_push: bool
    # Parsed git log and verify command output attribute
    global_git_log_lines: list[str]
    no_status_paths: bool
    # Parsed paths attributes
    apply_status_dirs: dict[Path, StatusCode]
    apply_status_files: dict[Path, StatusCode]
    managed_dir_paths: list[Path]
    managed_dirs_with_dest_dir: list[Path]
    managed_file_paths: list[Path]
    re_add_status_dirs: dict[Path, StatusCode]
    re_add_status_files: dict[Path, StatusCode]
    real_x_files: list[Path]
    status_paths: set[Path]
    tree_x_dirs: list[Path]
    x_dirs_with_status_children: set[Path]
    x_files: list[Path]
    # Cached widgets
    re_add_dir_nodes: dict[Path, DirNode]
    apply_dir_nodes: dict[Path, DirNode]

    def __init__(self, source: CommandResults) -> None:
        cls = type(source)
        for name in dir(cls):
            member = getattr(cls, name)
            if isinstance(member, property):
                setattr(self, name, getattr(source, name))

        self.managed_dirs_with_dest_dir = [self.dest_dir] + self.managed_dir_paths
        self.apply_dir_nodes = {}
        self.re_add_dir_nodes = {}
        self._update_apply_and_re_add_dir_nodes()

    def update_snapshot(self, source: CommandResults) -> None:
        self.__init__(source)

    def _get_dir_node(
        self,
        dir_path: Path,
        status_files: dict[Path, StatusCode],
        status_dirs: dict[Path, StatusCode],
    ) -> DirNode:
        # x files are the same for apply and re_add contexts
        x_files_in = {
            path: StatusCode.No_Status
            for path in self.managed_file_paths
            if path.parent == dir_path and path not in self.status_paths
        }
        # sub dir paths are the same for apply and re_add contexts
        sub_dir_paths = [
            p for p in self.managed_dirs_with_dest_dir if p.parent == dir_path
        ]
        tree_status_dirs_in: dict[Path, StatusCode] = {}
        tree_x_dirs_in: dict[Path, StatusCode] = {}
        for sub_dir in sub_dir_paths:
            if sub_dir in status_dirs or sub_dir in self.x_dirs_with_status_children:
                tree_status_dirs_in[sub_dir] = status_dirs.get(
                    sub_dir, StatusCode.No_Status
                )
            else:
                tree_x_dirs_in[sub_dir] = StatusCode.No_Status

        return DirNode(
            dir_path=dir_path,
            dir_status=status_dirs.get(dir_path, StatusCode.No_Status),
            status_files_in={
                p: s for p, s in status_files.items() if p.parent == dir_path
            },
            x_files_in=x_files_in,
            real_status_dirs_in={
                p: s for p, s in status_dirs.items() if p.parent == dir_path
            },
            tree_status_dirs_in=dict(sorted(tree_status_dirs_in.items())),
            tree_x_dirs_in=dict(sorted(tree_x_dirs_in.items())),
            nested_status_dirs={
                p: s
                for p, s in status_dirs.items()
                if p.is_relative_to(dir_path) and len(p.relative_to(dir_path).parts) > 1
            },
            nested_status_files={
                p: s
                for p, s in status_files.items()
                if p.is_relative_to(dir_path) and len(p.relative_to(dir_path).parts) > 1
            },
        )

    def _update_apply_and_re_add_dir_nodes(self) -> None:
        for dir_path in self.managed_dirs_with_dest_dir:

            self.apply_dir_nodes[dir_path] = self._get_dir_node(
                dir_path, self.apply_status_files, self.apply_status_dirs
            )
            self.re_add_dir_nodes[dir_path] = self._get_dir_node(
                dir_path, self.re_add_status_files, self.re_add_status_dirs
            )


@dataclass(slots=True)
class Commands:
    cmd_results: CommandResults = field(default_factory=CommandResults)
    run_cmd: ChezmoiCommand = field(default_factory=ChezmoiCommand)
    cache: CachedData = field(init=False)

    def __post_init__(self) -> None:
        self.cache = CachedData(self.cmd_results)

    # Properties for easy access to fields

    def update_parsed_data(self) -> None:
        self.cache.update_snapshot(self.cmd_results)


CMD = Commands()

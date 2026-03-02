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
    status_dirs: CommandResult | None = None
    status_files: CommandResult | None = None
    template_data: CommandResult | None = None
    verify: CommandResult | None = None

    @property
    def executed_commands(self) -> list[CommandResult]:
        return [
            getattr(self, field.name)
            for field in fields(self)
            if getattr(self, field.name) is not None
        ]


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
    dir_widgets: list[Static | Label] = field(default_factory=list[Static | Label])

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

    def __post_init__(self) -> None:
        # Populate dir_widgets for the destDir
        widgets: list[Static | Label] = []
        if self.dir_path == CMD.dest_dir:
            widgets.append(
                Label("Destination directory", classes=Tcss.main_section_label)
            )
            if not CMD.managed_dirs and not CMD.managed_files:
                widgets.append(
                    Static(
                        "No managed paths or paths with a status are in the chezmoi "
                        "repository. Switch to the Add tab to add paths.",
                        classes=Tcss.added,
                    )
                )
            elif CMD.no_status_paths is True:
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
        self.dir_widgets = widgets


@dataclass(slots=True)
class ParsedConfig:
    dest_dir: Path = Path.home()
    git_auto_commit: bool = False
    git_auto_push: bool = False


@dataclass(slots=True)
class ParsedPaths:
    managed_dirs: list[Path] = field(default_factory=list[Path])
    managed_files: list[Path] = field(default_factory=list[Path])
    x_dirs_with_status_children: set[Path] = field(default_factory=lambda: set())
    tree_x_dirs: list[Path] = field(default_factory=lambda: [])
    real_x_files: list[Path] = field(default_factory=lambda: [])
    apply_status_dirs: dict[Path, StatusCode] = field(
        default_factory=dict[Path, StatusCode]
    )
    apply_status_files: dict[Path, StatusCode] = field(
        default_factory=dict[Path, StatusCode]
    )
    re_add_status_dirs: dict[Path, StatusCode] = field(
        default_factory=dict[Path, StatusCode]
    )
    re_add_status_files: dict[Path, StatusCode] = field(
        default_factory=dict[Path, StatusCode]
    )


@dataclass(slots=True)
class Commands:
    _parsed_config: ParsedConfig = field(default_factory=ParsedConfig)
    _parsed_paths: ParsedPaths = field(default_factory=ParsedPaths)
    _status_paths: set[Path] = field(default_factory=lambda: set())
    apply_dir_nodes: dict[Path, DirNode] = field(default_factory=dict[Path, DirNode])
    cmd_results: CommandResults = field(default_factory=CommandResults)
    no_status_paths: bool = False
    re_add_dir_nodes: dict[Path, DirNode] = field(default_factory=dict[Path, DirNode])
    run_cmd: ChezmoiCommand = field(default_factory=ChezmoiCommand)

    def __post_init__(self) -> None:
        self.cmd_results = CommandResults()
        self.run_cmd = ChezmoiCommand()

    # Properties for easy access to fields

    @property
    def dest_dir(self) -> Path:
        return self._parsed_config.dest_dir

    @property
    def git_auto_commit(self) -> bool:
        return self._parsed_config.git_auto_commit

    @property
    def git_auto_push(self) -> bool:
        return self._parsed_config.git_auto_push

    @property
    def global_git_log_lines(self) -> list[str]:
        if self.cmd_results.git_log is None or not self.cmd_results.git_log.std_out:
            return ["No commits;No git log entries available yet."]
        return self.cmd_results.git_log.std_out.splitlines()

    @property
    def managed_dirs(self) -> list[Path]:
        return self._parsed_paths.managed_dirs

    @property
    def managed_files(self) -> list[Path]:
        return self._parsed_paths.managed_files

    @property
    def status_paths(self) -> set[Path]:
        return self._status_paths

    @property
    def tree_x_dirs(self) -> list[Path]:
        return self._parsed_paths.tree_x_dirs

    @property
    def x_files(self) -> list[Path]:
        return self._parsed_paths.real_x_files

    def update_parsed_data(self) -> None:
        self._update_dump_config()
        self._update_no_status_paths()
        self._update_managed_dirs_and_files()
        self._update_apply_and_re_add_status_dirs_and_files_and_status_paths()
        # Now update x files as they depend status paths and managed dirs/files
        self._update_real_x_files()
        # Now update dirs with and without status children as they also depend on
        # status paths and managed dirs/files
        self._update_dirs_with_and_dirs_without_status_children()
        # Now update dir nodes as they depend on all of the above
        self._update_apply_and_re_add_dir_nodes()

    def _update_dump_config(self) -> None:
        if self.cmd_results.dump_config is None:
            return
        parsed_config = json.loads(
            self.cmd_results.dump_config.completed_process.stdout
        )
        self._parsed_config = ParsedConfig(
            dest_dir=Path(parsed_config["destDir"]),
            git_auto_commit=parsed_config["git"]["autocommit"],
            git_auto_push=parsed_config["git"]["autopush"],
        )

    def _update_no_status_paths(self) -> None:
        if (
            self.cmd_results.verify is not None
            and self.cmd_results.verify.exit_code == 0
        ):
            self.no_status_paths = True

    def _update_managed_dirs_and_files(self) -> None:
        if (
            self.cmd_results.managed_dirs is None
            or self.cmd_results.managed_files is None
        ):
            raise ValueError(
                "One of the required CommandResults is None. Cannot update."
            )
        self._parsed_paths.managed_dirs = [self._parsed_config.dest_dir] + [
            Path(line) for line in self.cmd_results.managed_dirs.std_out.splitlines()
        ]
        self._parsed_paths.managed_files = [
            Path(line) for line in self.cmd_results.managed_files.std_out.splitlines()
        ]

    def _update_apply_and_re_add_status_dirs_and_files_and_status_paths(self) -> None:
        def parse_status_output(
            status_lines: list[str], index: int
        ) -> dict[Path, StatusCode]:
            return {Path(line[3:]): StatusCode(line[index]) for line in status_lines}

        if (
            self.cmd_results.status_dirs is None
            or self.cmd_results.status_files is None
        ):
            raise ValueError(
                "One of the required CommandResults is None. Cannot update."
            )

        status_dir_lines = self.cmd_results.status_dirs.std_out.splitlines()
        status_file_lines = self.cmd_results.status_files.std_out.splitlines()

        # Update status paths
        self._status_paths = {
            Path(line[3:]) for line in status_dir_lines + status_file_lines
        }

        # Update apply status dirs and files
        self._parsed_paths.apply_status_dirs = parse_status_output(status_dir_lines, 0)
        self._parsed_paths.apply_status_files = parse_status_output(
            status_file_lines, 0
        )

        # Update re-add status dirs and files
        self._parsed_paths.re_add_status_dirs = parse_status_output(status_dir_lines, 1)
        self._parsed_paths.re_add_status_files = parse_status_output(
            status_file_lines, 1
        )

    def _update_real_x_files(self) -> None:
        self._parsed_paths.real_x_files = [
            path
            for path in self._parsed_paths.managed_files
            if path not in self._status_paths
        ]

    def _update_dirs_with_and_dirs_without_status_children(self) -> None:
        # Update dirs with status children for tree population logic
        self._parsed_paths.x_dirs_with_status_children = set()
        for path in self._status_paths:
            current = path.parent
            while current != current.parent:
                self._parsed_paths.x_dirs_with_status_children.add(current)
                current = current.parent
        # Update dirs without status children for tree population logic
        self._parsed_paths.tree_x_dirs = [
            d
            for d in self._parsed_paths.managed_dirs
            if d not in self._parsed_paths.x_dirs_with_status_children
        ]

    def _update_apply_and_re_add_dir_nodes(self) -> None:

        def get_dir_node(
            dir_path: Path,
            sub_dir_paths: list[Path],
            status_files: dict[Path, StatusCode],
            status_dirs: dict[Path, StatusCode],
        ) -> DirNode:
            # x files are the same for apply and re_add contexts
            x_files_in = {
                path: StatusCode.No_Status
                for path in self._parsed_paths.managed_files
                if path.parent == dir_path and path not in self._status_paths
            }

            tree_status_dirs_in: dict[Path, StatusCode] = {}
            tree_x_dirs_in: dict[Path, StatusCode] = {}
            for sub_dir in sub_dir_paths:
                if sub_dir in status_dirs:
                    tree_status_dirs_in[sub_dir] = status_dirs[sub_dir]
                elif sub_dir in self._parsed_paths.x_dirs_with_status_children:
                    tree_status_dirs_in[sub_dir] = StatusCode.No_Status
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
                    if p.is_relative_to(dir_path)
                    and len(p.relative_to(dir_path).parts) > 1
                },
                nested_status_files={
                    p: s
                    for p, s in status_files.items()
                    if p.is_relative_to(dir_path)
                    and len(p.relative_to(dir_path).parts) > 1
                },
                dir_widgets=[],
            )

        for dir_path in self._parsed_paths.managed_dirs:
            sub_dir_paths = [
                p for p in self._parsed_paths.managed_dirs if p.parent == dir_path
            ]
            self.apply_dir_nodes[dir_path] = get_dir_node(
                dir_path,
                sub_dir_paths,
                self._parsed_paths.apply_status_files,
                self._parsed_paths.apply_status_dirs,
            )
            self.re_add_dir_nodes[dir_path] = get_dir_node(
                dir_path,
                sub_dir_paths,
                self._parsed_paths.re_add_status_files,
                self._parsed_paths.re_add_status_dirs,
            )


CMD = Commands()

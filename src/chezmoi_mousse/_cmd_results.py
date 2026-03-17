from __future__ import annotations

import copy
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar

from textual.widgets import Label, Static

from ._run_cmd import ChezmoiCommand
from ._str_enum_names import Tcss
from ._str_enums import StatusCode

if TYPE_CHECKING:
    from typing import Any

    from ._run_cmd import CommandResult

__all__ = ["CMD", "CachedData", "DirNode", "ParsedJson"]


type ParsedJson = dict[str, Any]


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

    # property to return if the dir has any nested paths with a status
    @property
    def _has_status_paths(self) -> bool:
        return bool(
            self.status_files_in
            or self.real_status_dirs_in
            or self.nested_status_dirs
            or self.nested_status_files
        )

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
            elif self._has_status_paths is True:
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
                widgets.append(Static(f"{status.color}{path}[/]"))
        if self.status_files_in:
            widgets.append(
                Label("Contains files with a status", classes=Tcss.sub_section_label)
            )
            for path, status in self.status_files_in.items():
                widgets.append(Static(f"{status.color}{path}[/]"))
        if self.nested_status_files:
            widgets.append(
                Label(
                    "Contains nested files with a status",
                    classes=Tcss.sub_section_label,
                )
            )
            for path, status in sorted(self.nested_status_files.items()):
                widgets.append(Static(f"{status.color}{path}[/]"))
        return widgets


class CachedData:
    cat_config: ClassVar[CommandResult | None] = None
    doctor: ClassVar[CommandResult | None] = None
    dump_config: ClassVar[CommandResult | None] = None
    git_log: ClassVar[CommandResult | None] = None
    ignored: ClassVar[CommandResult | None] = None
    managed: ClassVar[CommandResult | None] = None
    managed_dirs: ClassVar[CommandResult | None] = None
    managed_files: ClassVar[CommandResult | None] = None
    status: ClassVar[CommandResult | None] = None
    status_dirs: ClassVar[CommandResult | None] = None
    status_files: ClassVar[CommandResult | None] = None
    template_data: ClassVar[CommandResult | None] = None
    verify: ClassVar[CommandResult | None] = None
    re_add_dir_nodes: ClassVar[dict[Path, DirNode]] = {}
    apply_dir_nodes: ClassVar[dict[Path, DirNode]] = {}

    def __init__(self) -> None:
        _parsed_dump_cfg: ParsedJson = self._get_parsed_dump_config()
        self.dest_dir = _parsed_dump_cfg.get("destDir", Path().home())
        self.git_auto_commit = _parsed_dump_cfg.get("git", {}).get("autocommit", False)
        self.git_auto_push = _parsed_dump_cfg.get("git", {}).get("autopush", False)

    #####################################################
    # Properties derived from the above command results #
    #####################################################

    def _get_parsed_dump_config(self) -> ParsedJson:
        if self.dump_config is None:
            return {}
        try:
            json.loads(self.dump_config.std_out)
        except Exception:
            return {}
        return {}

    @property
    def global_git_log_lines(self) -> list[str]:
        if self.git_log is None or not self.git_log.std_out:
            return ["No commits;No git log entries available yet."]
        return self.git_log.std_out.splitlines()

    @property
    def managed_paths(self) -> set[Path]:
        if self.managed is None:
            return set()
        return {Path(line) for line in self.managed.std_out.splitlines()}

    @property
    def managed_dir_paths(self) -> list[Path]:
        if self.managed_dirs is None:
            return []
        return [Path(line) for line in self.managed_dirs.std_out.splitlines()]

    @property
    def managed_dirs_with_dest_dir(self) -> list[Path]:
        return [self.dest_dir] + self.managed_dir_paths

    @property
    def managed_file_paths(self) -> list[Path]:
        if self.managed_files is None:
            return []
        return [Path(line) for line in self.managed_files.std_out.splitlines()]

    ########################################################
    # Derived properties depending on the properties above #
    ########################################################

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
    def status_pairs(self) -> dict[Path, str]:
        if self.status is None:
            return {}
        return {
            Path(line[3:]): line[:2] for line in list(self.status.std_out.splitlines())
        }

    @property
    def status_paths(self) -> set[Path]:
        if self.status is None:
            return set()
        return {Path(line[3:]) for line in self.status.std_out.splitlines()}

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

    def update_apply_and_re_add_dir_nodes(self) -> None:
        for dir_path in self.managed_dirs_with_dest_dir:

            self.apply_dir_nodes[dir_path] = self._get_dir_node(
                dir_path, self.apply_status_files, self.apply_status_dirs
            )
            self.re_add_dir_nodes[dir_path] = self._get_dir_node(
                dir_path, self.re_add_status_files, self.re_add_status_dirs
            )


@dataclass(slots=True)
class Commands:
    run_cmd: ChezmoiCommand = field(default_factory=ChezmoiCommand)
    cache: CachedData = CachedData()
    changed_paths: list[Path] = field(default_factory=lambda: [])

    # Properties for easy access to fields

    def update_parsed_data(self) -> None:
        self.changed_paths.clear()
        old_cached = copy.deepcopy(self.cache)
        self.cache.update_apply_and_re_add_dir_nodes()

        # ^ symmetric difference: elements that exist in either set, but not in both
        # & intersection: elements that exist in both sets
        # | union: all elements that exist in either set

        # Collect changed paths: Symmetric difference (added/removed) + Status changes
        changed_paths = (old_cached.managed_paths ^ set(self.cache.managed_paths)) | {
            p
            for p in old_cached.managed_paths & set(self.cache.managed_paths)
            if old_cached.status_pairs.get(p) != self.cache.status_pairs.get(p)
        }
        self.changed_paths = sorted(changed_paths)


CMD = Commands()

from __future__ import annotations

from itertools import groupby
from typing import TYPE_CHECKING

from textual import getters
from textual.app import ComposeResult
from textual.containers import ScrollableContainer
from textual.reactive import reactive
from textual.widgets import Label, Static

from chezmoi_mousse.functions import Commands
from chezmoi_mousse.named_tuples import CommandResult
from chezmoi_mousse.str_enums import (
    InfoStaticString,
    ReadCmd,
    SectionLabel,
    TabLabel,
    Tcss,
)

from .components import (
    DiffLinesContainer,
    FlatSectionLabel,
    InfoStatic,
    MainSectionLabel,
    SubSectionLabel,
)
from .messages import LogCmdResultMsg

if TYPE_CHECKING:
    from pathlib import Path

    from chezmoi_mousse.app_ids import AppIds
    from chezmoi_mousse.gui.textual_app import ChezmoiGui
    from chezmoi_mousse.named_tuples import ManagedTreePaths

__all__ = ["DiffView"]

DIFF_TCSS = {
    " ": Tcss.context,
    "@@": Tcss.context,
    "index": Tcss.context,
    "-": Tcss.removed,
    "deleted": Tcss.removed,
    "old": Tcss.removed,
    "+": Tcss.added,
    "new": Tcss.added,
    "changed": Tcss.changed,
    "unhandled": Tcss.unhandled,
}


class DiffView(ScrollableContainer):
    if TYPE_CHECKING:
        app = getters.app(ChezmoiGui)

    show_path: reactive[Path | None] = reactive(None, init=False)

    def __init__(self, ids: AppIds) -> None:
        self.app_ids = ids
        self.diff_cmd = (
            ReadCmd.diff
            if self.app_ids.tab_label == TabLabel.apply
            else ReadCmd.diff_reverse
        )
        super().__init__(id=ids.container.diff)

    def compose(self) -> ComposeResult:
        yield MainSectionLabel()
        yield SubSectionLabel()
        yield InfoStatic()
        yield DiffLinesContainer()
        yield FlatSectionLabel()

    def on_mount(self) -> None:
        self.info_static = self.query_exactly_one(InfoStatic)
        self.main_section_label = self.query_exactly_one(MainSectionLabel)
        self.sub_section_label = self.query_exactly_one(SubSectionLabel)

        self.flat_section_label = self.query_exactly_one(FlatSectionLabel)
        self.flat_section_label.display = False
        self.diff_lines = self.query_exactly_one(DiffLinesContainer)
        self.diff_lines.display = False

        self._update_widgets(self.paths.dest_dir)

    @property
    def paths(self) -> ManagedTreePaths:
        return (
            self.app.cmattr.paths.apply_tree_paths
            if self.app_ids.tab_label == TabLabel.apply
            else self.app.cmattr.paths.re_add_tree_paths
        )

    def _update_widgets(self, path: Path) -> None:

        if path in self.paths.status_paths_set:
            diff_result = Commands.run_chezmoi_diff(self.diff_cmd, path)
            self.post_message(LogCmdResultMsg([diff_result]))

            self.main_section_label.update(str(diff_result.full_cmd))

            self.diff_lines.remove_children()
            self.diff_lines.mount_all(self._create_diff_widgets(diff_result))
            self.flat_section_label.update(diff_result.std_out.splitlines().pop(0))

            self.diff_lines.display = True
            self.flat_section_label.display = True
            self.sub_section_label.display = False
            self.info_static.display = False
            return

        if path == self.paths.dest_dir:
            self.main_section_label.update(SectionLabel.dest_dir)
            if self.app.cmattr.paths.no_managed_paths:
                self.sub_section_label.update(SectionLabel.no_managed_paths)
            else:
                self.sub_section_label.update(SectionLabel.dest_dir_diff)
            self.info_static.update(InfoStaticString.click_path_with_status)

        elif path in self.app.cmattr.paths.managed_paths_set:
            if path in self.paths.managed_dirs:
                self.main_section_label.update(SectionLabel.managed_dir)
            elif path in self.paths.managed_files:
                self.main_section_label.update(SectionLabel.managed_file)
            self.sub_section_label.update(SectionLabel.managed_no_status)
            self.info_static.update(InfoStaticString.click_path_with_status)

        elif path in self.paths.n_dirs:
            self.main_section_label.update(SectionLabel.managed_dir)
            self.sub_section_label.update(SectionLabel.n_dir)
            self.info_static.update(InfoStaticString.click_path_with_status)

        else:
            if path.is_dir():
                self.main_section_label.update(SectionLabel.unmanaged_dir)
            elif path.is_file():
                self.main_section_label.update(SectionLabel.unmanaged_file)
            self.sub_section_label.update(str(path))
            self.info_static.update(InfoStaticString.click_path_with_status)

        self.diff_lines.display = False
        self.flat_section_label.display = False
        self.sub_section_label.display = True
        self.info_static.display = True

    def _create_diff_widgets(self, diff_result: CommandResult) -> list[Static]:
        widgets: list[Label | Static] = []

        def get_prefix(line: str) -> str:
            for p in DIFF_TCSS:
                if line.startswith(p):
                    return p
            return "unhandled"

        for prefix, group_lines in groupby(
            diff_result.std_out.splitlines(), key=get_prefix
        ):
            group_list = list(group_lines)
            if prefix in ("+", "-"):
                text = "\n".join(group_list)
                widgets.append(
                    Static(text, classes=DIFF_TCSS[prefix].value, markup=False)
                )
            else:
                for line in group_list:
                    widgets.append(
                        Static(line, classes=DIFF_TCSS[prefix].value, markup=False)
                    )
        return widgets

    def watch_show_path(self, show_path: Path | None) -> None:
        if show_path is None:
            return
        self._update_widgets(show_path)

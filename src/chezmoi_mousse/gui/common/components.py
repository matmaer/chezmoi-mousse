from __future__ import annotations

from typing import TYPE_CHECKING

from textual import work
from textual.containers import (
    HorizontalGroup,
    ScrollableContainer,
    VerticalGroup,
)
from textual.reactive import reactive
from textual.widgets import Collapsible, Label, Static

from chezmoi_mousse.data_types import OperateViewData
from chezmoi_mousse.str_enums import (
    Chars,
    ColorVar,
    LabelStr,
    LogStr,
    Tcss,
)

if TYPE_CHECKING:
    from pathlib import Path

    from textual.app import ComposeResult

    from chezmoi_mousse.data_types import CommandResult, NodeData
__all__ = [
    "CmdResultCollapsible",
    "FlatSectionLabel",
    "MainSectionLabel",
    "PathInfo",
    "SubSectionLabel",
]


class CmdResultCollapsible(Collapsible):
    def __init__(self, *, cmd_result: CommandResult) -> None:
        collapsible_contents = self._collapsible_contents(cmd_result)
        super().__init__(
            *collapsible_contents,
            title=self._colored_with_timestamp(
                cmd_result.pretty_cmd,
                cmd_result.returncode,
                time_stamp=cmd_result.time_stamp,
            ),
            collapsed_symbol=Chars.right_triangle,
            expanded_symbol=Chars.down_triangle,
        )

    def _colored_with_timestamp(
        self, cmd_str: str, code: int | None, time_stamp: str
    ) -> str:
        if code is None:
            color = f"${ColorVar.text_error}"
        else:
            color = (
                f"${ColorVar.text_success}"
                if code == 0
                else f"${ColorVar.text_warning}"
            )
        return f"[{time_stamp}] [{color}]{cmd_str}[/] (returncode {code})"

    def _collapsible_contents(self, result: CommandResult) -> list[Label | Static]:
        curated_std_out = result.std_out or f"{LogStr.no_stdout}"
        curated_std_err = result.std_err or f"{LogStr.no_stderr}"
        contents: list[Label | Static] = []
        contents.extend([Label(result.full_cmd, classes=Tcss.full_cmd)])
        contents.extend(
            [
                SubSectionLabel(LabelStr.stdout_output),
                Static(f"{curated_std_out}", markup=False, classes=Tcss.cmd_output),
            ]
        )
        contents.extend(
            [
                SubSectionLabel(LabelStr.stderr_output),
                Static(f"{curated_std_err}", markup=False, classes=Tcss.cmd_output),
            ]
        )
        return contents


class MainSectionLabel(Label): ...


class SubSectionLabel(Label): ...


class FlatSectionLabel(Label): ...


class PathInfo(ScrollableContainer):
    node_data: reactive[NodeData | None] = reactive(None, init=False)

    class TrueLabel(Label):
        def on_mount(self) -> None:
            self.update("yes")

    class FalseLabel(Label):
        def on_mount(self) -> None:
            self.update(" no")

    class DirInfo(VerticalGroup): ...

    class FileInfo(VerticalGroup): ...

    class InfoLabel(Label): ...

    def compose(self) -> ComposeResult:
        yield self.DirInfo()
        yield self.FileInfo()

    def on_mount(self) -> None:
        self.cache: dict[Path, list[HorizontalGroup]] = {}
        self.paths = OperateViewData()
        self.dir_info = self.query_exactly_one(PathInfo.DirInfo)
        self.file_info = self.query_exactly_one(PathInfo.FileInfo)

    @work
    async def _set_dir_info(self, node_data: NodeData) -> None:

        if node_data.path in self.cache:
            widgets = self.cache[node_data.path]
        else:
            is_managed_label = (
                self.TrueLabel() if node_data.managed else self.FalseLabel()
            )
            has_status_label = (
                self.TrueLabel() if node_data.has_status else self.FalseLabel()
            )
            has_nested_status_label = (
                self.TrueLabel() if node_data.has_nested_status else self.FalseLabel()
            )
            has_nested_managed_label = (
                self.TrueLabel() if node_data.has_nested_managed else self.FalseLabel()
            )
            unwanted_label = (
                self.TrueLabel() if node_data.un_wanted_dir else self.FalseLabel()
            )
            exists = self.TrueLabel() if node_data.exists else self.FalseLabel()
            widgets = [
                HorizontalGroup(
                    self.InfoLabel(LabelStr.d_is_managed), is_managed_label
                ),
                HorizontalGroup(
                    self.InfoLabel(LabelStr.d_has_status), has_status_label
                ),
                HorizontalGroup(
                    self.InfoLabel(LabelStr.d_has_nested_status),
                    has_nested_status_label,
                ),
                HorizontalGroup(
                    self.InfoLabel(LabelStr.d_has_nested_managed),
                    has_nested_managed_label,
                ),
                HorizontalGroup(self.InfoLabel(LabelStr.d_un_wanted), unwanted_label),
                HorizontalGroup(self.InfoLabel(LabelStr.d_exists), exists),
            ]
        self.cache[node_data.path] = widgets
        self.dir_info.remove_children()
        self.dir_info.mount_all(self.cache[node_data.path])

    @work
    async def _set_file_info(self, node_data: NodeData) -> None:
        if node_data.path in self.cache:
            widgets = self.cache[node_data.path]
        else:
            is_managed_label = (
                self.TrueLabel() if node_data.managed else self.FalseLabel()
            )
            has_status_label = (
                self.TrueLabel() if node_data.has_status else self.FalseLabel()
            )
            un_wanted_label = (
                self.TrueLabel() if node_data.un_wanted_file else self.FalseLabel()
            )
            widgets = [
                HorizontalGroup(
                    self.InfoLabel(LabelStr.f_is_managed), is_managed_label
                ),
                HorizontalGroup(
                    self.InfoLabel(LabelStr.f_has_status), has_status_label
                ),
                HorizontalGroup(self.InfoLabel(LabelStr.f_un_wanted), un_wanted_label),
                HorizontalGroup(
                    self.InfoLabel(LabelStr.f_exists),
                    self.TrueLabel() if node_data.exists else self.FalseLabel(),
                ),
            ]
        self.cache[node_data.path] = widgets
        self.file_info.remove_children()
        self.file_info.mount_all(self.cache[node_data.path])

    def watch_node_data(self, node_data: NodeData) -> None:
        if node_data.dir_path or node_data.path.is_dir():
            self.file_info.display = False
            self._set_dir_info(node_data)
            self.dir_info.display = True
        else:
            self.dir_info.display = False
            self._set_file_info(node_data)
            self.file_info.display = True

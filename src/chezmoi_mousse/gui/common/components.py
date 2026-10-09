from __future__ import annotations

from typing import TYPE_CHECKING

from rich.markup import escape
from textual.containers import (
    HorizontalGroup,
    ScrollableContainer,
    VerticalGroup,
)
from textual.reactive import reactive
from textual.widgets import Collapsible, Label, Static

from chezmoi_mousse import path_funcs
from chezmoi_mousse.str_enums import (
    Chars,
    ColorVar,
    LabelStr,
    LogStr,
    Tcss,
)

if TYPE_CHECKING:
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
        return f"[{time_stamp}] [{color}]{escape(cmd_str)}[/] (returncode {code})"

    def _collapsible_contents(self, result: CommandResult) -> list[Label | Static]:
        curated_std_out = result.std_out or f"{LogStr.no_stdout}"
        curated_std_err = result.std_err or f"{LogStr.no_stderr}"
        contents: list[Label | Static] = []
        contents.extend([Label(escape(result.full_cmd), classes=Tcss.full_cmd)])
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


class TrueLabel(Label):
    def on_mount(self) -> None:
        self.update("yes")


class FalseLabel(Label):
    def on_mount(self) -> None:
        self.update(" no")


class InfoLabel(Label): ...


class InfoWidgets(VerticalGroup): ...


class PathInfo(ScrollableContainer):
    node_data: reactive[NodeData | None] = reactive(None, init=False)

    def compose(self) -> ComposeResult:
        yield InfoWidgets()
        yield SubSectionLabel()

    def on_mount(self) -> None:
        self.path_label = self.query_exactly_one(SubSectionLabel)
        self.info_widgets = self.query_exactly_one(InfoWidgets)

    def _set_path_info(self, node_data: NodeData) -> None:
        status = TrueLabel() if node_data.has_status else FalseLabel()
        exists = TrueLabel() if node_data.exists else FalseLabel()
        un_wanted = (
            FalseLabel() if node_data.wanted or node_data.managed else TrueLabel()
        )
        widgets = [
            HorizontalGroup(InfoLabel(LabelStr.path_has_status), status),
            HorizontalGroup(InfoLabel(LabelStr.path_exists), exists),
            HorizontalGroup(InfoLabel(LabelStr.path_un_wanted), un_wanted),
        ]
        if node_data.dir_path or node_data.path.is_dir():
            nested_status = TrueLabel() if node_data.nested_status else FalseLabel()
            nested_managed = TrueLabel() if node_data.nested_managed else FalseLabel()
            nested_un_man = TrueLabel() if node_data.nested_un_managed else FalseLabel()
            dir_info = [
                HorizontalGroup(InfoLabel(LabelStr.has_nested_status), nested_status),
                HorizontalGroup(InfoLabel(LabelStr.has_nested_managed), nested_managed),
                HorizontalGroup(InfoLabel(LabelStr.has_nested_un_man), nested_un_man),
            ]
            widgets.extend(dir_info)

        self.info_widgets.remove_children()
        self.info_widgets.mount_all(widgets)

    def watch_node_data(self, node_data: NodeData) -> None:
        self._set_path_info(node_data)
        if node_data.source_path is None:
            self.path_label.update(str(node_data.path))
        else:
            rel_path = path_funcs.get_rel_path_str(node_data.source_path)
            self.path_label.update(f"Source path: {rel_path}")

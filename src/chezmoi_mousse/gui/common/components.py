from __future__ import annotations

from typing import TYPE_CHECKING

from rich.markup import escape
from textual.widgets import Collapsible, Label, Static

from chezmoi_mousse.str_enums import Chars, ColorVar, LabelStr, LogStr, Tcss

if TYPE_CHECKING:
    from chezmoi_mousse.data_types import CommandResult
__all__ = [
    "CmdResultCollapsible",
    "FlatSectionLabel",
    "InfoLabel",
    "MainSectionLabel",
    "NoShowLabel",
    "SubSectionLabel",
    "TruthLabel",
    "WarningLabel",
]


class CmdResultCollapsible(Collapsible):
    def __init__(self, *, cmd_result: CommandResult) -> None:
        super().__init__(
            *self._collapsible_contents(cmd_result),
            title=self._colored_with_timestamp(
                cmd_result.pretty_cmd,
                cmd_result.returncode,
                time_stamp=cmd_result.time_stamp,
                interactive_approved=cmd_result.interactive_approved,
            ),
            collapsed_symbol=Chars.right_triangle,
            expanded_symbol=Chars.down_triangle,
        )

    def _colored_with_timestamp(
        self,
        cmd_str: str,
        code: int | None,
        time_stamp: str,
        interactive_approved: bool | None,
    ) -> str:
        if code is None:
            color = f"${ColorVar.text_error}"
        else:
            color = (
                f"${ColorVar.text_success}"
                if code == 0
                else f"${ColorVar.text_warning}"
            )
        suffix = (
            "(no operations approved)"
            if interactive_approved is False
            else f"(returncode {code})"
        )
        return f"[{time_stamp}] [{color}]{escape(cmd_str)}[/] {suffix}"

    def _collapsible_contents(self, result: CommandResult) -> list[Label | Static]:
        curated_std_out = result.std_out or f"{LogStr.no_stdout}"
        curated_std_err = result.std_err or f"{LogStr.no_stderr}"
        contents: list[Label | Static] = [FlatSectionLabel(escape(result.full_cmd))]
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


class FlatSectionLabel(Label): ...


class InfoLabel(Label): ...


class MainSectionLabel(Label): ...


class NoShowLabel(FlatSectionLabel): ...


class SubSectionLabel(Label): ...


class TruthLabel(Label):
    def __init__(self, truth: bool) -> None:
        label_text = "yes" if truth else "no"
        classes = Tcss.true_label if truth else Tcss.false_label
        super().__init__(label_text, classes=classes)


class WarningLabel(Label): ...

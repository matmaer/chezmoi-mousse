from __future__ import annotations

from typing import TYPE_CHECKING

from textual.widgets import Collapsible, Label, Static

from chezmoi_mousse.str_enums import Chars, ColorVar, LabelStr, LogStr, Tcss

if TYPE_CHECKING:
    from chezmoi_mousse.named_tuples import CommandResult

__all__ = [
    "CmdResultCollapsible",
    "FlatSectionLabel",
    "MainSectionLabel",
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

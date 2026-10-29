from __future__ import annotations

from itertools import groupby
from typing import TYPE_CHECKING

from rich.markup import escape
from textual.containers import HorizontalGroup
from textual.widgets import Collapsible, Label, Static

from chezmoi_mousse.gui.common.components import (
    FlatSectionLabel,
    InfoLabel,
    SubSectionLabel,
)
from chezmoi_mousse.str_enums import Chars, ColorVar, LabelStr, LogStr, Tcss

if TYPE_CHECKING:
    from chezmoi_mousse.data_types import CommandResult

_DIFF_TCSS_MAP: dict[str, Tcss] = {
    "diff --git a/": Tcss.command,
    " ": Tcss.context,
    "-": Tcss.removed,
    "deleted": Tcss.removed,
    "old mode ": Tcss.removed,
    "+": Tcss.added,
    "new mode ": Tcss.added,
    "new file mode ": Tcss.added,
}


def cmd_result_collapsible(cmd_result: CommandResult) -> Collapsible:
    rc = cmd_result.returncode
    appr = cmd_result.interactive_approved
    color = f"${ColorVar.text_success}" if rc == 0 else f"${ColorVar.text_warning}"
    suffix = "(no operations approved)" if appr is False else f"(returncode {rc})"
    ts = cmd_result.time_stamp
    title = f"[{ts}] [{color}]{escape(cmd_result.pretty_cmd)}[/]{suffix}"
    curated_stdout = cmd_result.std_out or f"{LogStr.no_stdout}"
    curated_stderr = cmd_result.std_err or f"{LogStr.no_stderr}"
    contents: list[Label | Static] = [FlatSectionLabel(escape(cmd_result.full_cmd))]
    contents.append(SubSectionLabel(LabelStr.stdout_output))
    contents.append(Static(f"{curated_stdout}", markup=False, classes=Tcss.cmd_output))
    contents.append(SubSectionLabel(LabelStr.stderr_output))
    contents.append(Static(f"{curated_stderr}", markup=False, classes=Tcss.cmd_output))
    return Collapsible(
        *contents,
        title=title,
        collapsed_symbol=Chars.right_triangle,
        expanded_symbol=Chars.down_triangle,
    )


def diff_statics(diff_str: str) -> list[Static]:
    diff_lines = diff_str.splitlines()

    def get_prefix(line: str) -> str:
        for p in _DIFF_TCSS_MAP:
            if line.startswith(p):
                return p
        return " "

    groups: list[tuple[str, str]] = []
    for prefix, group_lines in groupby(diff_lines, key=get_prefix):
        group_list = list(group_lines)
        if prefix in ("+", "-", " "):
            groups.append((prefix, "\n".join(group_list)))
        else:
            groups.extend((prefix, line) for line in group_list)

    return [
        Static(text, classes=_DIFF_TCSS_MAP[prefix].value, markup=False)
        for prefix, text in groups
    ]


def truth_widgets(truth_dict: dict[str, bool]) -> list[HorizontalGroup]:
    widgets: list[HorizontalGroup] = []
    for info_label, truth in truth_dict.items():
        label_text = "yes" if truth else "no"
        classes = Tcss.true_label if truth else Tcss.false_label
        widgets.append(
            HorizontalGroup(InfoLabel(info_label), Label(label_text, classes=classes))
        )
    return widgets

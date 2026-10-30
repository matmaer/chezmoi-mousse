from __future__ import annotations

from datetime import datetime
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
    title = f"[{color}][{ts}] {escape(cmd_result.pretty_cmd)}[/] {suffix}"
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


def diff_lines(diff_str: str) -> list[Static]:
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


def log_static(msg: str, color: ColorVar) -> Static:
    log_time = f"[{datetime.now().strftime('%H:%M:%S')}]"
    return Static(f"  [${color}]{log_time} {escape(msg)}[/]")


def doctor_log_lines(cr: CommandResult) -> list[Static]:
    lines: list[Static] = []
    first_col: list[str] = [
        line.split()[0] for line in cr.std_out.splitlines() if line.strip() != ""
    ]
    lines.append(log_static(f"{LogStr.doctor_section.start}", ColorVar.accent_darken_3))
    nothing_serious = True
    if "error" in first_col:
        lines.append(log_static(LogStr.doctor_errors_found, ColorVar.text_error))
        nothing_serious = False
    if "failed" in first_col:
        lines.append(log_static(LogStr.doctor_failed_found, ColorVar.text_error))
        nothing_serious = False
    if "warning" in first_col:
        lines.append(log_static(LogStr.doctor_warnings_found, ColorVar.text_warning))
    if "not set" in cr.std_out:
        lines.append(log_static(LogStr.doctor_not_set_found, ColorVar.text_warning))
    if nothing_serious:
        lines.append(log_static(LogStr.doctor_no_issue_found, ColorVar.text_success))
    else:
        lines.append(
            log_static(LogStr.doctor_minor_issues_found, ColorVar.text_warning)
        )
    lines.append(log_static(LogStr.doctor_section.end, ColorVar.accent_darken_3))
    return lines


def truth_widgets(truth_dict: dict[str, bool]) -> list[HorizontalGroup]:
    widgets: list[HorizontalGroup] = []
    for info_label, truth in truth_dict.items():
        label_text = "yes" if truth else "no"
        classes = Tcss.true_label if truth else Tcss.false_label
        widgets.append(
            HorizontalGroup(InfoLabel(info_label), Label(label_text, classes=classes))
        )
    return widgets

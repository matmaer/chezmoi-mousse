from __future__ import annotations

from itertools import groupby

from textual.containers import HorizontalGroup
from textual.widgets import Static

from chezmoi_mousse.gui.common.components import InfoLabel, TruthLabel
from chezmoi_mousse.str_enums import Tcss

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
        widgets.append(HorizontalGroup(InfoLabel(info_label), TruthLabel(truth)))
    return widgets

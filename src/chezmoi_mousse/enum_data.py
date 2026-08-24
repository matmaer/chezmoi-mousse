from __future__ import annotations

from enum import Enum

from chezmoi_mousse.named_tuples import SwitchData
from chezmoi_mousse.str_enums import (
    SwitchLabel,
)

__all__ = [
    "SwitchEnum",
]


class SwitchEnum(Enum):
    # Apply and Re-Add tab
    show_unchanged = SwitchData(
        label=SwitchLabel.show_unchanged,
        enabled_tooltip=(
            "Include unchanged paths, which are not found in the 'chezmoi status' "
            "output."
        ),
    )
    show_unmanaged = SwitchData(
        label=SwitchLabel.show_unmanaged,
        enabled_tooltip=("If enabled, also show unmanaged children."),
    )
    expand_all = SwitchData(
        label=SwitchLabel.expand_all, enabled_tooltip=("Expand all directories.")
    )

    # Add Tab

    show_managed = SwitchData(
        label=SwitchLabel.show_managed,
        enabled_tooltip=("If enabled, also show already managed paths."),
    )
    show_unwanted = SwitchData(
        label=SwitchLabel.show_unwanted,
        enabled_tooltip=(
            "Include files and directories considered as 'unwanted' for a dotfile "
            "manager. These include cache, temporary, trash (recycle bin) and other "
            "similar files or directories."
        ),
    )

    @property
    def label(self) -> str:
        return self.value.label

    @property
    def enabled_tooltip(self) -> str:
        return self.value.enabled_tooltip

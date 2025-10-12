from dataclasses import dataclass
from enum import Enum

from chezmoi_mousse._labels import SwitchLabel

__all__ = ["Switches", "SwitchData"]


@dataclass(frozen=True, slots=True)
class SwitchData:
    label: str
    switch_name: str
    tooltip: str
    disabled_tooltip: str = ""


class Switches(Enum):

    expand_all = SwitchData(
        label=SwitchLabel.expand_all.value,
        switch_name=SwitchLabel.expand_all.name,
        tooltip='Expand all managed directories. Showing unchanged depending on the "show unchanged files" switch.',
        disabled_tooltip="Switch to Tree to enable.",
    )
    unchanged = SwitchData(
        label=SwitchLabel.unchanged.value,
        switch_name=SwitchLabel.unchanged.name,
        tooltip="Include files unchanged files which are not found in the 'chezmoi status' output.",
    )
    unmanaged_dirs = SwitchData(
        label=SwitchLabel.unmanaged_dirs.value,
        switch_name=SwitchLabel.unmanaged_dirs.name,
        tooltip="The default (disabled), only shows directories which already contain managed files. This allows spotting new unmanaged files in already managed directories. Enable to show all directories which contain unmanaged files.",
    )
    unwanted = SwitchData(
        label=SwitchLabel.unwanted.value,
        switch_name=SwitchLabel.unwanted.name,
        tooltip="Include files and directories considered as 'unwanted' for a dotfile manager. These include cache, temporary, trash (recycle bin) and other similar files or directories. For example enable this to add files to your repository which are in a directory named '.cache'.",
    )

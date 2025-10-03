from dataclasses import dataclass
from enum import Enum

__all__ = ["Switches"]


class Switches(Enum):
    @dataclass(frozen=True)
    class SwitchData:
        label: str
        tooltip: str

    expand_all = SwitchData(
        "expand all dirs",
        "Expand all managed directories. Depending on the unchanged switch.",
    )
    unchanged = SwitchData(
        "show unchanged files",
        "Include files unchanged files which are not found in the 'chezmoi status' output.",
    )
    unmanaged_dirs = SwitchData(
        "show unmanaged dirs",
        "The default (disabled), only shows directories which already contain managed files. This allows spotting new unmanaged files in already managed directories. Enable to show all directories which contain unmanaged files.",
    )
    unwanted = SwitchData(
        "show unwanted paths",
        "Include files and directories considered as 'unwanted' for a dotfile manager. These include cache, temporary, trash (recycle bin) and other similar files or directories. For example enable this to add files to your repository which are in a directory named '.cache'.",
    )
